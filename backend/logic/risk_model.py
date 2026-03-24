import pandas as pd
from typing import Dict, List

# ── Etiquetas y Configuración ──────────────────────────────────────────────

# Listado completo de dimensiones emocionales analizadas por el modelo NLP
TARGET_LABELS = [
    "ESTRES_ANSIEDAD",
    "ENFADO_IRRITACION",
    "SOBRECARGA_URGENCIA",
    "CANSANCIO_FATIGA",
    "POSITIVO_ALIVIO",
    "NEUTRO",
]

# Mapeo de etiquetas NLP a columnas de la base de datos (Supabase)
DB_COLS = {
    "ESTRES_ANSIEDAD":    "estres_ansiedad",
    "ENFADO_IRRITACION":  "enfado_irritacion",
    "SOBRECARGA_URGENCIA":"sobrecarga_urgencia",
    "CANSANCIO_FATIGA":   "cansancio_fatiga",
    "POSITIVO_ALIVIO":    "positivo_alivio",
    "NEUTRO":             "neutro",
}

# Subconjunto de etiquetas que contribuyen negativamente al clima laboral
NEGATIVE_LABELS = [
    "ESTRES_ANSIEDAD",
    "ENFADO_IRRITACION",
    "SOBRECARGA_URGENCIA",
    "CANSANCIO_FATIGA",
]

# Umbrales para la categorización del riesgo en el Dashboard (%)
RISK_THRESHOLDS = {"Rojo": 35, "Amarillo": 20}

# ── Metodología de Cálculo de Riesgo ───────────────────────────────────────

def _risk_level(pct: float) -> str:
    """Categoriza el porcentaje de riesgo según los umbrales de semáforo."""
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

def compute_pearson_msg_risk(df: pd.DataFrame) -> pd.Series:
    """
    Calcula el riesgo individual por mensaje (msg_risk) ponderando etiquetas negativas.
    
    Metodología (Algoritmo Whysoserious):
      1. risk_base: Se identifica la intensidad máxima de cualquier emoción negativa por mensaje.
      2. Perfil de Relevancia: Se calcula la correlación de Pearson entre cada etiqueta negativa 
         y la serie 'risk_base'. Esto determina qué emoción es más influyente en el contexto actual.
      3. Ponderación Dinámica: Solo se consideran correlaciones positivas para asignar pesos.
      4. msg_risk: Suma ponderada de las etiquetas negativas normalizada al rango [0, 1].
    
      Seguridad (Fallback): Si no hay varianza suficiente para la correlación, se utiliza 
      la suma de las intensidades de las emociones negativas truncada a 1.0.
    """
    if df.empty: return pd.Series(dtype=float)

    neg_cols = [DB_COLS[l] for l in NEGATIVE_LABELS if DB_COLS[l] in df.columns]
    df = df.copy()
    
    # El risk_base representa la 'peor' emoción detectada en cada mensaje
    df["risk_base"] = df[neg_cols].max(axis=1)

    # Cálculo de pesos dinámicos según el contexto de datos (correlación)
    weights = {}
    for label in NEGATIVE_LABELS:
        col = DB_COLS[label]
        if col in df.columns:
            # Determinamos cuánto 'explica' cada etiqueta el riesgo base detectado
            c = _safe_corr(df[col], df["risk_base"])
            weights[label] = max(c, 0.0)
        else:
            weights[label] = 0.0

    total_w = sum(weights.values())
    if total_w == 0:
        # Si no hay varianza suficiente, sumamos intensidades (enfoque conservador)
        return df[neg_cols].sum(axis=1).clip(upper=1.0)

    # Normalización de pesos y cálculo de suma ponderada
    weights = _normalize_weights(weights)
    msg_risk = sum(
        weights[label] * df[DB_COLS[label]]
        for label in NEGATIVE_LABELS
        if DB_COLS[label] in df.columns
    )
    return msg_risk.clip(lower=0.0, upper=1.0)
