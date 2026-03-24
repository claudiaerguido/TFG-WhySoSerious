import os
from typing import Literal
from dotenv import load_dotenv

# FastAPI & Starlette
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel

# Background Tasks
from apscheduler.schedulers.background import BackgroundScheduler

# Local Modules - Core Logic
import nlp_model
from scheduler_tasks import run_nightly_analysis
from auth_graph_web import (
    build_auth_url, 
    exchange_code_for_token, 
    list_my_chats, 
    get_me_profile
)

# Local Modules - Services & DB
from services.permissions_service import ensure_org_user, get_user_role, get_teams_and_projects_for_user
from services.risk_service import (
    get_team_global_risk, get_project_tactical_risk,
    get_project_risk_trend, get_member_projects_breakdown, get_team_risk_trend,
    get_employee_full_profile, get_employee_risk_trend
)
from db_client import get_supabase_client

# ==========================================
# 1. CONFIGURACIÓN INICIAL & MIDDLEWARE
# ==========================================

# Cargamos variables de entorno desde .env si existe
load_dotenv()

app = FastAPI(title="WhySoSerious Backend API", version="1.1.0")

# --- SCHEDULER NOCTURNO ---
scheduler = BackgroundScheduler()
# Ejecutar cada noche a las 02:00 AM para analizar la organización
scheduler.add_job(run_nightly_analysis, trigger="cron", hour=2, minute=0)
scheduler.start()

# --- SEGURIDAD (CORS) ---
# Permitimos que el frontend (dev y prod local) acceda a la API con credenciales.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:5174", 
        "http://127.0.0.1:5173", 
        "http://127.0.0.1:5174"
    ], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SEGURIDAD (SESIÓN) ---
# Se utiliza una variable de entorno para la clave secreta de la sesión.
# Fallback a "secret-key-muy-segura" solo si no está definida en .env.
session_secret = os.getenv("SESSION_SECRET_KEY", "secret-key-muy-segura")
app.add_middleware(SessionMiddleware, secret_key=session_secret)


# --- MODELOS DE DATOS ---
class TextRequest(BaseModel):
    text: str
    model: Literal["baseline", "final"] = "baseline"

class MemberProjectRequest(BaseModel):
    user_email: str
    project_id: int


# ==========================================
# 2. HELPERS DE SEGURIDAD INTERNOS
# ==========================================

def _require_session(request: Request):
    """
    Helper centralizado para validar sesión.
    Devuelve (user_email, role) o (None, None) si no hay sesión activa.
    """
    token = request.session.get("access_token")
    if not token:
        return None, None
    
    email = request.session.get("user_email", "")
    # Se obtiene el rol directamente desde el servicio de permisos
    role  = get_user_role(email) if email else "employee"
    return email, role


def _check_project_access(email: str, role: str, project_id: int) -> bool:
    """Verifica si el usuario tiene permisos para acceder a un proyecto."""
    if role in ["admin", "manager"]: 
        return True
    
    supabase = get_supabase_client()
    if not supabase: 
        return False
        
    # El creador/owner del proyecto siempre tiene acceso
    res = supabase.table("projects") \
        .select("id") \
        .eq("id", project_id) \
        .eq("owner_email", email) \
        .maybe_single() \
        .execute()
    return res.data is not None


def _check_team_access(email: str, role: str, team_id: int) -> bool:
    """Verifica si el usuario tiene permisos para acceder a un equipo."""
    if role in ["admin", "manager"]: 
        return True
    
    supabase = get_supabase_client() # Corregido: ya no usa db_supabase antiguo
    if not supabase: 
        return False
        
    # El manager asignado al equipo siempre tiene acceso
    res = supabase.table("teams") \
        .select("id") \
        .eq("id", team_id) \
        .eq("manager_email", email) \
        .maybe_single() \
        .execute()
    return res.data is not None


