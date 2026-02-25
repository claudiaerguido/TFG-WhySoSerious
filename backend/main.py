from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from typing import Literal, Optional

# Importamos nuestro cerebro (NLP)
import nlp_model

# Importamos la lógica del scheduler de fondo
from scheduler_tasks import run_nightly_analysis
from auth_graph_app import list_users, list_user_chats, list_chat_messages
from db_supabase import (
    get_team_risk_metrics, get_teams_list, get_team_risk_trend,
    ensure_org_user, get_user_role, get_workspaces_for_user,
    get_workspace_risk_metrics, get_workspace_risk_trend, get_workspace_members,
)

# ==========================================
# 1. CONFIGURACIÓN INICIAL DE LA APP
# ==========================================
app = FastAPI()

# --- SCHEDULER NOCTURNO ---
from apscheduler.schedulers.background import BackgroundScheduler
from scheduler_tasks import run_nightly_analysis

scheduler = BackgroundScheduler()
# Ejecutar cada noche a las 02:00 AM
scheduler.add_job(run_nightly_analysis, trigger="cron", hour=2, minute=0)
scheduler.start()
# ---------------------------

# Configuración de Seguridad (CORS)
# Permitimos que la web (puerto 5173) hable con el servidor (puerto 8000)
# y se pasen "cookies" (credenciales) entre ellos.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de Sesión
# Esto crea una "Memoria" (Cookie) segura para guardar el Token del usuario.
app.add_middleware(SessionMiddleware, secret_key="secret-key-muy-segura")

class TextRequest(BaseModel):
    text: str
    model: Literal["baseline", "final"] = "baseline"

from auth_graph_web import build_auth_url, exchange_code_for_token, list_my_chats

# ==========================================
# 2. RUTAS DE AUTENTICACIÓN MICROSOFT
# ==========================================

@app.get("/api/auth-url")
async def auth_url(request: Request):
    """Devuelve la URL de OAuth. Llamado por el frontend para persistir cookies antes de navegar."""
    auth_url = build_auth_url(request.session)
    return JSONResponse({"url": auth_url})

@app.get("/login")
async def login(request: Request):
    """(Opcional) Atajo directo que podría fallar en algunos navegadores restrictivos."""
    auth_url = build_auth_url(request.session)
    return RedirectResponse(auth_url)

@app.get("/auth/callback")
async def auth_callback(request: Request, code: str = None, state: str = None, error: str = None):
    """Microsoft redirige aquí tras el login."""
    if error:
        print(f"⚠️ OAuth error from Azure: {error}")
        return RedirectResponse(f"http://localhost:5173/login?error={error}")
    try:
        code_verifier = request.session.get("code_verifier")
        print(f"📋 SESSION DICT: {request.session}\n📋 code_verifier in session: {'YES' if code_verifier else 'NO'}")
        token_data = exchange_code_for_token(code, code_verifier)
        access_token = token_data.get("access_token")
        request.session["access_token"] = access_token

        # Persistir identidad del usuario en sesión
        try:
            from auth_graph_web import get_me_profile
            profile = get_me_profile(access_token)
            email = profile.get("mail") or profile.get("userPrincipalName", "")
            display_name = profile.get("displayName", "")
            request.session["user_email"] = email
            request.session["display_name"] = display_name
            # Auto-registro si no existe en org_users
            ensure_org_user(email, display_name)
            print(f"✅ Sesión iniciada: {email} ({display_name})")
        except Exception as ep:
            print(f"⚠️ No se pudo obtener perfil Graph: {ep}")

        print("✅ Token exchange OK, redirigiendo al dashboard")
        return RedirectResponse("http://localhost:5173/")
    except Exception as e:
        print(f"❌ Token exchange exception: {e}")
        return RedirectResponse(f"http://localhost:5173/?auth_failed=1")

