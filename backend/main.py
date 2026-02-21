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
from db_supabase import get_team_risk_metrics

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

# ==========================================
# 2. RUTAS DE ADMINISTRACIÓN (TFG)
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
