import os
import torch
import pandas as pd
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.metrics import f1_score, precision_recall_fscore_support

import json

# Config
MODEL_PATH = "./models/final_teams"
TEST_CSV = "../data/teams_test.csv"
VAL_CSV = "../data/teams_val.csv"
THRESHOLDS_FILE = "thresholds_phaseB.json"
TARGET_LABELS = ["TRISTEZA", "ESTRES_ANSIEDAD", "ENFADO_IRRITACION", "SOBRECARGA_URGENCIA", "CANSANCIO_FATIGA", "POSITIVO_ALIVIO", "NEUTRO"]

def load_thresholds():
    with open(THRESHOLDS_FILE, 'r') as f:
        return json.load(f)

def predict_with_logic(probs, thresholds):
    """
    Aplica lógica:
    1. Check predicciones emocionales (Labels 0-5)
    2. Si alguna > su umbral -> Esa = 1, NEUTRO = 0
    3. Si ninguna > umbral -> Check NEUTRO > su umbral (0.65)
    """
    
    # Map label -> prob
    prob_map = {label: probs[i] for i, label in enumerate(TARGET_LABELS)}
    
    final_pred = [0] * 7 # Vector de saliday
    has_emotion = False
    
    # 1. Check emotions (indices 0-5)
    for i in range(6): # Los primeros 6 son emociones
        label = TARGET_LABELS[i]
        th = thresholds.get(label, 0.5)
        if prob_map[label] >= th:
            final_pred[i] = 1
            has_emotion = True
            
    # 2. Logic Neutral
    if has_emotion:
        final_pred[6] = 0 # NEUTRO id 6
    else:
        # Check Neutral threshold
        th_neu = thresholds.get("NEUTRO", 0.65)
        if prob_map["NEUTRO"] >= th_neu:
            final_pred[6] = 1
        else:
            # Fallback? Si no es nada, ¿lo marcamos neutro por defecto o todo ceros?
            # Por ahora todo ceros (Incerto) o Neutro default. 
            # Guía: "Si ninguna supera, decide con umbral 0.60". 
            pass 
            
    return final_pred

def evaluate_split(csv_path, split_name):
    print(f"\nEvaluando Split: {split_name} ({csv_path})")
    
    thresholds = load_thresholds()
    print(f"Thresholds loaded: {thresholds}")
    
    # Cargar datos de prueba (Manual Val Split)
    data_path = "../data/teams_val_manual.csv"  
    print(f"Evaluando con dataset MANUAL VAL: {data_path}")
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
    model.eval()
    
    # Cargar Data
    df = pd.read_csv(data_path)
    
    preds_all = []
    labels_all = []
    
    print("\n--- EJEMPLOS (Solo errores) ---")
    for idx, row in df.iterrows():
        text = row["text"]
        gt = [
            row["TRISTEZA"], row["ESTRES_ANSIEDAD"], row["ENFADO_IRRITACION"],
            row["SOBRECARGA_URGENCIA"], row["CANSANCIO_FATIGA"], row["POSITIVO_ALIVIO"],
            row["NEUTRO"]
        ]
        gt = [int(x) for x in gt]
        
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.sigmoid(outputs.logits).squeeze().numpy()
            
        pred = predict_with_logic(probs, thresholds)
        
        preds_all.append(pred)
        labels_all.append(gt)
        
        if list(pred) != gt:
            print(f"TXT: {text[:40]}...")
            print(f"  GT:   {gt}")
            print(f"  PRED: {list(pred)}")
            # Mostrar probs relevantes (cercanas al umbral)
            probs_fmt = {l: round(probs[i], 2) for i, l in enumerate(TARGET_LABELS) if probs[i] > 0.1}
            print(f"  PROBS:{probs_fmt}")

    preds_np = np.array(preds_all)
    labels_np = np.array(labels_all)
    
    micro = f1_score(labels_np, preds_np, average='micro', zero_division=0)
    macro = f1_score(labels_np, preds_np, average='macro', zero_division=0)
    
    print(f"\n[{split_name}] F1 Micro: {micro:.4f} | F1 Macro: {macro:.4f}")
    
    # Per label details
    p, r, f, _ = precision_recall_fscore_support(labels_np, preds_np, average=None, zero_division=0)
    print(f"{'Label':<20} {'F1':<5} {'Prec':<5} {'Rec':<5}")
    for i, name in enumerate(TARGET_LABELS):
        print(f"{name:<20} {f[i]:.2f}  {p[i]:.2f}  {r[i]:.2f}")

if __name__ == "__main__":
    evaluate_split(VAL_CSV, "VALIDATION")
    evaluate_split(TEST_CSV, "TEST")
