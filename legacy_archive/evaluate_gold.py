
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import json
import numpy as np
from sklearn.metrics import f1_score

# Config
MODEL_PATH = "./models/final_teams"
GOLD_CSV = "../data/teams_gold_dataset.csv" # The 40-item curated gold set
THRESHOLDS_FILE = "thresholds_phaseB.json"
TARGET_LABELS = ["TRISTEZA", "ESTRES_ANSIEDAD", "ENFADO_IRRITACION", "SOBRECARGA_URGENCIA", "CANSANCIO_FATIGA", "POSITIVO_ALIVIO", "NEUTRO"]

def load_thresholds():
    with open(THRESHOLDS_FILE, 'r') as f:
        return json.load(f)

def predict_with_logic(probs, thresholds):
    prob_map = {label: probs[i] for i, label in enumerate(TARGET_LABELS)}
    final_pred = [0] * 7
    has_emotion = False
    
    for i in range(6):
        label = TARGET_LABELS[i]
        th = thresholds.get(label, 0.5)
        if prob_map[label] >= th:
            final_pred[i] = 1
            has_emotion = True
            
    if has_emotion:
        final_pred[6] = 0
    else:
        th_neu = thresholds.get("NEUTRO", 0.65)
        if prob_map["NEUTRO"] >= th_neu:
            final_pred[6] = 1
            
    return final_pred

def main():
    print(f"--- Evaluación Final en GOLD SET ({GOLD_CSV}) ---")
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
    model.eval()
    
    thresholds = load_thresholds()
    df = pd.read_csv(GOLD_CSV)
    
    preds_all = []
    labels_all = []
    
    print(f"\nProcesando {len(df)} ejemplos...")
    
    for idx, row in df.iterrows():
        text = row["text"]
        # Asumimos columnas one-hot en el CSV o las generamos
        # El gold set original tenia columnas: text, TRISTEZA, etc...
        gt = []
        for l in TARGET_LABELS:
            gt.append(row.get(l, 0)) # 0 si no existe
        gt = [int(x) for x in gt]
        
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.sigmoid(outputs.logits).squeeze().numpy()
            
        pred = predict_with_logic(probs, thresholds)
        
        preds_all.append(pred)
        labels_all.append(gt)
        
        # Debug clean outputs
        print(f"TXT: {text[:60]:<60} | PRED: {[TARGET_LABELS[i] for i,x in enumerate(pred) if x==1]}")

    preds_np = np.array(preds_all)
    labels_np = np.array(labels_all)
    
    micro = f1_score(labels_np, preds_np, average='micro', zero_division=0)
    
    print(f"\nRESULTADOS GOLD SET:")
    print(f"F1 MICRO: {micro:.4f}")

if __name__ == "__main__":
    main()
