import os
import torch
import numpy as np
from datasets import load_dataset, Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments, DataCollatorWithPadding

# 1. Configuración Básica
MODEL_NAME = "bert-base-multilingual-uncased"
OUTPUT_DIR = "./models/final_xed"
# Mis 7 etiquetas objetivo
TARGET_LABELS = ["TRISTEZA", "ESTRES_ANSIEDAD", "ENFADO_IRRITACION", "SOBRECARGA_URGENCIA", "CANSANCIO_FATIGA", "POSITIVO_ALIVIO", "NEUTRO"]

def map_labels_xed(xed_labels):
    """
    Convierte etiquetas XED a mi formato (One-Hot de 7 posiciones).
    Lógica de Mapeo (User Recommended):
    - 6 (Sadness) -> TRISTEZA [0]
    - 4 (Fear)    -> ESTRES [1]
    - 1/3 (Anger/Disgust) -> ENFADO [2]
    - 5/8 (Joy/Trust) -> POSITIVO [5]
    - 0 (Neutral) -> NEUTRO [6]
    """
    vec = [0.0] * len(TARGET_LABELS)
    has_emotion = False
    
    # Check simple integers or lists
    if isinstance(xed_labels, int): 
        xed_labels = [xed_labels]
    
    # Mapeo Emocional
    if 6 in xed_labels: vec[0] = 1.0; has_emotion = True # Tristeza
    if 4 in xed_labels: vec[1] = 1.0; has_emotion = True # Estres
    if 1 in xed_labels or 3 in xed_labels: vec[2] = 1.0; has_emotion = True # Enfado
    if 5 in xed_labels or 8 in xed_labels: vec[5] = 1.0; has_emotion = True # Positivo
        
    # Lógica Neutro Exclusivo
    if has_emotion:
        pass # Si hay emoción, ignoramos neutro mixed
    elif 0 in xed_labels:
        vec[6] = 1.0 # Solo neutro
    else:
        return None # Solo tiene etiquetas descartadas (2, 7)
        
    return vec

class CustomCollator(DataCollatorWithPadding):
    def __call__(self, features):
        batch = super().__call__(features)
        batch["labels"] = batch["labels"].float()
        return batch

def main():
    print("--- Entrenando Modelo Fase A (XED Real + Neutros) ---")
    
    # 1. Cargar Datos Crudos (sin procesar)
    # Usamos trust_remote_code=True porque el script de XED lo requiere
    print("Cargando Emociones...")
    d_emo = load_dataset("Helsinki-NLP/xed_en_fi", "en_annotated", split="train", trust_remote_code=True)
    
    print("Cargando Neutros...")
    d_neu = load_dataset("Helsinki-NLP/xed_en_fi", "en_neutral", split="train", trust_remote_code=True)

    # 2. Mezclar y Procesar manualmente (Lista Python simple)
    # Evitamos errores de esquemas de 'datasets' haciendo esto a mano.
    final_data = []

    print("Procesando emociones...")
    for item in d_emo:
        # item es {'sentence': str, 'labels': list[int]}
        vec = map_labels_xed(item['labels'])
        if vec:
            final_data.append({"text": item['sentence'], "labels": vec})
            
    print("Procesando neutros (Sampleado)...")
    # Tomamos solo 5000 neutros para no desbalancear demasiado
    count_neu = 0
    for item in d_neu:
        if count_neu >= 5000: break
        
        vec = map_labels_xed(item['labels']) # Debería ser [0., 0., ..., 1.]
        if vec:
            final_data.append({"text": item['sentence'], "labels": vec})
            count_neu += 1

    print(f"Dataset Final creado: {len(final_data)} ejemplos.")
    
    # Convertir a Dataset de HF limpio
    full_dataset = Dataset.from_list(final_data)
    full_dataset = full_dataset.shuffle(seed=42)

    # 3. Tokenización
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    
    def tokenize_fn(examples):
        return tokenizer(examples["text"], truncation=True, padding=False, max_length=128)
    
    print("Tokenizando...")
    tokenized_ds = full_dataset.map(tokenize_fn, batched=True)
    
    # Split Train/Val
    split_ds = tokenized_ds.train_test_split(test_size=0.1)
    
    # 4. Modelo y Entreno
    print("Preparando Trainer...")
    id2label = {i: l for i, l in enumerate(TARGET_LABELS)}
    label2id = {l: i for i, l in enumerate(TARGET_LABELS)}
    
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=len(TARGET_LABELS),
        problem_type="multi_label_classification",
        id2label=id2label,
        label2id=label2id
    )
    
    args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        eval_strategy="epoch",
        save_strategy="no",
        learning_rate=2e-5,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        num_train_epochs=1, 
        weight_decay=0.01,
        logging_steps=100,
        push_to_hub=False,
    )
    
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=split_ds["train"],
        eval_dataset=split_ds["test"],
        tokenizer=tokenizer,
        data_collator=CustomCollator(tokenizer=tokenizer),
    )
    
    trainer.train()
    
    print(f"Guardando modelo ok en {OUTPUT_DIR}")
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

if __name__ == "__main__":
    main()
