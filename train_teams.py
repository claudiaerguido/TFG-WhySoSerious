import os
import torch
import pandas as pd
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from sklearn.metrics import f1_score
import numpy as np

# ==========================================
# 1. CONFIGURACIÓN DEL ENTRENAMIENTO
# ==========================================

# Ruta del modelo base pre-entrenado (BERT Multilingual para análisis de sentimiento)
BASE_MODEL_PATH = "nlptown/bert-base-multilingual-uncased-sentiment" 
# Directorio de salida para el modelo fine-tuneado
OUTPUT_DIR = "./models/final_teams"

# Datasets de entrada 
TRAIN_CSV = "../data/teams_train_manual.csv" 
VAL_CSV = "../data/teams_val_manual.csv"     

# Etiquetas objetivo para la clasificación multilabel
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
    print(f"--- Iniciando Fine-tuning del Modelo (Fase B: Teams) ---")

    # ==========================================
    # 2. CARGA Y PREPROCESAMIENTO DE DATOS
    # ==========================================
    try:
        df_train = pd.read_csv(TRAIN_CSV)
        df_val = pd.read_csv(VAL_CSV)
        print(f"Datos cargados. Train: {len(df_train)}, Val: {len(df_val)}")
    except Exception as e:
        print(f"Error cargando datasets: {e}")
        return

    # Función para transformar el DataFrame en un Dataset compatible con Hugging Face
    def prep_data(df, is_training=False):
        data = []
        for _, row in df.iterrows():
            # Construcción del vector de etiquetas (One-Hot Encoding)
            labels_vec = [
                row["TRISTEZA"],
                row["ESTRES_ANSIEDAD"],
                row["ENFADO_IRRITACION"],
                row["SOBRECARGA_URGENCIA"],
                row["CANSANCIO_FATIGA"],
                row["POSITIVO_ALIVIO"],
                row["NEUTRO"]
            ]
            labels_vec = [float(x) for x in labels_vec]
            
            # --- ESTRATEGIA DE OVERSAMPLING ---
            # Para mitigar el desbalanceo de clases, duplicamos las muestras de clases minoritarias
            # (Sobrecarga y Cansancio) durante la fase de entrenamiento.
            repeats = 1
            if is_training:
                # Indices 3 (Sobrecarga) y 4 (Cansancio)
                if labels_vec[3] == 1.0 or labels_vec[4] == 1.0: 
                    repeats = 5
            
            for _ in range(repeats):
                data.append({"text": row["text"], "labels": labels_vec})
                
        return Dataset.from_list(data)

    ds_train = prep_data(df_train, is_training=True) 
    ds_val = prep_data(df_val, is_training=False)   

    # ==========================================
    # 3. INICIALIZACIÓN DE TOKENIZER Y MODELO
    # ==========================================
    
    # Carga del Tokenizer correspondiente al modelo base
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_PATH)
    
    def tokenize_function(examples):
        # Tokenización con padding y truncado a 128 tokens
        return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=128)
        
    encoded_train = ds_train.map(tokenize_function, batched=True)
    encoded_val = ds_val.map(tokenize_function, batched=True)

    # Carga del Modelo para Clasificación de Secuencias
    model = AutoModelForSequenceClassification.from_pretrained(
        BASE_MODEL_PATH,
        num_labels=len(TARGET_LABELS),
        ignore_mismatched_sizes=True,
        problem_type="multi_label_classification",
        id2label={i: l for i, l in enumerate(TARGET_LABELS)},
        label2id={l: i for i, l in enumerate(TARGET_LABELS)}
    )

    # ==========================================
    # 4. HIPERPARÁMETROS DEL ENTRENAMIENTO
    # ==========================================
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=15,            # Número de épocas
        learning_rate=5e-5,             # Tasa de aprendizaje
        per_device_train_batch_size=4,  # Tamaño del batch
        eval_strategy="epoch",    # Evaluar al final de cada época
        save_strategy="epoch",          # Guardar checkpoint al final de cada época
        save_total_limit=1,             # GUARDAR SOLO EL ULTIMO CHECKPOINT (Evita llenar disco)
        load_best_model_at_end=True,    # Recuperar el mejor modelo al finalizar
        metric_for_best_model="f1_micro" # Métrica de optimización
    )

    # Función de métricas personalizada (F1-Micro para multilabel)
    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        # Aplicamos sigmoide y umbral de 0.5 para obtener predicciones binarias
        predictions = (1 / (1 + np.exp(-logits))) > 0.5
        score = f1_score(labels, predictions, average='micro')
        return {"f1_micro": score}

    # ==========================================
    # 5. EJECUCIÓN DEL ENTRENAMIENTO
    # ==========================================
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=encoded_train,
        eval_dataset=encoded_val,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
    )

    print("🚀 Ejecutando entrenamiento...")
    trainer.train()

    print(f"💾 Guardando modelo entrenado en {OUTPUT_DIR}")
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

if __name__ == "__main__":
    main()
