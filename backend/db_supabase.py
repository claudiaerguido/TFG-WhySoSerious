import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

load_dotenv()

# Labels que maneja tu modelo (como te pidió tu profesor)
TARGET_LABELS = [
    "ESTRES_ANSIEDAD",
    "ENFADO_IRRITACION",
    "SOBRECARGA_URGENCIA",
    "CANSANCIO_FATIGA",
    "POSITIVO_ALIVIO",
    "NEUTRO",
]

# Mapeo a nombres de columnas en tu tabla risk_metrics (snake_case)
DB_COLS = {
    "ESTRES_ANSIEDAD": "estres_ansiedad",
    "ENFADO_IRRITACION": "enfado_irritacion",
    "SOBRECARGA_URGENCIA": "sobrecarga_urgencia",
    "CANSANCIO_FATIGA": "cansancio_fatiga",
    "POSITIVO_ALIVIO": "positivo_alivio",
    "NEUTRO": "neutro",
}

# Para definir "malestar base" (riesgo) usaremos las negativas:
NEGATIVE_LABELS = [
    "ESTRES_ANSIEDAD",
    "ENFADO_IRRITACION",
    "SOBRECARGA_URGENCIA",
    "CANSANCIO_FATIGA",
]


def get_supabase_client() -> Optional[Client]:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("❌ Faltan credenciales de Supabase en .env")
        return None
    return create_client(url, key)


def save_risk_metrics(user_email: str, timestamp: str, scores: Dict[str, Any], message_id: str) -> None:
    """
    Guarda métricas del mensaje en Supabase.
    Requiere que la tabla risk_metrics tenga columna message_id (idealmente UNIQUE).
    """
    supabase = get_supabase_client()
    if not supabase:
        return

    data = {
        "user_email": user_email,
        "message_timestamp": timestamp,
        "message_id": message_id,
    }

    # Guardar todas las labels en columnas
    for label in TARGET_LABELS:
        col = DB_COLS[label]
        data[col] = float(scores.get(label, 0) or 0)

    try:
        # Insert (si tienes UNIQUE message_id, los duplicados darán error;
        # si prefieres "no duplicar nunca", cambia a upsert con on_conflict)
        supabase.table("risk_metrics").insert(data).execute()
    except Exception as e:
        # Si ya existe por UNIQUE message_id, puedes ignorarlo.
        # (Depende del mensaje exacto que devuelva tu SDK)
        msg = str(e).lower()
        if "duplicate" in msg or "unique" in msg:
            return
        print(f"⚠️ Error guardando en Supabase: {e}")


def _safe_corr(a: pd.Series, b: pd.Series) -> float:
    """Correlación robusta: devuelve 0 si no hay varianza suficiente."""
    if a.std() == 0 or b.std() == 0:
        return 0.0
    c = a.corr(b, method="pearson")
    return float(0.0 if pd.isna(c) else c)


def _normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """Normaliza para que la suma de |pesos| = 1 (estabilidad)."""
    denom = sum(abs(w) for w in weights.values())
    if denom == 0:
        return {k: 0.0 for k in weights}
    return {k: (v / denom) for k, v in weights.items()}


def get_team_risk_metrics(team_id: int, days: int = 7) -> Dict[str, Any]:
    """
    Indicador de riesgo usando matriz de correlación (coeficientes derivados de correlación).
    - Lee miembros desde user_teams
    - Lee métricas desde risk_metrics en ventana temporal
    - Agrega por usuario (para que cada usuario pese igual)
    - Define risk_base = media de negativas
    - Peso de cada label = corr(label, risk_base)
    - user_risk = suma(peso * label)
    - team_risk = media(user_risk)
    """
    supabase = get_supabase_client()
    if not supabase:
        return {"status": "error", "error": "Faltan credenciales de Supabase"}

    if team_id is None:
        return {"status": "error", "error": "Se requiere team_id"}

    # 1) Miembros del equipo
    ut = supabase.table("user_teams").select("user_email").eq("team_id", team_id).execute()
    emails = [r["user_email"] for r in (ut.data or [])]
    if not emails:
        return {
            "status": "ok",
            "risk_score_percentage": 0.0,
            "risk_level": "Verde",
            "sample_size": 0,
            "message": "Equipo sin miembros",
            "weights_used": {},
        }

    # 2) Ventana temporal
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()

    cols = ["user_email"] + [DB_COLS[l] for l in TARGET_LABELS]
    rm = (
        supabase.table("risk_metrics")
        .select(",".join(cols))
        .in_("user_email", emails)
        .gte("message_timestamp", since)
        .execute()
    )
    rows = rm.data or []
    if not rows:
        return {
            "status": "ok",
            "risk_score_percentage": 0.0,
            "risk_level": "Verde",
            "sample_size": 0,
            "message": "Sin datos en el período",
            "weights_used": {},
        }

    df = pd.DataFrame(rows)

    # 3) Agregar por usuario (cada usuario pesa igual)
    # Nos quedamos solo con columnas numéricas esperadas
    label_cols_db = [DB_COLS[l] for l in TARGET_LABELS if DB_COLS[l] in df.columns]
    per_user = df.groupby("user_email")[label_cols_db].mean()

    # 4) risk_base = media de negativas (en DB columns)
    neg_db_cols = [DB_COLS[l] for l in NEGATIVE_LABELS if DB_COLS[l] in per_user.columns]
    per_user["risk_base"] = per_user[neg_db_cols].mean(axis=1)

    # 5) Pesos = correlación de cada label con risk_base (con signo)
    weights = {}
    for label in TARGET_LABELS:
        col = DB_COLS[label]
        if col not in per_user.columns:
            weights[label] = 0.0
            continue
        weights[label] = _safe_corr(per_user[col], per_user["risk_base"])

    weights = _normalize_weights(weights)

    # 6) user_risk = suma(peso * valor)
    per_user["user_risk"] = 0.0
    for label in TARGET_LABELS:
        col = DB_COLS[label]
        if col in per_user.columns:
            per_user["user_risk"] += weights[label] * per_user[col]

    # Opcional: acotar 0..1 para que sea interpretable como "riesgo"
    # (si prefieres mantenerlo libre, comenta esta línea)
    per_user["user_risk"] = per_user["user_risk"].clip(lower=0.0, upper=1.0)

    team_risk = float(per_user["user_risk"].mean())
    users_included = int(per_user.shape[0])

    # 7) semáforo
    risk_pct = team_risk * 100.0
    risk_level = "Rojo" if risk_pct >= 66 else ("Amarillo" if risk_pct >= 33 else "Verde")

    return {
        "status": "ok",
        "team_id": team_id,
        "days": days,
        "risk_score_percentage": round(risk_pct, 3),
        "risk_level": risk_level,
        "sample_size": users_included,
        "weights_used": {k: round(v, 4) for k, v in weights.items()},
    }