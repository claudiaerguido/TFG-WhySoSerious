import pandas as pd
from sklearn.model_selection import train_test_split
import os

# Rutas relativas desde la raíz del proyecto (donde se ejecuta el script)
AUG = "data/teams_es_augmented_500.csv"
TRAIN_OUT = "data/teams_train.csv"
VAL_OUT = "data/teams_val.csv"

def main():
    if not os.path.exists(AUG):
        # Fallback si estamos corriéndolo desde dentro de scripts/ o algo así,
        # pero asumimos ejecución desde root.
        print(f"Error: No se encuentra {AUG}")
        return

    df = pd.read_csv(AUG)
    print(f"Cargado dataset aumentado: {len(df)} ejemplos")

    # Baraja fija para reproducibilidad
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    # Split 90/10 
    train_df, val_df = train_test_split(df, test_size=0.10, random_state=42)

    train_df.to_csv(TRAIN_OUT, index=False)
    val_df.to_csv(VAL_OUT, index=False)

    print("Splits creados:")
    print(f"  Train: {len(train_df)} -> {TRAIN_OUT}")
    print(f"  Val:   {len(val_df)} -> {VAL_OUT}")

if __name__ == "__main__":
    main()
