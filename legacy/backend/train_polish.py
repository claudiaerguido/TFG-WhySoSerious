import pandas as pd
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments, DataCollatorWithPadding
import torch
import os
import numpy as np
from sklearn.metrics import f1_score

# ==========================================
# 1. CONFIGURACIÓN DEL RE-ENTRENAMIENTO (FINE-TUNING SECUNDARIO)
# ==========================================

# Modelo base: Partimos del modelo ya entrenado en la Fase Principal (`train_teams.py`)
# en lugar de "bert-base". Esto permite refinar conocimientos previos.
MODEL_BASE = "./models/final_teams" 

# Directorio de salida (Sobreescribimos para que sea la versión definitiva)
OUTPUT_DIR = "./models/final_teams_polished"

# Datos para el refinamiento (Pueden ser nuevos datos o el mismo dataset con correcciones)
TARGET_CSV = "../data/teams_train_manual.csv" # Usamos el training set manual
VAL_CSV = "../data/teams_val_manual.csv"

TARGET_LABELS = [
    "TRISTEZA", 
    "ESTRES_ANSIEDAD", 
    "ENFADO_IRRITACION", 
    "SOBRECARGA_URGENCIA", 
    "CANSANCIO_FATIGA", 
    "POSITIVO_ALIVIO", 
    "NEUTRO"
]

def main():
    print("--- Iniciando Fase de Refinamiento (Polishing) ---")
    
    # Validar existencia del modelo base
    if not os.path.exists(MODEL_BASE):
        print(f"Error: No existe el modelo base en {MODEL_BASE}. Ejecuta train_teams.py primero.")
        return

    # ==========================================
    # 2. CARGA Y PREPROCESAMIENTO
    # ==========================================
    
    # Función auxiliar para vectorizar etiquetas
    def map_labels(row):
        vec = [0.0] * len(TARGET_LABELS)
        for i, label in enumerate(TARGET_LABELS):
            if label in row and row[label] == 1:
                vec[i] = 1.0
        return vec

    def prep_df(df_path):
        try:
            df = pd.read_csv(df_path)
            data = []
            for _, row in df.iterrows():
                # En este script asumimos que el CSV ya tiene las columnas one-hot o las mapeamos
                # Si el CSV es igual al de train_teams, usamos la lógica de columnas directas
                vec = [row[l] for l in TARGET_LABELS]
                data.append({"text": row["text"], "labels": [float(v) for v in vec]})
            return Dataset.from_list(data)
        except Exception as e:
            print(f"Error procesando {df_path}: {e}")
            return None

    ds_train = prep_df(TARGET_CSV)
    ds_val = prep_df(VAL_CSV)
    
    if not ds_train or not ds_val:
        return

    print(f"Datos de refinamiento cargados. Train: {len(ds_train)}")
    
    # ==========================================
    # 3. TOKENIZER Y MODELO
    # ==========================================
    tokenizer = AutoTokenizer.from_pretrained(MODEL_BASE) 
    
    # Cargamos el modelo previo (Transfer Learning incremental)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_BASE, 
        num_labels=len(TARGET_LABELS),
        problem_type="multi_label_classification",
        # Aseguramos consistencia en los mapas de etiquetas
        id2label={i: l for i, l in enumerate(TARGET_LABELS)},
        label2id={l: i for i, l in enumerate(TARGET_LABELS)}
    )

    def tokenize(examples):
        return tokenizer(examples["text"], truncation=True, padding=False, max_length=128)
    
    ds_train_tok = ds_train.map(tokenize, batched=True)
    ds_val_tok = ds_val.map(tokenize, batched=True)

    # ==========================================
    # 4. HIPERPARÁMETROS DE REFINAMIENTO
    # ==========================================
    # Notas técnicas:
    # - Learning Rate MUY BAJO (2e-5): Para no destruir lo que ya aprendió el modelo.
    # - Pocas épocas (5): Solo queremos ajustes finos, no re-entrenar desde cero.
    args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        overwrite_output_dir=True,
        eval_strategy="epoch",
        save_strategy="epoch", 
        load_best_model_at_end=True,
        metric_for_best_model="f1_micro",
        learning_rate=2e-5,      # LR reducido para estabilidad
        per_device_train_batch_size=8,
        num_train_epochs=5,      # Ciclo corto
        logging_steps=10,
        save_total_limit=1       # Limitar checkpoints para ahorrar espacio
    )

    # Misma métrica F1
    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        predictions = (1 / (1 + np.exp(-logits))) > 0.5
        score = f1_score(labels, predictions, average='micro')
        return {"f1_micro": score}

    # Data Collator para padding dinámico (eficiencia)
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=ds_train_tok,
        eval_dataset=ds_val_tok,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics
    )

    # ==========================================
    # 5. EJECUCIÓN
    # ==========================================
    print("Iniciando refinamiento del modelo...")
    trainer.train()
    
    print(f"Guardando modelo refinado (Polished) en {OUTPUT_DIR}")
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

if __name__ == "__main__":
    main()
