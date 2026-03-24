import os
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv


# ==========================================
# 1. CONFIGURACIÓN
# ==========================================

load_dotenv()

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
GRAPH_SCOPE = "https://graph.microsoft.com/.default"
TIMEOUT = 10

if TENANT_ID:
    AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
    TOKEN_URL = f"{AUTHORITY}/oauth2/v2.0/token"
else:
    AUTHORITY = ""
    TOKEN_URL = ""

# Caché simple para resolver IDs de usuario a email
USER_CACHE: Dict[str, str] = {}


# ==========================================
# 2. HELPERS INTERNOS
# ==========================================

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


def html_to_text(html: str) -> str:
    """Convierte HTML de Teams en texto plano."""
    if not html:
        return ""
    try:
        return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    except Exception:
        return html


# ==========================================
# 3. AUTENTICACIÓN DE APLICACIÓN
# ==========================================

def get_app_token() -> str:
    """
    Obtiene un token de aplicación mediante client credentials.
    No requiere login de usuario.
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


# ==========================================
# 4. WRAPPER GENÉRICO DE GRAPH
# ==========================================

def graph_get(
    path: str,
    token: Optional[str] = None,
    params: Optional[dict] = None
) -> dict:
    """
    Realiza una petición GET a Microsoft Graph.
    Si no se proporciona token, usa autenticación de aplicación.
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


# ==========================================
# 5. RESOLUCIÓN DE USUARIOS
# ==========================================

def get_user_email_from_id(user_id: str) -> Optional[str]:
    """
    Resuelve el email de un usuario desde caché o mediante Graph.
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


# ==========================================
# 6. USUARIOS → CHATS → MENSAJES
# ==========================================

def list_users(top: int = 999, token: Optional[str] = None) -> List[Dict]:
    """
    Lista usuarios del tenant usando paginación.
    El parámetro 'top' controla el tamaño de página inicial; si existen más
    resultados, se siguen automáticamente mediante @odata.nextLink.
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
        all_users.extend(data.get("value", []))
        url = data.get("@odata.nextLink")

    return all_users


def list_user_chats(user_id: str, top: int = 50, token: Optional[str] = None) -> List[Dict]:
    """
    Lista los chats en los que participa un usuario (con paginación).
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

    Nota:
    - No implementa paginación completa.
    - Requiere permiso: Chat.Read.All
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
        print(f"⚠️ Error obteniendo miembros de chat {chat_id}: {e}")
        return []


def list_chat_messages(chat_id: str, top: int = 50, token: Optional[str] = None) -> List[Dict]:
    """
    Lista mensajes de un chat siguiendo la paginación @odata.nextLink.
    Extrae texto limpio y email del remitente.
    """
    messages_out: List[Dict] = []
    # Usamos un 'top' alto por página para eficiencia, pero Graph paginará si hay más.
    url = f"{GRAPH_BASE}/chats/{chat_id}/messages?$top={top}&$orderby=createdDateTime desc"
    
    if token is None:
        token = get_app_token()
        
    headers = {"Authorization": f"Bearer {token}"}

    while url:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        if not resp.ok: 
            print(f"⚠️ Error Graph en {url}: {resp.status_code} {resp.text}")
            break
            
        data = resp.json()
        for message in data.get("value", []):
            # Solo procesamos mensajes de tipo 'message' (evitamos avisos de sistema)
            if message.get("messageType") != "message":
                continue

            body = message.get("body", {})
            text = html_to_text(body.get("content", ""))
            
            sender = message.get("from") or {}
            user_info = sender.get("user") or {}
            sender_email = user_info.get("userPrincipalName") or user_info.get("email")

            if not sender_email and user_info.get("id"):
                sender_email = get_user_email_from_id(user_info.get("id"))

            sender_name = user_info.get("displayName") or "Unknown"

            if text and len(text.strip()) > 0:
                messages_out.append({
                    "id": message.get("id"),
                    "text": text,
                    "from": sender_name,
                    "sender_email": sender_email.lower() if sender_email else None,
                    "createdDateTime": message.get("createdDateTime"),
                })
        
        # Paginación automática si Graph indica que hay más datos
        url = data.get("@odata.nextLink")

    return messages_out


# ==========================================
# 7. UTILIDAD MANUAL
# ==========================================

def collect_all_messages(limit_per_chat: int = 20, user_top: int = 50) -> List[Dict]:
    """
    Utilidad manual para recorrer parte de la organización y devolver mensajes
    listos para análisis.

    Nota:
    - Recorre los primeros `user_top` usuarios.
    - Recupera hasta `limit_per_chat` mensajes por chat.
    - Está pensada para pruebas, depuración o carga inicial pequeña.
    """
    results: List[Dict] = []
    token = get_app_token()

    users = list_users(top=user_top, token=token)

    for user in users:
        user_id = user.get("id")
        user_email = user.get("userPrincipalName") or user.get("mail")

        if not user_id:
            continue

        chats = list_user_chats(user_id, top=50, token=token)

        for chat in chats:
            chat_id = chat.get("id")
            if not chat_id:
                continue

            messages = list_chat_messages(chat_id, top=limit_per_chat, token=token)

            for msg in messages:
                results.append({
                    "user": user_email,
                    "chat_id": chat_id,
                    **msg,
                })

    return results