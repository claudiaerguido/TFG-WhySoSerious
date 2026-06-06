import torch
import numpy as np
import json
import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# --- Configuración del modelo ---

# Modelo de Producción (Emociones)
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models/final_teams")
THRESHOLDS_PATH = os.path.join(os.path.dirname(__file__), "thresholds.json")

# Modelo Baseline (Sentimiento Original - Estrellas)
BASELINE_MODEL_ID = "nlptown/bert-base-multilingual-uncased-sentiment"

# Etiquetas del modelo de emociones
LABELS = ["ESTRES_ANSIEDAD", "ENFADO_IRRITACION", "SOBRECARGA_URGENCIA", "CANSANCIO_FATIGA", "NEUTRO"]

# Núcleo Operativo del TFG (Señales de Riesgo Psicosocial)
OPERATIVE_CORE = ["ESTRES_ANSIEDAD", "ENFADO_IRRITACION", "SOBRECARGA_URGENCIA", "CANSANCIO_FATIGA"]

class NLPModel:
    def __init__(self):
        print(f"Cargando modelo NLP (Emociones) desde: {MODEL_PATH}")
        self.model = None
        self.tokenizer = None
        
        # 1. Carga del modelo de emociones (Fine-tuneado para Teams)
        try:
            if os.path.exists(MODEL_PATH):
                self.tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
                self.model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
                self.model.eval()
                print("Modelo de Emociones cargado correctamente.")
            else:
                print(f"No se encontró el modelo en {MODEL_PATH}")
        except Exception as e:
            print(f"Error cargando modelo de emociones: {e}")

        # 2. Carga del modelo baseline (Estrellas)
        self.base_tokenizer = None
        self.base_model = None
        try:
            self.base_tokenizer = AutoTokenizer.from_pretrained(BASELINE_MODEL_ID)
            self.base_model = AutoModelForSequenceClassification.from_pretrained(BASELINE_MODEL_ID)
            self.base_model.eval()
            print("Modelo Baseline cargado.")
        except Exception as e:
            print(f"Error cargando baseline: {e}")

        # 3. Carga de umbrales dinámicos
        self.thresholds = self._load_thresholds()
        print(f"Umbrales de Calibración Estratégica: {self.thresholds}")

    def _load_thresholds(self):
        """Carga los umbrales dinámicos desde el archivo config."""
        default = {l: 0.5 for l in LABELS}
        try:
            if os.path.exists(THRESHOLDS_PATH):
                with open(THRESHOLDS_PATH, 'r') as f:
                    return json.load(f)
            return default
        except Exception:
            return default

    def predict(self, text: str):
        """Predicción multilabel de emociones con salvaguarda para el núcleo operativo."""
        if not self.model or not self.tokenizer:
            return self._get_fallback_predict()

        try:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=128, padding=True)
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits.detach().cpu().numpy()[0]
            
            probs = 1 / (1 + np.exp(-logits)) 
            results = {label: float(probs[i]) for i, label in enumerate(LABELS)}
            
            # Etiquetas que superan el umbral de decisión
            detected = [label for label, prob in results.items() if prob >= self.thresholds.get(label, 0.5)]
            flags = [l for l in detected if l in OPERATIVE_CORE]
            

            # Limpiar duplicados y fallback a neutro
            flags = list(dict.fromkeys(flags)) or ["NEUTRO"]

            return {
                "labels": results, 
                "thresholds": self.thresholds, 
                "is_fallback": False, 
                "detected_labels": flags
            }
        except Exception as e:
            print(f" Error en predict: {e}")
            return self._get_fallback_predict()

    def _get_fallback_predict(self):
        """Devuelve un resultado neutro si falla la inferencia."""
        return {
            "labels": {l: 0.0 for l in LABELS},
            "thresholds": getattr(self, "thresholds", {}),
            "is_fallback": True,
            "detected_labels": []
        }

    def predict_sentiment(self, text: str):
        """Predicción de sentimiento baseline (1-5 estrellas)."""
        if not self.base_model or not self.base_tokenizer:
            return {"label": "Error", "score": 0.0, "stars": 0}
        
        try:
            inputs = self.base_tokenizer(text, return_tensors="pt", truncation=True, max_length=128, padding=True)
            with torch.no_grad():
                outputs = self.base_model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1).detach().cpu().numpy()[0]
            
            idx = np.argmax(probs)
            star_labels = ["1 estrella", "2 estrellas", "3 estrellas", "4 estrellas", "5 estrellas"]
            
            return {
                "label": star_labels[idx],
                "score": float(probs[idx]),
                "stars": int(idx + 1)
            }
        except Exception as e:
            print(f"Error en predict_sentiment: {e}")
            return {"label": "Error", "score": 0.0, "stars": 0}

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
