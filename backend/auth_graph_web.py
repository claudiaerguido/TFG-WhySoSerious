import os
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

def build_auth_url(session):
    state = os.urandom(16).hex()
    session["oauth_state"] = state
    
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "response_mode": "query",
        "scope": " ".join(SCOPES),
        "state": state
    }
    return f"{AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"

def exchange_code_for_token(code):
    data = {
        "client_id": CLIENT_ID,
        "scope": " ".join(SCOPES),
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
        "client_secret": CLIENT_SECRET
    }
    resp = requests.post(TOKEN_URL, data=data)
    resp.raise_for_status()
    return resp.json()

def html_to_text(html):
    if not html: return ""
    return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)

def list_my_chats(token):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{GRAPH_BASE}/me/chats?$expand=lastMessagePreview", headers=headers)
    if not resp.ok: return []
    
    chats = []
    for c in resp.json().get("value", []):
        topic = c.get("topic")
        if not topic:
            # Try to get participant name for 1:1 chats
            topic = "Chat sin título" 
        
        chat_id = c["id"]
        chats.append({"id": chat_id, "topic": topic})
    return chats

def list_chat_messages(token, chat_id, top=20):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{GRAPH_BASE}/chats/{chat_id}/messages?$top={top}", headers=headers)
    if not resp.ok: return []
    
    msgs = []
    for m in resp.json().get("value", []):
        if m.get("messageType") != "message": continue
        
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
            "createdDateTime": m["createdDateTime"]
        })
    return msgs
