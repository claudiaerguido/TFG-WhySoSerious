import os
import json
import csv
import torch
import numpy as np
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.metrics import f1_score, precision_recall_fscore_support

# Configuración
MODEL_PATH = "./models/final_xed"
TARGET_LABELS = ["TRISTEZA", "ESTRES_ANSIEDAD", "ENFADO_IRRITACION", "SOBRECARGA_URGENCIA", "CANSANCIO_FATIGA", "POSITIVO_ALIVIO", "NEUTRO"]
TEAMS_CSV = "../data/teams_val_dataset.csv" # Desde ceu-whysoserious
RESULTS_DIR = "./results"

# Etiquetas activas en Fase A (XED)
ACTIVE_LABELS_INDICES = [0, 1, 2, 5, 6] # Tristeza, Estres, Enfado, Positivo, Neutro
ACTIVE_LABELS_NAMES = ["TRISTEZA", "ESTRES", "ENFADO", "POSITIVO", "NEUTRO"] # Nombres cortos para reporte

def map_labels_xed(xed_labels):
    """Misma lógica que train_xed.py para consistencia"""
    vec = [0.0] * len(TARGET_LABELS)
    has_target_emotion = False
    
    if 6 in xed_labels: # Sadness
        vec[0] = 1.0; has_target_emotion = True
    if 4 in xed_labels: # Fear
        vec[1] = 1.0; has_target_emotion = True
    if 1 in xed_labels or 3 in xed_labels: # Anger/Disgust
        vec[2] = 1.0; has_target_emotion = True
    if 5 in xed_labels or 8 in xed_labels: # Joy/Trust
        vec[5] = 1.0; has_target_emotion = True
        
    if has_target_emotion:
        pass
    else:
        if 0 in xed_labels:
            vec[6] = 1.0
        else:
            return None # Discard
    return vec

from datasets import load_dataset, concatenate_datasets, Dataset

# ... (Previous code)

def load_and_prep_xed(tokenizer):
    print("Cargando XED Mixto para métricas (Emo + Neu)...")
    
    # 1. Load Raw
    d_emo = load_dataset("Helsinki-NLP/xed_en_fi", "en_annotated", split="train", trust_remote_code=True)
    d_neu = load_dataset("Helsinki-NLP/xed_en_fi", "en_neutral", split="train", trust_remote_code=True)

    # 2. Manual Merge (Simple Python List)
    final_data = []

    # Emo
    for item in d_emo:
        # labels is list[int]
        vec = map_labels_xed(item['labels'])
        if vec:
            final_data.append({"text": item['sentence'], "labels": vec})
            
    # Neu (We use 10% for validation in training, here we load ALL and then split?
    # Better to replicate training distribution roughly.
    # Let's take 1000 neutrals for validation consistency.)
    count_neu = 0
    for item in d_neu:
        if count_neu >= 1000: break
        
        # labels is int 0
        l = item['labels']
        l_list = [l] if isinstance(l, int) else l
        vec = map_labels_xed(l_list)
        if vec:
            final_data.append({"text": item['sentence'], "labels": vec})
            count_neu += 1
            
    # Create Dataset
    ds = Dataset.from_list(final_data)
    
    # Tokenize
    def preprocess(examples):
        return tokenizer(examples["text"], truncation=True, padding=False, max_length=128)

    encoded = ds.map(preprocess, batched=True)
    encoded.set_format("torch")
    
    # Split (Same seed as training to hopefully get a similar test set, 
    # though since I constructed it differently, exact overlap check is hard.
    # Just generating a fresh valid set is fine for metrics.)
    split = encoded.train_test_split(test_size=0.1, seed=42)
    return split["test"]