@app.get("/api/me")
async def me(request: Request):
    """Comprueba si el usuario tiene sesión activa, devuelve email y rol."""
    token = request.session.get("access_token")
    if not token:
        return JSONResponse({"authenticated": False}, status_code=401)
    user_email = request.session.get("user_email", "")
    role = get_user_role(user_email) if user_email else "employee"
    return JSONResponse({
        "authenticated": True,
        "user_email": user_email,
        "display_name": request.session.get("display_name", ""),
        "role": role,
    })


# ═══════════════════════════════════════════════════════════════
#  WORKSPACE ENDPOINTS — scope por rol
# ═══════════════════════════════════════════════════════════════

def _require_session(request: Request):
    """Helper: devuelve (user_email, role) o None si no hay sesión."""
    token = request.session.get("access_token")
    if not token:
        return None, None
    email = request.session.get("user_email", "")
    role  = get_user_role(email) if email else "employee"
    return email, role


@app.get("/api/my/workspaces")
async def my_workspaces(request: Request):
    """Lista los workspaces visibles para el usuario de sesión (scope por rol)."""
    email, role = _require_session(request)
    if not email:
        return JSONResponse({"error": "No autenticado"}, status_code=401)
    workspaces = get_workspaces_for_user(email, role)
    return JSONResponse({"workspaces": workspaces, "role": role})


def _check_workspace_access(email: str, role: str, workspace_id: int) -> bool:
    """
    Política de acceso a workspace concreto:
    - admin / manager → acceso total (pueden ver cualquier workspace)
    - employee        → SOLO si son el owner_email del workspace
                        (Ana→PRJ-Alpha, Carlos→PRJ-Beta, Irene→QA)
    """
    if role in ["admin", "manager"]:
        return True  # Javier (manager) siempre tiene acceso total
    from db_supabase import get_supabase_client
    supabase = get_supabase_client()
    if not supabase:
        return False
    try:
        # employee: solo acceso si es el jefe (owner) del workspace
        res = (
            supabase.table("workspaces")
            .select("id")
            .eq("id", workspace_id)
            .eq("owner_email", email)
            .maybe_single()
            .execute()
        )
        return res.data is not None
    except Exception:
        return False


@app.get("/api/workspace/risk")
async def workspace_risk(request: Request, workspace_id: int, days: int = 7):
    """Riesgo del workspace. Protegido por rol."""
    email, role = _require_session(request)
    if not email:
        return JSONResponse({"error": "No autenticado"}, status_code=401)
    if not _check_workspace_access(email, role, workspace_id):
        return JSONResponse({"error": "Sin permisos para este workspace"}, status_code=403)
    result = get_workspace_risk_metrics(workspace_id, days)
    print(f"[BACKEND] /api/workspace/risk workspace_id={workspace_id} days={days} → {result.get('risk_level')}")
    return JSONResponse(result)


@app.get("/api/workspace/trend")
async def workspace_trend(request: Request, workspace_id: int, days: int = 30):
    """Tendencia del workspace. Protegido por rol."""
    email, role = _require_session(request)
    if not email:
        return JSONResponse({"error": "No autenticado"}, status_code=401)
    if not _check_workspace_access(email, role, workspace_id):
        return JSONResponse({"error": "Sin permisos para este workspace"}, status_code=403)
    result = get_workspace_risk_trend(workspace_id, days)
    return JSONResponse(result)


@app.get("/api/workspace/members")
async def workspace_members(request: Request, workspace_id: int):
    """Miembros del workspace (enmascarados). Protegido por rol."""
    email, role = _require_session(request)
    if not email:
        return JSONResponse({"error": "No autenticado"}, status_code=401)
    if not _check_workspace_access(email, role, workspace_id):
        return JSONResponse({"error": "Sin permisos para este workspace"}, status_code=403)
    members = get_workspace_members(workspace_id)
    return JSONResponse({"members": members, "workspace_id": workspace_id})


