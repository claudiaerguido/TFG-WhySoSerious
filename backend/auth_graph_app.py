import os
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# ==========================================
# 1. CARGA DE CONFIGURACIÓN
# ==========================================

load_dotenv()

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
TOKEN_URL = f"{AUTHORITY}/oauth2/v2.0/token"

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
GRAPH_SCOPE = "https://graph.microsoft.com/.default"

# ==========================================
# 2. AUTENTICACIÓN DE APLICACIÓN (SIN LOGIN)
# ==========================================

def get_app_token() -> str:
    """
    Obtiene un token de aplicación usando client credentials.
    NO hay login de usuario.
    """
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": GRAPH_SCOPE,
    }

    response = requests.post(TOKEN_URL, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

# ==========================================
# 3. FUNCIÓN GENÉRICA PARA GRAPH
# ==========================================

def graph_get(
    path: str,
    token: Optional[str] = None,
    params: Optional[dict] = None
) -> dict:
    """
    Realiza una petición GET a Microsoft Graph.
    """
    if token is None:
        token = get_app_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.get(f"{GRAPH_BASE}{path}", headers=headers, params=params)

    if not response.ok:
        raise RuntimeError(
            f"GRAPH ERROR {response.status_code} ({path}): {response.text}"
        )

    return response.json()

# ==========================================
# 4. UTILIDADES
# ==========================================

def html_to_text(html: str) -> str:
    """
    Convierte HTML de Teams en texto limpio.
    """
    if not html:
        return ""
    return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)

# ==========================================
# 5. BUCLE MÁGICO: USUARIOS → CHATS → MENSAJES
# ==========================================

def list_users() -> List[Dict]:
    """
    Lista todos los usuarios del tenant.
    Requiere permiso: User.Read.All
    """
    data = graph_get("/users", params={"$top": 50})
    return data.get("value", [])

def list_user_chats(user_id: str) -> List[Dict]:
    """
    Lista los chats en los que participa un usuario.
    Requiere permiso: Chat.Read.All
    """
    data = graph_get(f"/users/{user_id}/chats")
    return data.get("value", [])

def list_chat_messages(chat_id: str, top: int = 20) -> List[Dict]:
    """
    Lista mensajes de un chat concreto.
    Requiere permiso: ChatMessage.Read.All
    """
    data = graph_get(
        f"/chats/{chat_id}/messages",
        params={"$top": top}
    )

    messages = []
    for m in data.get("value", []):
        body_html = m.get("body", {}).get("content", "")
        text = html_to_text(body_html)

        sender = m.get("from")
        if sender:
            user_info = sender.get("user") or {}
            app_info = sender.get("application") or {}
            sender_name = user_info.get("displayName") or app_info.get("displayName") or "Desconocido"
        else:
            sender_name = "Sistema / Evento"

        messages.append({
            "id": m.get("id"),
            "text": text,
            "from": sender_name,
            "raw_from": sender, # Added this for filtering in scheduler_tasks.py
            "createdDateTime": m.get("createdDateTime"),
        })

    return messages

# ==========================================
# 6. FUNCIÓN DE ALTO NIVEL (OPCIONAL)
# ==========================================

def collect_all_messages(limit_per_chat: int = 20) -> List[Dict]:
    """
    Recorre toda la organización y devuelve mensajes
    listos para analizar con IA.
    """
    results = []

    users = list_users()
    for user in users:
        user_id = user["id"]
        user_email = user.get("userPrincipalName")

        chats = list_user_chats(user_id)
        for chat in chats:
            chat_id = chat["id"]

            messages = list_chat_messages(chat_id, top=limit_per_chat)
            for msg in messages:
                results.append({
                    "user": user_email,
                    "chat_id": chat_id,
                    **msg
                })

    return results
