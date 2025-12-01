from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import nlp_model  # Importamos nuestro "cerebro" del Bloque A

# Creamos la aplicación FastAPI
app = FastAPI()

# Configuración de CORS (para que el Frontend pueda hablar con el Backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción esto debería ser más restrictivo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Definimos el modelo de datos para recibir texto en POST /predict
class TextRequest(BaseModel):
    text: str

# 1. Endpoint de salud (Health Check)
@app.get("/health")
def health_check():
    return {"status": "ok"}

# 2. Endpoint para predecir (usa nlp_model)
@app.post("/predict")
def predict_text(request: TextRequest):
    # Llamamos a la función predict que creamos en el Bloque A
    resultado = nlp_model.predict(request.text)
    return resultado

# 3. Endpoint para obtener mensajes simulados (Mock)
@app.get("/messages")
def get_messages():
    # Simulamos unos mensajes de Teams para probar luego el frontend
    return [
        {"id": 1, "author": "Juan", "text": "El proyecto va genial, estoy muy contento."},
        {"id": 2, "author": "Ana", "text": "No llego a los plazos, estoy muy estresada."},
        {"id": 3, "author": "Luis", "text": "Reunión mañana a las 10."},
        {"id": 4, "author": "Marta", "text": "Odio este software, falla siempre."}
    ]
