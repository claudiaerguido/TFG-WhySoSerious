# nlp_model.py
# Módulo de Inferencia para Clasificación de Texto Multilabel y Sentimiento (Estrellas)

import torch
import numpy as np
import json
import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# ==========================================
# CONFIGURACIÓN DEL MODELO
# ==========================================

# Modelo de Producción (Emociones)
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models/final_teams")
THRESHOLDS_PATH = os.path.join(os.path.dirname(__file__), "thresholds_phaseB.json")

# Modelo Baseline (Sentimiento Original - Estrellas)
# Este modelo clasifica el texto en una escala de 1 a 5 estrellas.
BASELINE_MODEL_ID = "nlptown/bert-base-multilingual-uncased-sentiment"
    
LABELS = ["TRISTEZA", "ESTRES_ANSIEDAD", "ENFADO_IRRITACION", "SOBRECARGA_URGENCIA", "CANSANCIO_FATIGA", "POSITIVO_ALIVIO", "NEUTRO"]

class NLPModel:
    def __init__(self):
        print(f"🔄 Cargando modelo NLP (Emociones) desde: {MODEL_PATH}")
        self.model = None
        self.tokenizer = None
        
        # 1. Carga del modelo de emociones (Fine-tuneado para Teams)
        try:
            if os.path.exists(MODEL_PATH):
                self.tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
                self.model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
                self.model.eval()
                print("✅ Modelo de Emociones cargado correctamente.")
            else:
                print(f"⚠️ No se encontró el modelo en {MODEL_PATH}")
        except Exception as e:
            print(f"⚠️ Error cargando modelo de emociones: {e}")

        # 2. Carga del modelo baseline (Sentiento Original de Estrellas)
        print(f"🔄 Cargando modelo Baseline (Sentimiento) [{BASELINE_MODEL_ID}]...")
        self.base_tokenizer = None
        self.base_model = None
        try:
            self.base_tokenizer = AutoTokenizer.from_pretrained(BASELINE_MODEL_ID)
            self.base_model = AutoModelForSequenceClassification.from_pretrained(BASELINE_MODEL_ID)
            self.base_model.eval()
            print("✅ Modelo Baseline cargado correctamente.")
        except Exception as e:
            print(f"⚠️ Error cargando modelo baseline: {e}")

    def load_thresholds(self):
        """Carga los umbrales dinámicos para el modelo de emociones."""
        default_thresholds = {label: 0.5 for label in LABELS}
        try:
            if os.path.exists(THRESHOLDS_PATH):
                with open(THRESHOLDS_PATH, 'r') as f:
                    return json.load(f)
            return default_thresholds
        except Exception as e:
            print(f"⚠️ Error leyendo thresholds.json: {e}")
            return default_thresholds

    def predict(self, text: str):
        """Realiza la predicción multilabel de emociones."""
        thresholds = self.load_thresholds()
        if not self.model or not self.tokenizer:
            return {"labels": {l: 0.0 for l in LABELS}, "thresholds": thresholds, "is_fallback": True, "detected_labels": []}

        try:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=128, padding=True)
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits.numpy()[0]
            
            # Sigmoide para probabilidades independientes (multilabel)
            probs = 1 / (1 + np.exp(-logits)) 
            
            results = {}
            flags = []
            for i, label in enumerate(LABELS):
                probability = float(probs[i])
                results[label] = probability
                if probability >= thresholds.get(label, 0.5):
                    flags.append(label)

            return {"labels": results, "thresholds": thresholds, "is_fallback": False, "detected_labels": flags}
        except Exception as e:
            print(f"Error en predict: {e}")
            return {"labels": {l: 0.0 for l in LABELS}, "thresholds": thresholds, "is_fallback": True, "detected_labels": []}

    def predict_sentiment(self, text: str):
        """Realiza la predicción de sentimiento original (1-5 estrellas)."""
        if not self.base_model or not self.base_tokenizer:
            return {"label": "Error", "score": 0.0}
        
        try:
            inputs = self.base_tokenizer(text, return_tensors="pt", truncation=True, max_length=128, padding=True)
            with torch.no_grad():
                outputs = self.base_model(**inputs)
                # Softmax para clases mutuamente excluyentes (estrellas)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1).numpy()[0]
            
            # El modelo nlptown devuelve 5 clases: [1 star, 2 stars, 3 stars, 4 stars, 5 stars]
            idx = np.argmax(probs)
            star_labels = ["1 estrella", "2 estrellas", "3 estrellas", "4 estrellas", "5 estrellas"]
            
            return {
                "label": star_labels[idx],
                "score": float(probs[idx]),
                "stars": int(idx + 1)
            }
        except Exception as e:
            print(f"Error en predict_sentiment: {e}")
            return {"label": "Error", "score": 0.0}

# Instancia global del servicio
nlp_service = NLPModel()

# --- Funciones de exportación para compatibilidad ---

def final_predict(text):
    """Predicción completa de emociones."""
    return nlp_service.predict(text)

def baseline_predict(text):
    """Predicción original basada en estrellas."""
    return nlp_service.predict_sentiment(text)

# Marcador de disponibilidad para el servidor
_model = nlp_service.model