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
# Importamos la nueva arquitectura modular
from services.permissions_service import ensure_org_user, get_user_role, get_teams_and_projects_for_user
from services.risk_service import (
    get_employee_global_risk, get_employee_project_risk,
    get_team_global_risk, get_project_global_risk,
    get_project_risk_trend, get_project_members_list as get_project_members,
    get_member_projects_breakdown, get_team_risk_trend
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
#  GESTIÓN DE ENTIDADES (EQUIPOS Y PROYECTOS) — SEGURIDAD POR ROL
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
    """Lista las entidades (equipos y proyectos) visibles para el usuario autenticado."""
    email, role = _require_session(request)
    if not email:
        return JSONResponse({"error": "No autenticado"}, status_code=401)
    
    data = get_teams_and_projects_for_user(email, role)
    # Devolvemos un formato compatible o extendido
    return JSONResponse({
        "teams": data["teams"],
        "projects": data["projects"],
        "role": role
    })


def _check_project_access(email: str, role: str, project_id: int) -> bool:
    """Acceso a proyecto: admin/manager o owner del proyecto."""
    if role in ["admin", "manager"]: return True
    from db_client import get_supabase_client
    supabase = get_supabase_client()
    if not supabase: return False
    res = supabase.table("projects").select("id").eq("id", project_id).eq("owner_email", email).maybe_single().execute()
    return res.data is not None


def _check_team_access(email: str, role: str, team_id: int) -> bool:
    """Acceso a equipo: admin/manager o manager del equipo."""
    if role in ["admin", "manager"]: return True
    from db_supabase import get_supabase_client
    supabase = get_supabase_client()
    if not supabase: return False
    res = supabase.table("teams").select("id").eq("id", team_id).eq("manager_email", email).maybe_single().execute()
    return res.data is not None


@app.get("/api/project/risk")
async def project_risk(request: Request, project_id: int, days: int = 7):
    """Nivel 4: Riesgo Táctico del Proyecto."""
    email, role = _require_session(request)
    if not email: return JSONResponse({"error": "No autenticado"}, status_code=401)
    if not _check_project_access(email, role, project_id):
        return JSONResponse({"error": "Sin permisos para este proyecto"}, status_code=403)
    return JSONResponse(get_project_global_risk(project_id, days))


@app.get("/api/project/trend")
async def project_trend(request: Request, project_id: int, days: int = 30):
    """Tendencia del Proyecto."""
    email, role = _require_session(request)
    if not email: return JSONResponse({"error": "No autenticado"}, status_code=401)
    if not _check_project_access(email, role, project_id):
        return JSONResponse({"error": "Sin permisos para este proyecto"}, status_code=403)
    return JSONResponse(get_project_risk_trend(project_id, days))


@app.get("/api/team/risk")
async def team_risk(request: Request, team_id: int, days: int = 7):
    """Nivel 3: Riesgo Global del Equipo."""
    email, role = _require_session(request)
    if not email: return JSONResponse({"error": "No autenticado"}, status_code=401)
    if not _check_team_access(email, role, team_id):
        return JSONResponse({"error": "Sin permisos para este equipo"}, status_code=403)
    return JSONResponse(get_team_global_risk(team_id, days))


@app.get("/api/team/trend")
async def team_trend(request: Request, team_id: int, days: int = 30):
    """Tendencia Global del Equipo."""
    email, role = _require_session(request)
    if not email: return JSONResponse({"error": "No autenticado"}, status_code=401)
    if not _check_team_access(email, role, team_id):
        return JSONResponse({"error": "Sin permisos para este equipo"}, status_code=403)
    return JSONResponse(get_team_risk_trend(team_id, days))


@app.get("/api/team/member-breakdown")
async def team_member_breakdown(request: Request, user_email: str, days: int = 7):
    """Desglose de proyectos para un miembro de equipo."""
    email, role = _require_session(request)
    if not email: return JSONResponse({"error": "No autenticado"}, status_code=401)
    # Nota: Aquí se podría añadir check de si el que pide el dato es manager de ese equipo
    return JSONResponse(get_member_projects_breakdown(user_email, days))


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

@app.get("/api/teams")
async def get_teams_list(request: Request):
    """Devuelve la lista de equipos para selectores."""
    email, role = _require_session(request)
    if not email: return JSONResponse({"error": "No autenticado"}, status_code=401)
    data = get_teams_and_projects_for_user(email, role)
    return JSONResponse({"teams": data["teams"]})

# Nota: get_team_trend y otros han sido refactorizados o integrados en los nuevos endpoints

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
