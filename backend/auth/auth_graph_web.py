import os
import hashlib
import base64
import secrets
import requests
import urllib.parse

from dotenv import load_dotenv
from auth import html_to_text


# ==========================================
# 1. CONFIGURACIÓN
# ==========================================

load_dotenv()

TENANT_ID    = os.getenv("TENANT_ID")
CLIENT_ID    = os.getenv("CLIENT_ID")
REDIRECT_URI = os.getenv("REDIRECT_URI")

# En producción esta variable debe apuntar al dominio real del servidor
# En local: http://localhost:8000
# En producción: https://tu-dominio.com
APP_ORIGIN = os.getenv("APP_ORIGIN", "http://localhost:8000")

AUTH_URL   = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0"
GRAPH_BASE = "https://graph.microsoft.com/v1.0"

# Permisos que pedimos al usuario cuando hace login
# User.Read       → leer su perfil (nombre, email)
# Chat.Read       → leer sus chats
# ChatMessage.Read → leer los mensajes de sus chats
SCOPES = ["User.Read", "Chat.Read", "ChatMessage.Read"]

# Timeout para todas las peticiones a Graph (en segundos)
# 30s para evitar que una petición lenta bloquee el servidor
TIMEOUT = 30


# ==========================================
# 2. AUTENTICACIÓN OAuth con PKCE
# ==========================================

def _generate_pkce_pair():
    """
    Genera un par code_verifier / code_challenge para el flujo PKCE.

    PKCE es un mecanismo de seguridad para OAuth que evita que alguien
    intercepte el código de autorización y lo use por su cuenta.

    Funciona así:
    1. Generamos un código aleatorio secreto (code_verifier)
    2. Lo hasheamos con SHA256 (code_challenge)
    3. Enviamos el challenge a Microsoft al hacer login
    4. Cuando Microsoft devuelve el código, enviamos el verifier original
    5. Microsoft comprueba que el verifier hashea al challenge → todo correcto
    """
    code_verifier = secrets.token_urlsafe(96)[:128]
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge


def build_auth_url(session: dict) -> str:
    """
    Construye la URL de login de Microsoft con estado y desafío PKCE.

    El usuario será redirigido a esta URL para hacer login con su cuenta
    de Microsoft. Después de autenticarse, Microsoft redirige de vuelta
    a REDIRECT_URI con un código de autorización.
    """
    # El state es un valor aleatorio que enviamos y esperamos recibir de vuelta
    # Sirve para verificar que la respuesta viene realmente de Microsoft
    # y no de un atacante (protección CSRF)
    state = os.urandom(16).hex()
    session["oauth_state"] = state

    code_verifier, code_challenge = _generate_pkce_pair()
    session["code_verifier"] = code_verifier

    params = {
        "client_id":             CLIENT_ID,
        "response_type":         "code",
        "redirect_uri":          REDIRECT_URI,
        "scope":                 " ".join(SCOPES),
        "state":                 state,
        "code_challenge":        code_challenge,
        "code_challenge_method": "S256",
        "prompt":                "select_account",
    }

    return f"{AUTH_URL}/authorize?{urllib.parse.urlencode(params)}"


def exchange_code_for_token(code: str, code_verifier: str = None) -> dict:
    """
    Intercambia el código de autorización por un token de acceso.

    Microsoft nos da un código temporal después del login.
    Lo canjeamos aquí por el token real que usaremos para llamar a Graph.
    El code_verifier es la parte secreta del PKCE que demuestra que somos
    los mismos que iniciaron el flujo de login.
    """
    data = {
        "client_id":     CLIENT_ID,
        "scope":         " ".join(SCOPES),
        "code":          code,
        "redirect_uri":  REDIRECT_URI,
        "grant_type":    "authorization_code",
        "code_verifier": code_verifier,
    }

    # APP_ORIGIN viene de variable de entorno para funcionar tanto en local
    # como en producción sin cambiar el código
    headers = {"Origin": APP_ORIGIN}

    resp = requests.post(
        f"{AUTH_URL}/token",
        data=data,
        headers=headers,
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


# ==========================================
# 3. HELPERS
# ==========================================

# ==========================================
# 4. LLAMADAS A GRAPH API
# ==========================================

def get_me_profile(token: str) -> dict:
    """
    Obtiene el perfil del usuario autenticado: nombre y email.
    Se usa para mostrar quién ha hecho login en la interfaz.
    """
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{GRAPH_BASE}/me?$select=displayName,mail,userPrincipalName"

    resp = requests.get(url, headers=headers, timeout=TIMEOUT)

    if not resp.ok:
        print(f"⚠️ Error obteniendo perfil: {resp.status_code} {resp.text}")
        return {}

    return resp.json()


def list_my_chats(token: str) -> list:
    """
    Lista todos los chats en los que participa el usuario autenticado.
    Sigue la paginación automáticamente para devolver todos los chats,
    no solo la primera página que devuelve Graph.
    """
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{GRAPH_BASE}/me/chats?$expand=lastMessagePreview"

    all_chats = []

    while url:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)

        if not resp.ok:
            print(f"⚠️ Error obteniendo chats: {resp.status_code} {resp.text}")
            break

        data = resp.json()

        for c in data.get("value", []):
            all_chats.append({
                "id":    c["id"],
                "topic": c.get("topic") or "Chat sin título",
            })

        # Si Graph tiene más páginas, nos da la URL de la siguiente
        url = data.get("@odata.nextLink")

    return all_chats


def list_chat_messages(token: str, chat_id: str, top: int = 50) -> list:
    """
    Lista los mensajes de un chat concreto con paginación automática.
    Solo devuelve mensajes reales escritos por personas,
    ignorando los avisos del sistema de Teams (alguien entró al chat, etc.).
    """
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{GRAPH_BASE}/chats/{chat_id}/messages?$top={top}"

    msgs = []

    while url:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)

        if not resp.ok:
            print(f"⚠️ Error obteniendo mensajes del chat {chat_id}: {resp.status_code} {resp.text}")
            break

        data = resp.json()

        for m in data.get("value", []):
            # Ignoramos mensajes del sistema, solo procesamos los escritos por personas
            if m.get("messageType") != "message":
                continue

            sender = (
                m.get("from", {})
                 .get("user", {})
                 .get("displayName", "Desconocido")
            )

            text = html_to_text(m.get("body", {}).get("content", ""))

            # Solo guardamos mensajes que tengan texto real
            if not text.strip():
                continue

            msgs.append({
                "text":            text,
                "from":            sender,
                "createdDateTime": m.get("createdDateTime"),
            })

        # Seguimos a la siguiente página si la hay
        url = data.get("@odata.nextLink")

    return msgs