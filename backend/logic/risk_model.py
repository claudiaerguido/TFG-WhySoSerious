import pandas as pd
from typing import Dict, List

# ── Constantes ─────────────────────────────────────────────────────────────

TARGET_LABELS = [
    "ESTRES_ANSIEDAD",
    "ENFADO_IRRITACION",
    "SOBRECARGA_URGENCIA",
    "CANSANCIO_FATIGA",
    "POSITIVO_ALIVIO",
    "NEUTRO",
]

DB_COLS = {
    "ESTRES_ANSIEDAD":    "estres_ansiedad",
    "ENFADO_IRRITACION":  "enfado_irritacion",
    "SOBRECARGA_URGENCIA":"sobrecarga_urgencia",
    "CANSANCIO_FATIGA":   "cansancio_fatiga",
    "POSITIVO_ALIVIO":    "positivo_alivio",
    "NEUTRO":             "neutro",
}

NEGATIVE_LABELS = [
    "ESTRES_ANSIEDAD",
    "ENFADO_IRRITACION",
    "SOBRECARGA_URGENCIA",
    "CANSANCIO_FATIGA",
]

RISK_THRESHOLDS = {"Rojo": 35, "Amarillo": 20}

# ── Lógica de Cálculo ──────────────────────────────────────────────────────

def _risk_level(pct: float) -> str:
    """Devuelve el nivel de riesgo (Rojo/Amarillo/Verde) según el porcentaje."""
    if pct >= RISK_THRESHOLDS["Rojo"]:
        return "Rojo"
    if pct >= RISK_THRESHOLDS["Amarillo"]:
        return "Amarillo"
    return "Verde"


def _safe_corr(a: pd.Series, b: pd.Series) -> float:
    """Correlación de Pearson robusta: devuelve 0 si no hay varianza."""
    if a.std() == 0 or b.std() == 0:
        return 0.0
    c = a.corr(b, method="pearson")
    return float(0.0 if pd.isna(c) else c)


def _normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """Normaliza para que la suma de pesos = 1."""
    denom = sum(abs(w) for w in weights.values())
    if denom == 0:
        return {k: 0.0 for k in weights}
    return {k: v / denom for k, v in weights.items()}


def compute_pearson_msg_risk(df: pd.DataFrame) -> pd.Series:
    """
    Calcula el riesgo por mensaje (msg_risk) usando correlación de Pearson.
    
    Algoritmo:
      1. risk_base = max(negativas) por mensaje.
      2. peso = corr(label_negativa, risk_base), solo si > 0.
      3. msg_risk = suma(peso × label_negativa) normalizado.
    """
    if df.empty:
        return pd.Series(dtype=float)

    neg_cols = [DB_COLS[l] for l in NEGATIVE_LABELS if DB_COLS[l] in df.columns]
    
    df = df.copy()
    df["risk_base"] = df[neg_cols].max(axis=1)

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
        # Fallback: suma directa si no hay varianza
        return df[neg_cols].sum(axis=1).clip(upper=1.0)

    weights = _normalize_weights(weights)
    msg_risk = sum(
        weights[label] * df[DB_COLS[label]]
        for label in NEGATIVE_LABELS
        if DB_COLS[label] in df.columns
    )
    return msg_risk.clip(lower=0.0, upper=1.0)
