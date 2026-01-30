import os
import torch
import numpy as np
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.metrics import precision_recall_fscore_support

# Configuración
MODEL_PATH = "./models/final_xed"
TARGET_LABELS = ["TRISTEZA", "ESTRES_ANSIEDAD", "ENFADO_IRRITACION", "SOBRECARGA_URGENCIA", "CANSANCIO_FATIGA", "POSITIVO_ALIVIO", "NEUTRO"]

# Indices de interés para el análisis
IDX_ESTRES = 1
IDX_NEUTRO = 6

def map_labels_xed(xed_labels):
    """Misma lógica que train_xed.py"""
    vec = [0.0] * len(TARGET_LABELS)
    has_target_emotion = False
    
    if 6 in xed_labels: vec[0] = 1.0; has_target_emotion = True
    if 4 in xed_labels: vec[1] = 1.0; has_target_emotion = True
    if 1 in xed_labels or 3 in xed_labels: vec[2] = 1.0; has_target_emotion = True
    if 5 in xed_labels or 8 in xed_labels: vec[5] = 1.0; has_target_emotion = True
        
    if has_target_emotion:
        pass
    else:
        if 0 in xed_labels:
            vec[6] = 1.0
        else:
            return None 
    return vec

from datasets import load_dataset, Dataset

def load_data(tokenizer):
    print("Cargando dataset Mixto (Emo + Neu)...")
    
    # 1. Load Raw
    d_emo = load_dataset("Helsinki-NLP/xed_en_fi", "en_annotated", split="train", trust_remote_code=True)
    d_neu = load_dataset("Helsinki-NLP/xed_en_fi", "en_neutral", split="train", trust_remote_code=True)

    # 2. Manual Merge
    final_data = []

    # Emo
    for item in d_emo:
        vec = map_labels_xed(item['labels'])
        if vec:
            final_data.append({"text": item['sentence'], "labels": vec})
            
    # Neu (Validación consistente con eval: 1000 neutros)
    count_neu = 0
    for item in d_neu:
        if count_neu >= 1000: break
        
        l = item['labels']
        l_list = [l] if isinstance(l, int) else l
        vec = map_labels_xed(l_list)
        if vec:
            final_data.append({"text": item['sentence'], "labels": vec})
            count_neu += 1
            
    # Create Dataset
    ds = Dataset.from_list(final_data)
    
    def preprocess(examples):
        return tokenizer(examples["text"], truncation=True, padding=False, max_length=128)

    encoded = ds.map(preprocess, batched=True)
    encoded.set_format("torch")
    
    # Split
    split = encoded.train_test_split(test_size=0.1, seed=42)
    return split["test"]

def analyze_thresholds():
    print(f"Cargando modelo {MODEL_PATH}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
    model.eval()
    
    val_ds = load_data(tokenizer)
    print(f"Total ejemplos validación: {len(val_ds)}")
    
    all_probs = []
    all_labels = []
    
    print("Ejecutando inferencia...")
    with torch.no_grad():
        for i in range(len(val_ds)):
            input_ids = torch.tensor(val_ds[i]["input_ids"]).unsqueeze(0)
            attention_mask = torch.tensor(val_ds[i]["attention_mask"]).unsqueeze(0)
            labels = torch.tensor(val_ds[i]["labels"])
            
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            probs = torch.sigmoid(outputs.logits).squeeze().numpy()
            
            all_probs.append(probs)
            all_labels.append(labels.numpy())
            
    probs_np = np.array(all_probs)
    labels_np = np.array(all_labels)
    
    # Análisis Distribución Gold
    gold_neutro = np.sum(labels_np[:, IDX_NEUTRO])
    gold_estres = np.sum(labels_np[:, IDX_ESTRES])
    
    print("\n--- DISTRIBUCIÓN GROUND TRUTH ---")
    print(f"Total NEUTRO (Gold): {int(gold_neutro)} ({gold_neutro/len(val_ds)*100:.2f}%)")
    print(f"Total ESTRES (Gold): {int(gold_estres)} ({gold_estres/len(val_ds)*100:.2f}%)")
    
    # Análisis Threshold 0.5 (Baseline)
    pred_neutro_05 = np.sum(probs_np[:, IDX_NEUTRO] > 0.5)
    print(f"Total NEUTRO Pred (th=0.5): {pred_neutro_05} ({pred_neutro_05/len(val_ds)*100:.2f}%)")
    
    if gold_neutro == 0:
        print("\nERROR CRÍTICO: No hay ejemplos NEUTRO en el conjunto de validación.")
        print("Revisar lógica de filtrado o dataset original.")
        return

    print("\n--- SWEEP DE UMBRALES (NEUTRO & ESTRES) ---")
    print(f"{'Threshold':<10} | {'NEUTRO F1':<10} {'Prec':<8} {'Rec':<8} | {'ESTRES F1':<10} {'Prec':<8} {'Rec':<8}")
    print("-" * 80)
    
    thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    
    for th in thresholds:
        preds_th = (probs_np > th).astype(int)
        
        # Calcular metricas per label
        p, r, f, _ = precision_recall_fscore_support(labels_np, preds_th, average=None, zero_division=0)
        
        n_p, n_r, n_f = p[IDX_NEUTRO], r[IDX_NEUTRO], f[IDX_NEUTRO]
        e_p, e_r, e_f = p[IDX_ESTRES], r[IDX_ESTRES], f[IDX_ESTRES]
        
        print(f"{th:<10} | {n_f:<10.4f} {n_p:<8.4f} {n_r:<8.4f} | {e_f:<10.4f} {e_p:<8.4f} {e_r:<8.4f}")

if __name__ == "__main__":
    analyze_thresholds()
