import os
from typing import List, Dict, Optional
 
import requests
from auth import html_to_text
from dotenv import load_dotenv
 
 
# --- Configuración ---

load_dotenv()
 
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
 
GRAPH_BASE = "https://graph.microsoft.com/v1.0"
GRAPH_SCOPE = "https://graph.microsoft.com/.default"
 
# Subido de 10 a 30 segundos para evitar fallos en organizaciones grandes
# donde Graph puede tardar más en responder
TIMEOUT = 30
 
if TENANT_ID:
    AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
    TOKEN_URL = f"{AUTHORITY}/oauth2/v2.0/token"
else:
    AUTHORITY = ""
    TOKEN_URL = ""
 
# Caché simple para resolver IDs de usuario a email
# Evita hacer una petición a Graph cada vez que necesitamos el email de alguien
USER_CACHE: Dict[str, str] = {}
 
 
# --- Helpers internos ---
 
def _validate_graph_config() -> None:
    """Valida que la configuración mínima de Graph esté disponible."""
    missing = []
    if not TENANT_ID:
        missing.append("TENANT_ID")
    if not CLIENT_ID:
        missing.append("CLIENT_ID")
    if not CLIENT_SECRET:
        missing.append("CLIENT_SECRET")
 
    if missing:
        raise RuntimeError(
            f"Faltan variables de entorno de Microsoft Graph: {', '.join(missing)}"
        )
 
 
 
 
# --- Autenticación de aplicación ---
 