def _can_manage_user(admin_email: str, admin_role: str, target_user_email: str) -> bool:
    """
    Valida si el solicitante puede gestionar al usuario objetivo:
    - Admin: Siempre puede gestionar a cualquiera.
    - Manager: Solo si el objetivo pertenece a un equipo gestionado directamente por él.
    """
    if admin_role == "admin": return True
    if admin_role != "manager": return False
    
    supabase = get_supabase_client()
    if not supabase: return False

    # 1. Obtener equipos gestionados por el manager
    managed_teams = supabase.table("teams").select("id").eq("manager_email", admin_email).execute()
    team_ids = [t["id"] for t in (managed_teams.data or [])]
    if not team_ids: return False

    # 2. Verificar si el objetivo está en alguno de esos equipos
    res = supabase.table("user_teams").select("id").in_("team_id", team_ids).eq("user_email", target_user_email).execute()
    return len(res.data or []) > 0


# ==========================================
# 3. RUTAS DE AUTENTICACIÓN (MICROSOFT)
# ==========================================

@app.get("/api/auth-url")
async def auth_url(request: Request):
    """Devuelve la URL de login de Microsoft Graph."""
    url = build_auth_url(request.session)
    return JSONResponse({"url": url})

@app.get("/login")
async def login(request: Request):
    """Atajo para redirección directa al login."""
    return RedirectResponse(build_auth_url(request.session))

@app.get("/auth/callback")
async def auth_callback(request: Request, code: str = None, state: str = None, error: str = None):
    """Callback tras autenticación exitosa en Microsoft."""
    if error:
        print(f"⚠️ OAuth error: {error}")
        return RedirectResponse(f"http://localhost:5173/login?error={error}")
    
    try:
        code_verifier = request.session.get("code_verifier")
        token_data = exchange_code_for_token(code, code_verifier)
        access_token = token_data.get("access_token")
        request.session["access_token"] = access_token

        # Persistencia en sesión y auto-registro
        try:
            profile = get_me_profile(access_token)
            email = profile.get("mail") or profile.get("userPrincipalName", "")
            display_name = profile.get("displayName", "")
            
            request.session["user_email"] = email
            request.session["display_name"] = display_name
            
            ensure_org_user(email, display_name)
            print(f"✅ Login exitoso: {email}")
        except Exception as ep:
            print(f"⚠️ Error obteniendo perfil: {ep}")

        return RedirectResponse("http://localhost:5173/")
    except Exception as e:
        print(f"❌ Error en callback: {e}")
        return RedirectResponse(f"http://localhost:5173/?auth_failed=1")

@app.get("/api/me")
async def me(request: Request):
    """Información básica de la sesión actual."""
    email, role = _require_session(request)
    if not email:
        return JSONResponse({"authenticated": False}, status_code=401)
    
    return JSONResponse({
        "authenticated": True,
        "user_email": email,
        "display_name": request.session.get("display_name", ""),
        "role": role,
    })

@app.get("/api/me/info")
async def me_info_full(request: Request):
    """Perfil completo del usuario desde Graph API."""
    token = request.session.get("access_token")
    if not token:
        return JSONResponse({"error": "No autenticado"}, status_code=401)
    
    try:
        profile = get_me_profile(token)
        if not profile:
            return JSONResponse({"error": "No se pudo recuperar el perfil"}, status_code=502)
        
        name = profile.get("displayName", "")
        # Lógica para iniciales (ej: "Juan Perez" -> "JP")
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
    """Limpia la sesión y redirige al frontend."""
    request.session.clear()
    return RedirectResponse("http://localhost:5173/login")


# ==========================================
# 4. GESTIÓN DE EQUIPOS & PROYECTOS
# ==========================================

@app.get("/api/my/workspaces")
async def my_workspaces(request: Request):
    """Lista equipos y proyectos filtrados por los permisos del usuario."""
    email, role = _require_session(request)
    if not email:
        return JSONResponse({"error": "No autenticado"}, status_code=401)
    
    data = get_teams_and_projects_for_user(email, role)
    return JSONResponse({
        "teams": data["teams"],
        "projects": data["projects"],
        "role": role
    })

