import os
import uuid
import requests
from bs4 import BeautifulSoup
from msal import ConfidentialClientApplication
from dotenv import load_dotenv
from typing import Optional, List, Dict

# ==========================================
# 1. CARGA DE CONFIGURACIÓN Y CREDENCIALES
# ==========================================
load_dotenv()
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
GRAPH_BASE = "https://graph.microsoft.com/v1.0"

# Permisos que solicitamos a Microsoft
SCOPES = [
    "User.Read",               # Leer perfil básico user
    "Team.ReadBasic.All",      # Leer lista de equipos
    "Channel.ReadBasic.All",   # Leer lista de canales
    "ChannelMessage.Read.All", # Leer mensajes de canal (A veces restringido)
    "Group.Read.All",          # Leer grupos
    "Group.ReadWrite.All",     
]

# Inicializamos la App de MSAL (el "Portero" de la autenticación)
msal_app = ConfidentialClientApplication(
    client_id=CLIENT_ID,
    authority=AUTHORITY,
    client_credential=CLIENT_SECRET,
)

# ==========================================
# 2. FUNCIONES DE AUTENTICACIÓN (LOGIN)
# ==========================================

def build_auth_url(session: dict) -> str:
    """
    Paso 1: Genera el link de 'Iniciar Sesión con Microsoft'.
    Guarda un estado aleatorio en la sesión para seguridad.
    """
    state = str(uuid.uuid4())
    session["state"] = state
    return msal_app.get_authorization_request_url(
        scopes=SCOPES,
        state=state,
        redirect_uri=REDIRECT_URI,
        prompt="select_account",
    )

def exchange_code_for_token(code: str) -> dict:
    """
    Paso 2: Canjea el código temporal que nos da Microsoft por el Token real.
    """
    result = msal_app.acquire_token_by_authorization_code(
        code=code,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    if "error" in result:
        raise RuntimeError(f"Error Login: {result.get('error_description')}")
    return result

# ==========================================
# 3. HERRAMIENTAS ÚTILES
# ==========================================

def graph_get(access_token: str, path: str, params: Optional[dict] = None) -> dict:
    """
    Hace una petición GET a la API de Microsoft Graph usando el token.
    Maneja errores básicos e imprime si algo sale mal.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{GRAPH_BASE}{path}", headers=headers, params=params)
    
    # Si la respuesta es mala (4xx o 5xx), intentamos ver por qué
    if not response.ok:
        print(f"⚠️ GRAPH ERROR ({path}): {response.status_code} - {response.text}")
        try:
            return {"error": response.json()}
        except:
            return {"error": response.text}
    
    return response.json()

def html_to_text(html: str) -> str:
    """
    Teams devuelve los mensajes en HTML sucio (<div>hola</div>).
    Esta función lo convierte a texto limpio ("hola").
    """
    if not html: return ""
    return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)

# ==========================================
# 4. FUNCIONES DE CHAT (PLAN C - EL QUE FUNCIONA)
# ==========================================

def list_my_chats(access_token: str) -> List[Dict]:
    """Lista los últimos 10 chats del usuario."""
    # $expand=members nos permitiría ver nombres de grupo, pero con $top=10 vale por ahora
    data = graph_get(access_token, "/me/chats", params={"$top": 10})
    return data.get("value", [])

def list_chat_messages(access_token: str, chat_id: str, top: int = 20) -> List[Dict]:
    """
    Descarga los mensajes de un chat específico y los limpia.
    """
    data = graph_get(access_token, f"/chats/{chat_id}/messages", params={"$top": top})
    
    if "error" in data:
        # Si falla, devolvemos lista vacía para no romper la app
        print(f"Error leyendo chat {chat_id}: {data}")
        return []
        
    raw_msgs = data.get("value", [])
    clean_msgs = []
    
    for m in raw_msgs:
        # 1. Limpiar HTML del mensaje
        raw_body = m.get("body", {}).get("content", "")
        clean_text = html_to_text(raw_body)
        
        # 2. Averiguar quién lo envió (puede ser null si es mensaje de sistema)
        sender_obj = m.get("from") or {} 
        user_obj = sender_obj.get("user") or sender_obj.get("application") or {}
        sender_name = user_obj.get("displayName", "Desconocido")
        
        clean_msgs.append({
            "id": m.get("id"),
            "text": clean_text,
            "from": sender_name,
            "createdDateTime": m.get("createdDateTime")
        })
        
    return clean_msgs

# ==========================================
# 5. FUNCIONES DE EQUIPOS (LEGACY / AVANZADO)
# ==========================================
# Estas funciones funcionan para listar, pero leer mensajes suele dar Error 410
# a menos que tengas licencia especial. Las mantenemos por compatibilidad.

def list_joined_teams(access_token: str) -> List[Dict]:
    """Lista equipos donde estoy."""
    data = graph_get(access_token, "/me/joinedTeams")
    return data.get("value", [])

def list_team_channels(access_token: str, team_id: str) -> List[Dict]:
    """Lista canales de un equipo."""
    data = graph_get(access_token, f"/teams/{team_id}/channels")
    return data.get("value", [])

def list_channel_messages(access_token: str, team_id: str, channel_id: str, top=20) -> List[Dict]:
    """Lee mensajes de canal. (Suele requerir permisos de Administrador/Pago)."""
    data = graph_get(access_token, f"/teams/{team_id}/channels/{channel_id}/messages", params={"$top": top})
    if "error" in data:
        raise RuntimeError(f"Error Canal: {data['error']}")
    
    # Lógica de limpieza simplificada (igual que chat, pero resumida aquí)
    raw_msgs = data.get("value", [])
    clean_msgs = []
    for m in raw_msgs:
         clean_msgs.append({
            "text": html_to_text(m.get("body", {}).get("content", "")),
            "from": "CanalUser", # Simplificado
            "createdDateTime": m.get("createdDateTime")
        })
    return clean_msgs
