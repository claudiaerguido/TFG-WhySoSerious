from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from typing import Literal

# Importamos nuestro cerebro (NLP) y nuestro traductor de Teams (auth_graph_web)
import nlp_model
from auth_graph_web import (
    build_auth_url, 
    exchange_code_for_token, 
    list_my_chats, 
    list_chat_messages
)

# ==========================================
# 1. CONFIGURACIÓN INICIAL DE LA APP
# ==========================================
app = FastAPI()

# Configuración de Seguridad (CORS)
# Permitimos que la web (puerto 5173) hable con el servidor (puerto 8000)
# y se pasen "cookies" (credenciales) entre ellos.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"], 
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
# 2. RUTAS DE AUTENTICACIÓN (LOGIN)
# ==========================================

@app.get("/login")
def login(request: Request):
    """Paso 1: Manda al usuario a la web de Microsoft para loguearse."""
    url = build_auth_url(request.session)
    return RedirectResponse(url)

@app.get("/auth/callback")
def auth_callback(request: Request, code: str = ""):
    """Paso 2: Microsoft nos devuelve al usuario con un 'código'."""
    try:
        # Canjeamos coste por Token Real
        token_data = exchange_code_for_token(code)
        
        # Guardamos el Token en la "caja fuerte" (la cookie de sesión)
        request.session["access_token"] = token_data["access_token"]
        
        # Le enviamos de vuelta al Frontend
        return RedirectResponse("http://localhost:5173") # Ojo: Redirige directo a tu web React
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/logout")
def logout(request: Request):
    """Limpia la sesión y desconecta."""
    request.session.clear()
    return RedirectResponse("http://localhost:5173")

# ==========================================
# 3. RUTAS DE TEAMS (EL CEREBRO LEE)
# ==========================================

@app.get("/me/chats")
def get_my_chats(request: Request):
    """Devuelve la lista de chats recientes del usuario."""
    token = request.session.get("access_token")
    if not token:
        # Si no hay token, avisamos al frontend que necesita login
        return JSONResponse({"error": "No autenticado"}, status_code=401)
    
    chats = list_my_chats(token)
    return {"chats": chats}

@app.get("/chats/{chat_id}/analyze")
def analyze_chat(request: Request, chat_id: str):
    """
    LA JOYA DE LA CORONA:
    1. Lee mensajes del chat.
    2. Los pasa por la IA.
    3. Cuenta riesgos (Estrés, Sobrecarga, Fatiga).
    """
    token = request.session.get("access_token")
    if not token: return JSONResponse({"error": "No autenticado"}, status_code=401)

    # 1. Obtenemos mensajes limpios (solo texto)
    msgs = list_chat_messages(token, chat_id, top=20)
    
    results = []
    # Contadores de Alerta
    risk_counter = {
        "SOBRECARGA_URGENCIA": 0, 
        "ESTRES_ANSIEDAD": 0,
        "CANSANCIO_FATIGA": 0 
    }

    for m in msgs:
        text = m["text"]
        if len(text.strip()) < 3: continue # Ignoramos "ok", "si", etc.
        
        # 2. Análisis con IA
        prediction = nlp_model.final_predict(text)
        labels = prediction["labels"]
        
        # 3. Detectar Riesgos (Si la probabilidad > 40%)
        if labels.get("SOBRECARGA_URGENCIA", 0) > 0.4:
            risk_counter["SOBRECARGA_URGENCIA"] += 1
            
        if labels.get("ESTRES_ANSIEDAD", 0) > 0.4:
            risk_counter["ESTRES_ANSIEDAD"] += 1
            
        if labels.get("CANSANCIO_FATIGA", 0) > 0.4:
            risk_counter["CANSANCIO_FATIGA"] += 1

        results.append({
            "message": text,
            "author": m["from"],
            "date": m["createdDateTime"],
            "analysis": labels
        })
        
    return {
        "summary": {
            "total_messages": len(msgs),
            "analyzed": len(results),
            "risks_detected": risk_counter
        },
        "details": results
    }

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
