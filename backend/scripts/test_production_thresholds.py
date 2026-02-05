
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import json
import numpy as np

# Config
MODEL_PATH = "./models/final_teams"
THRESHOLDS_FILE = "thresholds_phaseB.json"
TARGET_LABELS = ["TRISTEZA", "ESTRES_ANSIEDAD", "ENFADO_IRRITACION", "SOBRECARGA_URGENCIA", "CANSANCIO_FATIGA", "POSITIVO_ALIVIO", "NEUTRO"]

# Nuevos umbrales propuestos para producción (Más conservadores en Estrés/Sobrecarga)
# Actuales B1: ESTRES: 0.15, SOBRECARGA: 0.10, NEUTRO: 0.65
PROD_THRESHOLDS = {
    "TRISTEZA": 0.25,
    "ESTRES_ANSIEDAD": 0.35,      # Subido de 0.15 a 0.35
    "ENFADO_IRRITACION": 0.30,
    "SOBRECARGA_URGENCIA": 0.30,  # Subido de 0.10 a 0.30
    "CANSANCIO_FATIGA": 0.25,     # Subido de 0.10 a 0.25
    "POSITIVO_ALIVIO": 0.40,
    "NEUTRO": 0.60                # Mantenido alto
}

stress_test_phrases = [
    "Vale, lo subo luego",
    "Confirmado",
    "He actualizado la diapositiva",
    "Mañana nos reunimos a las 10",
    "El cliente ha pedido un cambio menor",
    "Estoy revisando el documento",
    "Ya he terminado la parte de backend",
    "Queda pendiente el test de integración",
    "Lo miro en un hueco",
    "Gracias, recibido"
]

def predict_with_logic(probs, thresholds):
    prob_map = {label: probs[i] for i, label in enumerate(TARGET_LABELS)}
    final_pred = []
    has_emotion = False
    
    for i in range(6):
        label = TARGET_LABELS[i]
        th = thresholds.get(label, 0.5)
        if prob_map[label] >= th:
            final_pred.append(f"{label} ({prob_map[label]:.2f})")
            has_emotion = True
            
    if not has_emotion:
        th_neu = thresholds.get("NEUTRO", 0.65)
        if prob_map["NEUTRO"] >= th_neu:
            final_pred.append(f"NEUTRO ({prob_map['NEUTRO']:.2f})")
        else:
             final_pred.append(f"INCERTO (Max: {max(probs):.2f})")
            
    return final_pred

def main():
    print(f"--- Stress Test: Neutral False Positives ---")
    print(f"Thresholds (PROD Proposed): {PROD_THRESHOLDS}")
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
    model.eval()
    
    print("\nEvaluando frases neutras delicadas:")
    for text in stress_test_phrases:
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.sigmoid(outputs.logits).squeeze().numpy()
            
        pred = predict_with_logic(probs, PROD_THRESHOLDS)
        
        print(f"TXT: {text[:40]:<40} | PRED: {pred}")
        # Show specific dangerous probs
        estres = probs[TARGET_LABELS.index("ESTRES_ANSIEDAD")]
        sobrecarga = probs[TARGET_LABELS.index("SOBRECARGA_URGENCIA")]
        if estres > 0.1 or sobrecarga > 0.1:
             print(f"    -> Riesgo (Raw Probs): Estrés={estres:.2f}, Sobrecarga={sobrecarga:.2f}")

if __name__ == "__main__":
    main()
