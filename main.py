from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from nlp import SentimentHFModel

# Instanciamos el modelo globalmente (se cargará el pipeline una vez, singleton)
nlp_engine = SentimentHFModel()

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

# 2. Endpoint para predecir (usa nlp_engine)
@app.post("/predict")
def predict_text(request: TextRequest):
    # Llamamos a la función predict del nuevo motor NLP
    resultado = nlp_engine.predict(request.text)
    return resultado
