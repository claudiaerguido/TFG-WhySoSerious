import os
import hashlib
import base64
import secrets
import requests
import urllib.parse
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
AUTHORIZE_URL = f"{AUTHORITY}/oauth2/v2.0/authorize"
TOKEN_URL = f"{AUTHORITY}/oauth2/v2.0/token"

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
SCOPES = ["User.Read", "Chat.Read", "ChatMessage.Read"]


def _generate_pkce_pair():
    """Genera code_verifier y code_challenge (S256) para el flujo PKCE."""
    code_verifier = secrets.token_urlsafe(96)[:128]
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge


def build_auth_url(session):
    state = os.urandom(16).hex()
    session["oauth_state"] = state

    code_verifier, code_challenge = _generate_pkce_pair()
    session["code_verifier"] = code_verifier

    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "response_mode": "query",
        "scope": " ".join(SCOPES),
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "prompt": "select_account",
    }
    return f"{AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"


def exchange_code_for_token(code, code_verifier=None):
    data = {
        "client_id": CLIENT_ID,
        "scope": " ".join(SCOPES),
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    if code_verifier:
        data["code_verifier"] = code_verifier
        
    headers = {"Origin": "http://localhost:8000"}  # Origin match para evitar cross-origin errors

    resp = requests.post(TOKEN_URL, data=data, headers=headers)
    if not resp.ok:
        print(f"❌ Token error [{resp.status_code}]: {resp.text}")
        resp.raise_for_status()
    return resp.json()


def html_to_text(html):
    if not html:
        return ""
    return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)


def get_me_profile(token):
    """Obtiene el perfil del usuario desde Microsoft Graph."""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(
        f"{GRAPH_BASE}/me?$select=displayName,mail,userPrincipalName,jobTitle,department,officeLocation",
        headers=headers,
    )
    if not resp.ok:
        return {}
    return resp.json()


def list_my_chats(token):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{GRAPH_BASE}/me/chats?$expand=lastMessagePreview", headers=headers)
    if not resp.ok:
        return []

    chats = []
    for c in resp.json().get("value", []):
        topic = c.get("topic") or "Chat sin título"
        chats.append({"id": c["id"], "topic": topic})
    return chats


def list_chat_messages(token, chat_id, top=20):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{GRAPH_BASE}/chats/{chat_id}/messages?$top={top}", headers=headers)
    if not resp.ok:
        return []

    msgs = []
    for m in resp.json().get("value", []):
        if m.get("messageType") != "message":
            continue
        body_content = m.get("body", {}).get("content", "")
        text = html_to_text(body_content)
        sender = m.get("from")
        if sender:
            user_info = sender.get("user") or {}
            sender_name = user_info.get("displayName", "Desconocido")
        else:
            sender_name = "Sistema"
        msgs.append({
            "text": text,
            "from": sender_name,
            "createdDateTime": m["createdDateTime"],
        })
    return msgs
