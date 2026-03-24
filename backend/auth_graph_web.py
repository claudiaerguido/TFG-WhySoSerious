import os, hashlib, base64, secrets, requests, urllib.parse
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Configuración básica de Microsoft Graph
load_dotenv()
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
REDIRECT_URI = os.getenv("REDIRECT_URI")

AUTH_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0"
GRAPH_BASE = "https://graph.microsoft.com/v1.0"
SCOPES = ["User.Read", "Chat.Read", "ChatMessage.Read"]

def _generate_pkce_pair():
    """Genera code_verifier y code_challenge (S256) para el flujo PKCE."""
    code_verifier = secrets.token_urlsafe(96)[:128]
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge

def build_auth_url(session):
    """Construye la URL de login con estado y desafío PKCE."""
    session["oauth_state"] = state = os.urandom(16).hex()
    code_verifier, code_challenge = _generate_pkce_pair()
    session["code_verifier"] = code_verifier

    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(SCOPES),
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "prompt": "select_account",
    }
    return f"{AUTH_URL}/authorize?{urllib.parse.urlencode(params)}"

def exchange_code_for_token(code, code_verifier=None):
    """Intercambia el código por un token de acceso usando el verifier PKCE."""
    data = {
        "client_id": CLIENT_ID,
        "scope": " ".join(SCOPES),
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
        "code_verifier": code_verifier
    }
    # Origin match para evitar cross-origin errors en entornos locales
    headers = {"Origin": "http://localhost:8000"}
    resp = requests.post(f"{AUTH_URL}/token", data=data, headers=headers)
    resp.raise_for_status()
    return resp.json()

def html_to_text(html):
    """Limpia el HTML de Teams a texto plano."""
    return BeautifulSoup(html, "html.parser").get_text(" ", strip=True) if html else ""

def get_me_profile(token):
    """Obtiene el perfil básico (Nombre, Email) del usuario autenticado."""
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{GRAPH_BASE}/me?$select=displayName,mail,userPrincipalName"
    resp = requests.get(url, headers=headers)
    return resp.json() if resp.ok else {}

def list_my_chats(token):
    """Lista los chats recientes en los que participa el usuario."""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{GRAPH_BASE}/me/chats?$expand=lastMessagePreview", headers=headers)
    if not resp.ok: return []
    
    return [
        {"id": c["id"], "topic": (c.get("topic") or "Chat")} 
        for c in resp.json().get("value", [])
    ]

def list_chat_messages(token, chat_id, top=50):
    """Lista mensajes del chat siguiendo la paginación @odata.nextLink."""
    headers, msgs, url = {"Authorization": f"Bearer {token}"}, [], f"{GRAPH_BASE}/chats/{chat_id}/messages?$top={top}"
    
    while url:
        resp = requests.get(url, headers=headers)
        if not resp.ok: break
        
        data = resp.json()
        for m in data.get("value", []):
            if m.get("messageType") == "message":
                sender = m.get("from", {}).get("user", {}).get("displayName", "Sistema")
                text = html_to_text(m.get("body", {}).get("content", ""))
                msgs.append({
                    "text": text,
                    "from": sender,
                    "createdDateTime": m["createdDateTime"],
                })
        url = data.get("@odata.nextLink")
        
    return msgs