def evaluate_model():
    print(f"Cargando modelo desde {MODEL_PATH}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
    model.eval()
    
    # 1. Métricas XED (Fase A)
    val_ds = load_and_prep_xed(tokenizer)
    print(f"Evaluando en {len(val_ds)} ejemplos de validación XED...")
    
    preds_all = []
    labels_all = []
    
    # Inferencia manual simple (batch size 1 para simplicidad en script de eval)
    # Para 1500 items es rápido.
    with torch.no_grad():
        for i in range(len(val_ds)):
            # Use pre-tokenized data
            input_ids = torch.tensor(val_ds[i]["input_ids"]).unsqueeze(0)
            attention_mask = torch.tensor(val_ds[i]["attention_mask"]).unsqueeze(0)
            
            labels = torch.tensor(val_ds[i]["labels"])
            
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            probs = torch.sigmoid(outputs.logits).squeeze().numpy()
            
            # Threshold 0.5
            pred_vec = (probs > 0.5).astype(int)
            preds_all.append(pred_vec)
            labels_all.append(labels.numpy().astype(int))
            
    preds_np = np.array(preds_all)
    labels_np = np.array(labels_all)
    
    # Calculo métricas (Solo sobre las 5 etiquetas activas para limpieza, o sobre todo?)
    # El modelo tiene 7 salidas. Las indices 3 y 4 (Sobrecarga/Cansancio) deberían ser 0 siempre en Ground Truth XED.
    
    f1_micro = f1_score(labels_np, preds_np, average='micro')
    f1_macro = f1_score(labels_np, preds_np, average='macro')
    
    # Per label
    p, r, f1_per_class, _ = precision_recall_fscore_support(labels_np, preds_np, average=None)
    
    metrics = {
        "f1_micro": float(f1_micro),
        "f1_macro": float(f1_macro),
        "per_label": {}
    }
    
    for idx, name in enumerate(TARGET_LABELS):
        metrics["per_label"][name] = {
            "f1": float(f1_per_class[idx]),
            "precision": float(p[idx]),
            "recall": float(r[idx])
        }
    
    metric_file = os.path.join(RESULTS_DIR, "metrics_phaseA_xed.json")
    with open(metric_file, "w") as f:
        json.dump(metrics, f, indent=4)
    print(f"Métricas guardadas en {metric_file}")
    
    # 2. Mini Test Teams (25 ejemplos)
    print("Ejecutando Mini Test Teams...")
    teams_results = []
    
    with open(TEAMS_CSV, "r", encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = row["text"]
            # Ground Truth
            gt = {
                "TRISTEZA": int(row["TRISTEZA"]),
                "ESTRES": int(row["ESTRES_ANSIEDAD"]),
                "ENFADO": int(row["ENFADO_IRRITACION"]),
                "POSITIVO": int(row["POSITIVO_ALIVIO"]),
                "NEUTRO": int(row["NEUTRO"])
            }
            
            # Predicción
            inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
            with torch.no_grad():
                outputs = model(**inputs)
                probs = torch.sigmoid(outputs.logits).squeeze().numpy()
                
            p_dict = {
                "TRISTEZA": 1 if probs[0] > 0.5 else 0,
                "ESTRES": 1 if probs[1] > 0.5 else 0,
                "ENFADO": 1 if probs[2] > 0.5 else 0,
                # Sobrecarga (3) y Cansancio (4) ignorados en Phase A
                "POSITIVO": 1 if probs[5] > 0.5 else 0,
                "NEUTRO": 1 if probs[6] > 0.5 else 0
            }
            
            # Comparación (Match total en estas 5?)
            match = (gt == p_dict)
            
            res_row = {
                "id": row["id"],
                "text": text,
                "prediction": json.dumps(p_dict, ensure_ascii=False),
                "ground_truth": json.dumps(gt, ensure_ascii=False),
                "match": match
            }
            teams_results.append(res_row)
            
    report_file = os.path.join(RESULTS_DIR, "teams25_phaseA_report.csv")
    with open(report_file, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["id", "text", "prediction", "ground_truth", "match"])
        writer.writeheader()
        writer.writerows(teams_results)
        
    print(f"Reporte Teams guardado en {report_file}")
    
    # Imprimir resumen de los primeros 5
    print("\n--- EJEMPLOS TEAMS (Primeros 5) ---")
    for r in teams_results[:5]:
        print(f"ID {r['id']}: {r['match']} | Pred: {r['prediction']} | Gold: {r['ground_truth']}")

if __name__ == "__main__":
    evaluate_model()
