import pandas as pd
from sklearn.model_selection import train_test_split

# ==========================================
# CONFIGURACIÓN
# ==========================================

# Ruta del archivo CSV fuente con datos etiquetados manualmente
SOURCE_CSV = "../data/teams_val_dataset.csv" 

# Rutas de salida para los conjuntos de entrenamiento y validación
OUTPUT_TRAIN = "../data/teams_train_manual.csv"
OUTPUT_VAL = "../data/teams_val_manual.csv"

def main():
    print("--- Iniciando División de Datos (Data Splitting) ---")

    # 1. Carga del Dataset
    try:
        df = pd.read_csv(SOURCE_CSV)
        print(f"✅ Dataset cargado: {len(df)} registros encontrados.")
    except FileNotFoundError:
        print(f"❌ Error: No se encuentra el archivo {SOURCE_CSV}")
        return

    # 2. División Estratificada (Train/Test Split)
    # Separamos el 80% para entrenamiento y 20% para validación.
    # random_state=42 asegura reproducibilidad (que la división sea siempre idéntica).
    # shuffle=True garantiza que los datos se mezclen aleatoriamente antes de dividir.
    train_df, val_df = train_test_split(
        df, 
        test_size=0.2, 
        random_state=42, 
        shuffle=True
    )

    print(f"📊 División completada:")
    print(f"   - Entrenamiento (80%): {len(train_df)} registros")
    print(f"   - Validación (20%): {len(val_df)} registros")

    # 3. Persistencia de Datos
    train_df.to_csv(OUTPUT_TRAIN, index=False)
    val_df.to_csv(OUTPUT_VAL, index=False)
    
    print(f"💾 Archivos generados:\n   -> {OUTPUT_TRAIN}\n   -> {OUTPUT_VAL}")

if __name__ == "__main__":
    main()