@app.get("/api/me/info")
async def me_info(request: Request):
    """Devuelve el perfil completo del usuario autenticado desde Microsoft Graph."""
    from auth_graph_web import get_me_profile
    token = request.session.get("access_token")
    if not token:
        return JSONResponse({"error": "No autenticado"}, status_code=401)
    try:
        profile = get_me_profile(token)
        if not profile:
            return JSONResponse({"error": "No se pudo obtener el perfil"}, status_code=502)
        name = profile.get("displayName", "")
        initials = "".join([p[0].upper() for p in name.split() if p])[:2] if name else "?"
        return JSONResponse({
            "displayName": name,
            "mail": profile.get("mail") or profile.get("userPrincipalName", ""),
            "jobTitle": profile.get("jobTitle", ""),
            "department": profile.get("department", ""),
            "officeLocation": profile.get("officeLocation", ""),
            "initials": initials,
        })
    except Exception as e:
        print(f"❌ Error en /api/me/info: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/logout")
async def logout(request: Request):
    """Cierra la sesión y redirige al login del frontend."""
    request.session.clear()
    return RedirectResponse("http://localhost:5173/login")

@app.get("/me/chats")
async def my_chats(request: Request):
    """Devuelve los chats del usuario autenticado."""
    token = request.session.get("access_token")
    if not token:
        return RedirectResponse("http://localhost:8000/login")
    chats = list_my_chats(token)
    return {"chats": chats}

# ==========================================
# 3. RUTAS DE ADMINISTRACIÓN (TFG)
# ==========================================

@app.post("/admin/trigger-analysis")
def trigger_analysis():
    """
    Endpoints para la demo del TFG: 
    Fuerza la ejecución del análisis de toda la organización (como lo haría el scheduler).
    Devuelve un resumen de los resultados analizados.
    """
    try:
        # Llamamos a la lógica que ya tenías montada en el scheduler
        # que lee todo usando Permisos de Aplicación y lo guarda en base de datos.
        run_nightly_analysis()
        return {"status": "success", "message": "Análisis completado y guardado en Supabase."}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/team/risk")
def get_team_risk(team_id: int, days: int = 7):
    """
    US11 MVP: Devuelve el indicador global de riesgo de la organización llamando a la BD.
    Ejemplo de uso: /api/team/risk?team_id=1&days=30
    """
    print(f"\n[BACKEND FASTAPI] 📥 Recibida petición GET /api/team/risk - Params: team_id={team_id}, days={days}")
    result = get_team_risk_metrics(team_id, days)
    print(f"[BACKEND FASTAPI] 📤 Devolviendo a React: {result}\n")
    return result

@app.get("/api/teams")
def get_teams():
    """Devuelve la lista de equipos disponibles para el selector del frontend."""
    from db_supabase import get_supabase_client
    supabase = get_supabase_client()
    if not supabase:
        return JSONResponse({"error": "Sin conexión a Supabase"}, status_code=500)
    try:
        res = supabase.table("teams").select("id, name, manager_email").execute()
        return {"teams": res.data or []}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/team/risk/trend")
def get_team_trend(team_id: int, days: int = 30, bucket: str = "daily"):
    """Devuelve la serie temporal de riesgo medio del equipo por día."""
    result = get_team_risk_trend(team_id, days)
    return result

# ==========================================
# 4. RUTAS DE IA PURA (PRUEBAS MANUALES)
# ==========================================

@app.get("/health")
def health_check():
    return {"status": "ok", "model": "loaded" if nlp_model._model else "loading"}

@app.post("/predict")
async def predict(request: TextRequest):
    """Endpoint manual (el que usas en la tarjeta de abajo)."""
    if request.model == "baseline":
        res = nlp_model.baseline_predict(request.text)
        return {
            "model": "baseline", 
            "sentiment_label": res["label"], 
            "confidence": res["score"],
            "stars": res.get("stars", 0)
        }

    # Fallback si el modelo no cargó bien
    if nlp_model._model is None:
        res = nlp_model.baseline_predict(request.text)
        return {"labels": {res["label"]: res["score"]}, "is_fallback": True, "model": "final"}
    
    # Predicción Final
    out = nlp_model.final_predict(request.text)
    out["model"] = "final"
    return out