def get_app_token() -> str:
    """
    Obtiene un token de aplicación mediante client credentials.
    No requiere login de usuario: el sistema se autentica solo con
    las credenciales de la aplicación registrada en Azure AD.
    """
    _validate_graph_config()
 
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": GRAPH_SCOPE,
    }
 
    response = requests.post(TOKEN_URL, data=data, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()["access_token"]
 
 
# --- Wrapper genérico de Graph ---
 
def graph_get(
    path: str,
    token: Optional[str] = None,
    params: Optional[dict] = None
) -> dict:
    """
    Realiza una petición GET a Microsoft Graph.
    Si no se proporciona token, obtiene uno automáticamente.
    """
    if token is None:
        token = get_app_token()
 
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
 
    response = requests.get(
        f"{GRAPH_BASE}{path}",
        headers=headers,
        params=params,
        timeout=TIMEOUT,
    )
 
    if not response.ok:
        raise RuntimeError(
            f"GRAPH ERROR {response.status_code} ({path}): {response.text}"
        )
 
    return response.json()
 
 
# --- Resolución de usuarios ---
 
def get_user_email_from_id(user_id: str) -> Optional[str]:
    """
    Resuelve el email de un usuario desde caché o mediante Graph.
    Primero mira en la caché local (USER_CACHE). Si no está,
    hace una petición a Graph y lo guarda para futuras consultas.
    """
    if user_id in USER_CACHE:
        return USER_CACHE[user_id]
 
    try:
        user_data = graph_get(f"/users/{user_id}")
        email = user_data.get("userPrincipalName") or user_data.get("mail")
        if email:
            USER_CACHE[user_id] = email.lower()
            return USER_CACHE[user_id]
    except Exception:
        return None
 
    return None
 
 
# --- Usuarios → Chats → Mensajes ---
 
def list_users(top: int = 999, token: Optional[str] = None) -> List[Dict]:
    """
    Lista todos los usuarios del tenant usando paginación automática.
    Graph devuelve los usuarios en páginas. Este código sigue
    el @odata.nextLink hasta que no hay más páginas.
    También calienta la caché de emails para evitar peticiones individuales después.
    """
    all_users = []
    url = f"{GRAPH_BASE}/users?$top={top}"
 
    if token is None:
        token = get_app_token()
 
    headers = {"Authorization": f"Bearer {token}"}
 
    while url:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        users_batch = data.get("value", [])
        all_users.extend(users_batch)
 
        # Calentamos la caché con todos los usuarios de esta página
        # Así no tenemos que hacer peticiones individuales después
        for u in users_batch:
            uid = u.get("id")
            email = u.get("userPrincipalName") or u.get("mail")
            if uid and email:
                USER_CACHE[uid] = email.lower()
 
        url = data.get("@odata.nextLink")
 
    return all_users
 
 
def list_user_chats(user_id: str, top: int = 50, token: Optional[str] = None) -> List[Dict]:
    """
    Lista todos los chats en los que participa un usuario (con paginación).
    """
    all_chats = []
    url = f"{GRAPH_BASE}/users/{user_id}/chats?$top={top}"
 
    if token is None:
        token = get_app_token()
 
    headers = {"Authorization": f"Bearer {token}"}
 
    while url:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        all_chats.extend(data.get("value", []))
        url = data.get("@odata.nextLink")
 
    return all_chats
 
 
def list_chat_members(chat_id: str) -> List[str]:
    """
    Lista los emails de los participantes de un chat.
    Nota: no implementa paginación completa (suficiente para chats normales).
    Requiere permiso: Chat.Read.All
    """
    try:
        data = graph_get(f"/chats/{chat_id}/members")
        members = data.get("value", [])
        emails: List[str] = []
 
        for member in members:
            email = member.get("email") or member.get("userPrincipalName")
            if email:
                emails.append(email.lower())
 
        return emails
 
    except Exception as e:
        print(f"Error obteniendo miembros de chat {chat_id}: {e}")
        return []
 
 
def list_chat_messages(chat_id: str, top: int = 50, since: Optional[str] = None, token: Optional[str] = None) -> List[Dict]:
    """
    Lista mensajes de un chat siguiendo la paginación @odata.nextLink.
    Extrae texto limpio y email del remitente.
    Solo devuelve mensajes reales (ignora avisos del sistema de Teams).
    `since`: ISO8601 timestamp — si se proporciona, solo devuelve mensajes posteriores.
    """
    messages_out: List[Dict] = []
    # Graph API no soporta $filter por createdDateTime en mensajes de chat.
    # Filtramos en Python después de recibir cada página.
    url = f"{GRAPH_BASE}/chats/{chat_id}/messages?$top={top}&$orderby=createdDateTime desc"

    if token is None:
        token = get_app_token()

    headers = {"Authorization": f"Bearer {token}"}

    while url:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        if not resp.ok:
            print(f"Error Graph en {url}: {resp.status_code} {resp.text}")
            break

        data = resp.json()
        stop_pagination = False
        for message in data.get("value", []):
            # Ignoramos mensajes del sistema (avisos de que alguien entró al chat, etc.)
            # Solo procesamos mensajes reales escritos por personas
            if message.get("messageType") != "message":
                continue
 
            body = message.get("body", {})
            text = html_to_text(body.get("content", ""))
 
            sender = message.get("from") or {}
            user_info = sender.get("user") or {}
            sender_email = user_info.get("userPrincipalName") or user_info.get("email")
 
            # Si Graph no devuelve el email directamente, intentamos resolverlo por ID
            if not sender_email and user_info.get("id"):
                sender_email = get_user_email_from_id(user_info.get("id"))
 
            sender_name = user_info.get("displayName") or "Unknown"
 
            if not sender_email:
                print(f"No se pudo resolver email para '{sender_name}' (ID: {user_info.get('id')})")
 
            created = message.get("createdDateTime", "")
            if since and created and created < since:
                # Los mensajes vienen ordenados desc: en cuanto uno es anterior
                # al umbral, todos los siguientes también lo serán.
                stop_pagination = True
                break

            if text and len(text.strip()) > 0:
                messages_out.append({
                    "id": message.get("id"),
                    "text": text,
                    "from": sender_name,
                    "sender_email": sender_email.lower() if sender_email else None,
                    "createdDateTime": created,
                })

        url = None if stop_pagination else data.get("@odata.nextLink")
 
    return messages_out
 
 
# --- Utilidad manual ---
 
def collect_all_messages(limit_per_chat: int = 20, user_top: int = 50) -> List[Dict]:
    """
    Recorre la organización y devuelve mensajes listos para análisis de riesgo psicosocial.
 
    CAMBIO RESPECTO A LA VERSIÓN ANTERIOR:
    - Se añade 'chats_procesados' para evitar mensajes duplicados.
 
    El problema anterior: si Ana y Pedro tienen un chat compartido, ese chat
    aparecía en los chats de Ana Y en los chats de Pedro. El código lo procesaba
    dos veces, guardando cada mensaje duplicado. Eso inflaba las métricas de
    burnout de cada persona.
 
    La solución: llevamos un registro de los IDs de chat ya procesados. Si un
    chat ya fue procesado cuando recorrimos a Ana, lo saltamos cuando llegamos
    a Pedro. Cada mensaje se procesa una sola vez y se asocia a quien lo escribió
    (sender_email), no al usuario por el que llegamos al chat.
 
    Notas:
    - Pensada para pruebas o carga inicial pequeña.
    - Para producción con muchos usuarios, usar delta queries de Graph API.
    """
    results: List[Dict] = []
    token = get_app_token()
 
    # Conjunto de IDs de chats ya procesados
    # Usamos un set porque buscar en un set es instantáneo aunque tenga miles de IDs
    chats_procesados: set = set()
 
    users = list_users(top=user_top, token=token)
 
    for user in users:
        user_id = user.get("id")
 
        if not user_id:
            continue
 
        chats = list_user_chats(user_id, top=50, token=token)
 
        for chat in chats:
            chat_id = chat.get("id")
            if not chat_id:
                continue
 
            # Evita procesar el mismo chat dos veces si aparece en los chats de varios usuarios
            if chat_id in chats_procesados:
                continue
 
            chats_procesados.add(chat_id)
 
            messages = list_chat_messages(chat_id, top=limit_per_chat, token=token)
 
            for msg in messages:
                results.append({
                    # IMPORTANTE: asociamos el mensaje a quien lo ESCRIBIÓ (sender_email),
                    # no al usuario por el que llegamos a este chat.
                    # Así los datos de burnout son individuales y correctos.
                    "user": msg.get("sender_email"),
                    "chat_id": chat_id,
                    **msg,
                })
 
    return results
