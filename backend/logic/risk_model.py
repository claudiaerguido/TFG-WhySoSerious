import json
import os
import pandas as pd
from typing import Dict

# ── Etiquetas y Configuración ──────────────────────────────────────────────

# Dimensiones emocionales que el modelo NLP clasifica en cada mensaje
TARGET_LABELS = [
    "ESTRES_ANSIEDAD",
    "ENFADO_IRRITACION",
    "SOBRECARGA_URGENCIA",
    "CANSANCIO_FATIGA",
    "NEUTRO",
]

# Mapeo de etiquetas NLP a columnas de la base de datos (Supabase)
DB_COLS = {
    "ESTRES_ANSIEDAD":    "estres_ansiedad",
    "ENFADO_IRRITACION":  "enfado_irritacion",
    "SOBRECARGA_URGENCIA":"sobrecarga_urgencia",
    "CANSANCIO_FATIGA":   "cansancio_fatiga",
    "NEUTRO":             "neutro",
}

# Subconjunto de etiquetas operativas que alimentan el observatorio de riesgo
NEGATIVE_LABELS = [
    "ESTRES_ANSIEDAD",
    "ENFADO_IRRITACION",
    "SOBRECARGA_URGENCIA",
    "CANSANCIO_FATIGA",
]

# Umbrales para la categorización del riesgo en el Dashboard (escala 0-100)
RISK_THRESHOLDS = {"Rojo": 35, "Amarillo": 20}

# ── Metodología de Cálculo de Riesgo ───────────────────────────────────────

def _risk_level(pct: float) -> str:
    """Categoriza el riesgo según los umbrales de semáforo. Espera valores en escala 0-100."""
    if pct >= RISK_THRESHOLDS["Rojo"]: return "Rojo"
    if pct >= RISK_THRESHOLDS["Amarillo"]: return "Amarillo"
    return "Verde"

def _safe_corr(a: pd.Series, b: pd.Series) -> float:
    """
    Calcula la correlación de Pearson entre dos series de datos.
    Retorna 0.0 si alguna serie no tiene varianza para evitar divisiones por cero.
    """
    if a.std() == 0 or b.std() == 0: return 0.0
    c = a.corr(b, method="pearson")
    return float(0.0 if pd.isna(c) else c)

def _normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """Establece pesos unitarios para que la métrica final se mantenga en escala [0, 1]."""
    denom = sum(abs(w) for w in weights.values())
    if denom == 0: return {k: 0.0 for k in weights}
    return {k: v / denom for k, v in weights.items()}

# Umbrales de decisión calibrados para cada etiqueta (ver thresholds.json)
THRESHOLDS_PATH = os.path.join(os.path.dirname(__file__), "../thresholds.json")

def _load_calibrated_thresholds() -> Dict[str, float]:
    """Carga los umbrales de decisión del archivo de configuración."""
    try:
        if os.path.exists(THRESHOLDS_PATH):
            with open(THRESHOLDS_PATH, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error cargando umbrales en risk_model: {e}")
    
    # Fallback: Umbral neutro conservador
    return {l: 0.35 for l in TARGET_LABELS}

def compute_pearson_msg_risk(df: pd.DataFrame) -> pd.Series:
    """
    Calcula el riesgo individual por mensaje (msg_risk) ponderando etiquetas negativas.
    
    Metodología (Algoritmo Whysoserious):
      1. Calibración: Se filtran las intensidades por debajo de los umbrales definidos.
      2. risk_base: Se identifica la intensidad máxima de cualquier emoción negativa por mensaje.
      3. Perfil de Relevancia: Se calcula la correlación de Pearson entre cada etiqueta negativa 
         y la serie 'risk_base'. Esto determina qué emoción es más influyente en el contexto actual.
      4. Ponderación Dinámica: Solo se consideran correlaciones positivas para asignar pesos.
      5. msg_risk: Suma ponderada de las etiquetas negativas normalizada al rango [0, 1].
    """
    if df.empty: return pd.Series(dtype=float)

    neg_cols = [DB_COLS[l] for l in NEGATIVE_LABELS if DB_COLS[l] in df.columns]
    df = df.copy()

    # Aplicar calibración: si la probabilidad no supera el umbral del modelo, no cuenta para el riesgo.
    thresholds = _load_calibrated_thresholds()
    for label in NEGATIVE_LABELS:
        col = DB_COLS[label]
        if col in df.columns:
            threshold = thresholds.get(label, 0.50)
            df[col] = df[col].apply(lambda x: x if x >= threshold else 0.0)

    # El risk_base representa la 'peor' intensidad detectada (tras calibración operativa)
    df["risk_base"] = df[neg_cols].max(axis=1)

    # Cálculo de pesos dinámicos (Pearson) centrado solo en señales operativas
    weights = {}
    for label in NEGATIVE_LABELS:
        col = DB_COLS[label]
        if col in df.columns:
            c = _safe_corr(df[col], df["risk_base"])
            weights[label] = max(c, 0.0)
        else:
            weights[label] = 0.0

    total_w = sum(weights.values())
    if total_w == 0:
        # Fallback: Riesgo conservador basado en el máximo tras calibración
        return df["risk_base"]

    # Normalización de pesos y cálculo de suma ponderada
    weights = _normalize_weights(weights)
    msg_risk = sum(
        weights[label] * df[DB_COLS[label]]
        for label in NEGATIVE_LABELS
        if DB_COLS[label] in df.columns
    )
    return msg_risk.clip(lower=0.0, upper=1.0)