@app.get("/api/teams")
async def get_teams_list(request: Request):
    """Lista simplificada de equipos para selectores frontend."""
    email, role = _require_session(request)
    if not email: 
        return JSONResponse({"error": "No autenticado"}, status_code=401)
    
    data = get_teams_and_projects_for_user(email, role)
    return JSONResponse({"teams": data["teams"]})

@app.get("/api/project/risk")
async def project_risk(request: Request, project_id: int, days: int = 7):
    """Calcula el riesgo acumulado de un proyecto específico."""
    email, role = _require_session(request)
    if not email: return JSONResponse({"error": "No autenticado"}, status_code=401)
    
    if not _check_project_access(email, role, project_id):
        return JSONResponse({"error": "Acceso restringido a este proyecto"}, status_code=403)
        
    return JSONResponse(get_project_tactical_risk(project_id, days))

@app.get("/api/project/trend")
async def project_trend(request: Request, project_id: int, days: int = 30):
    """Histórico de tendencia de riesgo para un proyecto."""
    email, role = _require_session(request)
    if not email: return JSONResponse({"error": "No autenticado"}, status_code=401)
    
    if not _check_project_access(email, role, project_id):
        return JSONResponse({"error": "Acceso restringido"}, status_code=403)
        
    return JSONResponse(get_project_risk_trend(project_id, days))

@app.get("/api/team/risk")
async def team_risk(request: Request, team_id: int, days: int = 7):
    """Riesgo global agregado de un equipo completo."""
    email, role = _require_session(request)
    if not email: return JSONResponse({"error": "No autenticado"}, status_code=401)
    
    if not _check_team_access(email, role, team_id):
        return JSONResponse({"error": "Acceso restringido a este equipo"}, status_code=403)
        
    return JSONResponse(get_team_global_risk(team_id, days))

@app.get("/api/team/trend")
async def team_trend(request: Request, team_id: int, days: int = 30):
    """Tendencia temporal de riesgo para un equipo."""
    email, role = _require_session(request)
    if not email: return JSONResponse({"error": "No autenticado"}, status_code=401)
    
    if not _check_team_access(email, role, team_id):
        return JSONResponse({"error": "Acceso restringido"}, status_code=403)
        
    return JSONResponse(get_team_risk_trend(team_id, days))

@app.get("/api/team/member-breakdown")
async def team_member_breakdown(request: Request, user_email: str, days: int = 7):
    """
    Desglose de riesgo por proyectos de un usuario.
    Solo accesible por Admins/Managers o por el propio usuario.
    """
    email, role = _require_session(request)
    if not email: return JSONResponse({"error": "No autenticado"}, status_code=401)
    
    # Validación de seguridad mejorada
    if role not in ["admin", "manager"] and email != user_email:
        return JSONResponse({"error": "No tienes permiso para ver el desglose de este miembro"}, status_code=403)
        
    return JSONResponse(get_member_projects_breakdown(user_email, days))


@app.get("/api/employee/profile")
async def employee_profile(request: Request, user_email: str, days: int = 7):
    """Perfil detallado de riesgo de un empleado."""
    email, role = _require_session(request)
    if not email: return JSONResponse({"error": "No autenticado"}, status_code=401)
    
    # Solo Admins/Managers o el propio usuario pueden ver su perfil
    if role not in ["admin", "manager"] and email != user_email:
        return JSONResponse({"error": "No tienes permiso para ver este perfil"}, status_code=403)
        
    return JSONResponse(get_employee_full_profile(user_email, days))

@app.get("/api/employee/trend")
async def employee_trend(request: Request, user_email: str, days: int = 30):
    """Tendencia temporal de riesgo de un empleado."""
    email, role = _require_session(request)
    if not email: return JSONResponse({"error": "No autenticado"}, status_code=401)
    
    if role not in ["admin", "manager"] and email != user_email:
        return JSONResponse({"error": "No tienes permiso para ver esta tendencia"}, status_code=403)
        
    return JSONResponse(get_employee_risk_trend(user_email, days))


