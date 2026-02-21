import os
import torch
import pandas as pd
import numpy as np

from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    DataCollatorWithPadding,
)

from sklearn.metrics import f1_score
from torch.utils.data import WeightedRandomSampler

# ==========================================
# 1. CONFIGURACIÓN DEL ENTRENAMIENTO
# ==========================================

BASE_MODEL_PATH = "nlptown/bert-base-multilingual-uncased-sentiment"
OUTPUT_DIR = "./models/final_teams"

TRAIN_CSV = "../../data/teams_train_manual.csv"
VAL_CSV = "../../data/teams_val_manual.csv"

TARGET_LABELS = [
    "TRISTEZA",
    "ESTRES_ANSIEDAD",
    "ENFADO_IRRITACION",
    "SOBRECARGA_URGENCIA",
    "CANSANCIO_FATIGA",
    "POSITIVO_ALIVIO",
    "NEUTRO",
]

# Índices de clases “minoría” para darles más importancia en sampling
IDX_SOBRECARGA = TARGET_LABELS.index("SOBRECARGA_URGENCIA")
IDX_CANSANCIO = TARGET_LABELS.index("CANSANCIO_FATIGA")


def df_to_dataset(df: pd.DataFrame) -> Dataset:
    """Convierte un DataFrame con columnas TARGET_LABELS en un HF Dataset."""
    data = []
    for _, row in df.iterrows():
        labels_vec = [float(row[l]) for l in TARGET_LABELS]
        data.append({"text": row["text"], "labels": labels_vec})
    return Dataset.from_list(data)


def compute_sample_weights(ds: Dataset, boost: float = 5.0) -> np.ndarray:
    """
    Calcula un peso por ejemplo:
    - peso normal = 1.0
    - si el ejemplo tiene SOBRECARGA o CANSANCIO, le subimos el peso (boost)
    Esto evita duplicar filas (menos overfitting).
    """
    weights = np.ones(len(ds), dtype=np.float32)

    for i in range(len(ds)):
        labels_vec = ds[i]["labels"]
        if labels_vec[IDX_SOBRECARGA] == 1.0 or labels_vec[IDX_CANSANCIO] == 1.0:
            weights[i] = boost

    return weights


class WeightedTrainer(Trainer):
    """
    Trainer custom para usar WeightedRandomSampler en el DataLoader de entrenamiento.
    Así hacemos oversampling por muestreo (no por duplicación de filas).
    """
    def __init__(self, *args, train_sample_weights=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.train_sample_weights = train_sample_weights

    def get_train_dataloader(self):
        if self.train_dataset is None:
            raise ValueError("No hay train_dataset")

        if self.train_sample_weights is None:
            return super().get_train_dataloader()

        # WeightedRandomSampler elige ejemplos con probabilidad proporcional al peso
        sampler = WeightedRandomSampler(
            weights=torch.tensor(self.train_sample_weights, dtype=torch.double),
            num_samples=len(self.train_sample_weights),
            replacement=True,
        )

        return torch.utils.data.DataLoader(
            self.train_dataset,
            batch_size=self.args.per_device_train_batch_size,
            sampler=sampler,
            collate_fn=self.data_collator,
            drop_last=self.args.dataloader_drop_last,
            num_workers=self.args.dataloader_num_workers,
            pin_memory=self.args.dataloader_pin_memory,
        )


def main():
    print("--- Iniciando Fine-tuning del Modelo (Fase B: Teams) ---")

    # ==========================================
    # 2. CARGA DE DATOS
    # ==========================================
    try:
        df_train = pd.read_csv(TRAIN_CSV)
        df_val = pd.read_csv(VAL_CSV)
        print(f"Datos cargados. Train: {len(df_train)}, Val: {len(df_val)}")
    except Exception as e:
        print(f"Error cargando datasets: {e}")
        return

    ds_train = df_to_dataset(df_train)
    ds_val = df_to_dataset(df_val)

    # ==========================================
    # 3. TOKENIZER Y MODELO
    # ==========================================
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_PATH)

    # Tokenización SIN padding fijo: el padding lo hará el data_collator dinámicamente
    def tokenize_function(examples):
        return tokenizer(examples["text"], truncation=True, max_length=128)

    encoded_train = ds_train.map(tokenize_function, batched=True)
    encoded_val = ds_val.map(tokenize_function, batched=True)

    model = AutoModelForSequenceClassification.from_pretrained(
        BASE_MODEL_PATH,
        num_labels=len(TARGET_LABELS),
        ignore_mismatched_sizes=True,
        problem_type="multi_label_classification",
        id2label={i: l for i, l in enumerate(TARGET_LABELS)},
        label2id={l: i for i, l in enumerate(TARGET_LABELS)},
    )

    # ==========================================
    # 4. HIPERPARÁMETROS
    # ==========================================
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

    # Oversampling por muestreo (sin duplicación)
    sample_weights = compute_sample_weights(encoded_train, boost=5.0)

    # ==========================================
    # 5. ENTRENAMIENTO
    # ==========================================
    trainer = WeightedTrainer(
        model=model,
        args=training_args,
        train_dataset=encoded_train,
        eval_dataset=encoded_val,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
        train_sample_weights=sample_weights,
    )

    print("🚀 Ejecutando entrenamiento...")
    trainer.train()

    print(f"💾 Guardando modelo entrenado en {OUTPUT_DIR}")
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)


if __name__ == "__main__":
    main()
