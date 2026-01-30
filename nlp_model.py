# nlp_model.py
# Módulo de Inferencia para Clasificación de Texto Multilabel

import torch
import numpy as np
import json
import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# ==========================================
# CONFIGURACIÓN DEL MODELO
# ==========================================

# Ruta dinámica al modelo fine-tuneado (Fase B)
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models/final_teams")
# Archivo de configuración de umbrales dinámicos
THRESHOLDS_PATH = os.path.join(os.path.dirname(__file__), "thresholds_phaseB.json")

# Etiquetas del modelo
LABELS = [
    "TRISTEZA", 
    "ESTRES_ANSIEDAD", 
    "ENFADO_IRRITACION", 
    "SOBRECARGA_URGENCIA", 
    "CANSANCIO_FATIGA", 
    "POSITIVO_ALIVIO", 
    "NEUTRO"
]

class NLPModel:
    def __init__(self):
        """
        Inicializa el modelo NLP cargando el tokenizador y los pesos del modelo.
        """
        print(f"🔄 Cargando modelo NLP desde: {MODEL_PATH}")
        self.model = None
        self.tokenizer = None
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
            self.model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
            self.model.eval() # Establecer modelo en modo evaluación (desactiva dropout, etc.)
            print("✅ Modelo cargado correctamente.")
        except Exception as e:
            print(f"⚠️ Error cargando modelo local: {e}. El sistema funcionará en modo degradado (Fallback).")

    def load_thresholds(self):
        """
        Carga los umbrales de decisión desde el archivo JSON de configuración.
        Permite ajustar la sensibilidad del modelo sin reentrenar.
        """
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
        """
        Realiza la inferencia sobre el texto de entrada.
        Devuelve probabilidades crudas y metadatos.
        """
        thresholds = self.load_thresholds()
        
        # Fallback si el modelo no está cargado
        if not self.model or not self.tokenizer:
            return {
                "labels": {l: 0.0 for l in LABELS}, # Todo a cero
                "thresholds": thresholds,
                "is_fallback": True,
                "detected_labels": []
            }

        try:
            # 1. Preprocesamiento (Tokenización)
            inputs = self.tokenizer(
                text, 
                return_tensors="pt", 
                truncation=True, 
                max_length=128, 
                padding=True
            )

            # 2. Inferencia (Forward Pass)
            with torch.no_grad(): # Desactivamos gradientes para inferencia
                outputs = self.model(**inputs)
                logits = outputs.logits.numpy()[0]

            # 3. Post-procesamiento (Sigmoide)
            probs = 1 / (1 + np.exp(-logits)) 
            
            results = {}
            flags = []

            # 4. Decisión (Thresholding)
            for i, label in enumerate(LABELS):
                probability = float(probs[i])
                threshold = thresholds.get(label, 0.5)
                
                results[label] = probability
                
                # Decisión de activación
                if probability >= threshold:
                    flags.append(label)

            return {
                "labels": results,
                "thresholds": thresholds,
                "is_fallback": False,
                "detected_labels": flags
            }
            
        except Exception as e:
            print(f"Error en inferencia: {e}")
            return {
                "labels": {l: 0.0 for l in LABELS},
                "thresholds": thresholds,
                "is_fallback": True,
                "detected_labels": []
            }

# Instancia global del modelo (Singleton implícito)
nlp_service = NLPModel()

# --- API Pública para Scripts Externos ---

def final_predict(text):
    """
    Función envoltorio (Wrapper) utilizada por main.py y evaluate_goldset.py.
    Garantiza una interfaz estable para la predicción.
    """
    return nlp_service.predict(text)