# ==========================================
# 5. ADMINISTRACIÓN & CONFIGURACIÓN TFG
# ==========================================

@app.post("/admin/trigger-analysis")
async def trigger_analysis(request: Request):
    """Fuerza la ejecución inmediata del pipeline de análisis."""
    email, role = _require_session(request)
    if not email: return JSONResponse({"error": "No autenticado"}, status_code=401)
    
    # Solo roles de gestión pueden disparar el análisis manual
    if role not in ["admin", "manager"]:
        return JSONResponse({"error": "Acceso denegado: Se requiere rol Admin o Manager"}, status_code=403)
    
    try:
        # Lógica centralizada en el scheduler para consistencia
        run_nightly_analysis()
        return {"status": "success", "message": "Proceso de análisis activado manualmente."}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ==========================================
# 6. GESTIÓN DE PROYECTOS (US-20)
# ==========================================

@app.get("/api/projects/catalog")
async def projects_catalog(request: Request):
    """Catálogo completo de proyectos para selectores UI."""
    email, role = _require_session(request)
    if not email: return JSONResponse({"error": "No autenticado"}, status_code=401)
    
    # Solo managers y admins ven el catálogo para gestión
    if role not in ["admin", "manager"]:
        return JSONResponse({"error": "Acceso denegado"}, status_code=403)
        
    from db_repository import fetch_all_projects_catalog
    return JSONResponse(fetch_all_projects_catalog(get_supabase_client()))

@app.post("/api/project/members")
async def add_project_member(request: Request, body: MemberProjectRequest):
    """Asocia un usuario a un proyecto."""
    email, role = _require_session(request)
    if not email: return JSONResponse({"error": "No autenticado"}, status_code=401)
    
    if not _can_manage_user(email, role, body.user_email):
        return JSONResponse({"error": "No tienes permiso para gestionar a este usuario"}, status_code=403)
        
    from db_repository import add_user_to_project
    success = add_user_to_project(get_supabase_client(), body.user_email, body.project_id)
    return {"status": "success" if success else "error"}

@app.delete("/api/project/members")
async def remove_project_member(request: Request, user_email: str, project_id: int):
    """Desasocia un usuario de un proyecto."""
    email, role = _require_session(request)
    if not email: return JSONResponse({"error": "No autenticado"}, status_code=401)
    
    if not _can_manage_user(email, role, user_email):
        return JSONResponse({"error": "No tienes permiso para gestionar a este usuario"}, status_code=403)
        
    from db_repository import remove_user_from_project
    success = remove_user_from_project(get_supabase_client(), user_email, project_id)
    return {"status": "success" if success else "error"}


# ==========================================
# 7. IA & PRUEBAS MANUALES (DEBUG)
# ==========================================

@app.get("/health")
def health_check():
    """Estado de carga del modelo y salud del servidor."""
    return {
        "status": "ok", 
        "model": "loaded" if nlp_model._model else "loading"
    }

@app.post("/predict")
async def predict(request: TextRequest):
    """Endpoint manual para validación rápida del motor de NLP."""
    if request.model == "baseline":
        res = nlp_model.baseline_predict(request.text)
        return {
            "model": "baseline", 
            "sentiment_label": res["label"], 
            "confidence": res["score"],
            "stars": res.get("stars", 0)
        }

    # Fallback automático si el modelo final no está cargado
    if nlp_model._model is None:
        res = nlp_model.baseline_predict(request.text)
        return {
            "labels": {res["label"]: res["score"]}, 
            "is_fallback": True, 
            "model": "final"
        }
    
    # Predicción real con el modelo entrenado
    out = nlp_model.final_predict(request.text)
    out["model"] = "final"
    return out

@app.get("/me/chats")
async def my_chats(request: Request):
    """Debug: Lista chats directos desde Graph."""
    email, role = _require_session(request)
    token = request.session.get("access_token")
    if not token:
        return JSONResponse({"error": "No autenticado"}, status_code=401)
    
    chats = list_my_chats(token)
    return {"chats": chats}
