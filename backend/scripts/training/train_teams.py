import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pandas as pd
import numpy as np

from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    DataCollatorWithPadding,
    Trainer,
)

from sklearn.metrics import f1_score

# --- Configuración del entrenamiento ---

BASE_MODEL_PATH = "nlptown/bert-base-multilingual-uncased-sentiment"
OUTPUT_DIR = "./models/final_teams"

TRAIN_CSV = "../../data/teams_train_manual.csv"
VAL_CSV = "../../data/teams_val_manual.csv"

TARGET_LABELS = [
    "ESTRES_ANSIEDAD",
    "ENFADO_IRRITACION",
    "SOBRECARGA_URGENCIA",
    "CANSANCIO_FATIGA",
    "NEUTRO",
]

def df_to_dataset(df: pd.DataFrame) -> Dataset:
    """Convierte un DataFrame con columnas TARGET_LABELS en un HF Dataset."""
    data = []
    for _, row in df.iterrows():
        labels_vec = [float(row[l]) for l in TARGET_LABELS]
        data.append({"text": row["text"], "labels": labels_vec})
    return Dataset.from_list(data)



def main():
    print("--- Iniciando Fine-tuning del Modelo ---")

    # --- Carga de datos ---
    try:
        df_train = pd.read_csv(TRAIN_CSV)
        df_val = pd.read_csv(VAL_CSV)
        print(f"Datos cargados. Train: {len(df_train)}, Val: {len(df_val)}")
    except Exception as e:
        print(f"Error cargando datasets: {e}")
        return

    ds_train = df_to_dataset(df_train)
    ds_val = df_to_dataset(df_val)

    # --- Tokenizer y modelo ---
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_PATH)

    # Tokenización SIN padding fijo: el padding lo hará el data_collator dinámicamente
    def tokenize_function(examples):
        return tokenizer(examples["text"], truncation=True, max_length=128)

    encoded_train = ds_train.map(tokenize_function, batched=True).remove_columns(["text"])
    encoded_val = ds_val.map(tokenize_function, batched=True).remove_columns(["text"])

    model = AutoModelForSequenceClassification.from_pretrained(
        BASE_MODEL_PATH,
        num_labels=len(TARGET_LABELS),
        ignore_mismatched_sizes=True,
        problem_type="multi_label_classification",
        id2label={i: l for i, l in enumerate(TARGET_LABELS)},
        label2id={l: i for i, l in enumerate(TARGET_LABELS)},
    )

    # --- Hiperparámetros ---
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=15,
        learning_rate=5e-5,
        per_device_train_batch_size=4,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=1,
        load_best_model_at_end=True,
        metric_for_best_model="f1_micro",
        # opcional: logging
        logging_steps=10,
    )

    # Padding dinámico (más eficiente que max_length fijo)
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        probs = 1 / (1 + np.exp(-logits))      # sigmoid
        predictions = probs > 0.5             # umbral
        score = f1_score(labels, predictions, average="micro")
        return {"f1_micro": score}

    # --- Entrenamiento ---
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=encoded_train,
        eval_dataset=encoded_val,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    print("Ejecutando entrenamiento...")
    trainer.train()

    print(f"Guardando modelo entrenado en {OUTPUT_DIR}")
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)


if __name__ == "__main__":
    main()
