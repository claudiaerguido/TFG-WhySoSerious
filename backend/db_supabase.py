"""
db_supabase.py — Capa de datos principal (sistema de workspaces).

Cálculo de riesgo: Correlación de Pearson al nivel de mensaje.
  risk_base  = max(emociones negativas) por mensaje   → "verdad de campo"
  peso_label = corr(label, risk_base) solo si > 0     → aprendido de los datos
  msg_risk   = suma ponderada de labels por mensaje    → [-0,1]
  user_risk  = media(msg_risk) del usuario
  team_risk  = media(user_risk) de los miembros con datos
"""

import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

load_dotenv()

# ── Constantes del modelo NLP ────────────────────────────────────────────────

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

# Labels que se consideran señal de riesgo (negativas)
NEGATIVE_LABELS = [
    "ESTRES_ANSIEDAD",
    "ENFADO_IRRITACION",
    "SOBRECARGA_URGENCIA",
    "CANSANCIO_FATIGA",
]

# Umbrales de riesgo (%)
RISK_THRESHOLDS = {"Rojo": 35, "Amarillo": 20}


# ── Helpers internos ─────────────────────────────────────────────────────────

def get_supabase_client() -> Optional[Client]:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("❌ Faltan credenciales de Supabase en .env")
        return None
    return create_client(url, key)


def _risk_level(pct: float) -> str:
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


def _fetch_workspace_emails(supabase: Client, workspace_id: int) -> List[str]:
    """Emails de los miembros de un workspace."""
    res = (
        supabase.table("workspace_members")
        .select("user_email")
        .eq("workspace_id", workspace_id)
        .execute()
    )
    return [r["user_email"] for r in (res.data or [])]


def _fetch_team_metrics(
    supabase: Client,
    emails: List[str],
    days: int,
    workspace_id: int = None,
) -> pd.DataFrame:
    """
    Devuelve el DataFrame de métricas de riesgo filtrado por ventana temporal
    y, opcionalmente, por workspace_id para evitar contaminación cruzada.
    """
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    cols = ["user_email", "message_timestamp"] + [DB_COLS[l] for l in TARGET_LABELS]
    q = (
        supabase.table("risk_metrics")
        .select(",".join(cols))
        .in_("user_email", emails)
        .gte("message_timestamp", since)
    )
    if workspace_id is not None:
        q = q.eq("workspace_id", workspace_id)
    return pd.DataFrame(q.execute().data or [])


def _pearson_msg_risk(df: pd.DataFrame) -> pd.Series:
    """
    Calcula msg_risk por fila usando correlación de Pearson SOLO sobre NEGATIVE_LABELS.

    POSITIVO_ALIVIO y NEUTRO quedan excluidos del cálculo de pesos Y del scoring.
    Con datasets pequeños pueden correlacionar por azar con risk_base y sumar riesgo
    — exactamente lo contrario de su significado semántico.

    Algoritmo:
      1. risk_base = max(negativas) por mensaje  (la "verdad de campo" del mensaje)
      2. peso = corr(label_negativa, risk_base), solo si > 0
      3. msg_risk = suma(peso × label_negativa) normalizado, clipado [0, 1]
    Fallback si no hay varianza: suma directa de negativas.
    """
    neg_cols = [DB_COLS[l] for l in NEGATIVE_LABELS if DB_COLS[l] in df.columns]

    df = df.copy()
    df["risk_base"] = df[neg_cols].max(axis=1)

    # Pesos SOLO de labels negativas (excluye POSITIVO y NEUTRO)
    weights = {}
    for label in NEGATIVE_LABELS:
        col = DB_COLS[label]
        if col in df.columns:
            c = _safe_corr(df[col], df["risk_base"])
            weights[label] = max(c, 0.0)
        else:
            weights[label] = 0.0

    print(f"  WEIGHTS_CORR: { {k: round(v,4) for k,v in weights.items()} }")

    total_w = sum(weights.values())
    if total_w == 0:
        # Fallback: suma directa de negativas (sin varianza en los datos)
        return df[neg_cols].sum(axis=1).clip(upper=1.0)

    weights = _normalize_weights(weights)
    # msg_risk = suma ponderada SOLO de labels negativas
    msg_risk = sum(
        weights[label] * df[DB_COLS[label]]
        for label in NEGATIVE_LABELS
        if DB_COLS[label] in df.columns
    )
    return msg_risk.clip(lower=0.0, upper=1.0)


# ── Persistencia de métricas ─────────────────────────────────────────────────

def save_risk_metrics(
    user_email: str,
    timestamp: str,
    scores: Dict[str, Any],
    message_id: str,
    workspace_id: int = None,
) -> None:
    """
    Guarda las métricas de un mensaje en Supabase.
    workspace_id asegura que cada mensaje esté vinculado al equipo correcto,
    evitando contaminación cruzada entre workspaces.
    """
    supabase = get_supabase_client()
    if not supabase:
        return

    data: Dict[str, Any] = {
        "user_email": user_email,
        "message_timestamp": timestamp,
        "message_id": message_id,
    }
    if workspace_id is not None:
        data["workspace_id"] = workspace_id

    for label in TARGET_LABELS:
        data[DB_COLS[label]] = float(scores.get(label, 0) or 0)

    try:
        supabase.table("risk_metrics").upsert(data, on_conflict="message_id").execute()
    except Exception as e:
        if "duplicate" not in str(e).lower() and "unique" not in str(e).lower():
            print(f"⚠️ Error guardando en Supabase: {e}")


# ── Sistema de usuarios y roles ──────────────────────────────────────────────

def ensure_org_user(email: str, display_name: str) -> None:
    """Crea la fila en org_users si no existe (role='employee' por defecto)."""
    supabase = get_supabase_client()
    if not supabase or not email:
        return
    try:
        supabase.table("org_users").upsert(
            {"user_email": email, "display_name": display_name, "role": "employee"},
            on_conflict="user_email",
            ignore_duplicates=True,
        ).execute()
    except Exception as e:
        print(f"⚠️ ensure_org_user: {e}")


def get_user_role(email: str) -> str:
    """Devuelve el role del usuario ('admin'|'manager'|'employee')."""
    supabase = get_supabase_client()
    if not supabase or not email:
        return "employee"
    try:
        res = (
            supabase.table("org_users")
            .select("role")
            .eq("user_email", email)
            .maybe_single()
            .execute()
        )
        return (res.data or {}).get("role", "employee")
    except Exception as e:
        print(f"⚠️ get_user_role: {e}")
        return "employee"


def get_workspaces_for_user(email: str, role: str) -> List[Dict[str, Any]]:
    """
    Visibilidad según rol:
    - admin / manager → todos los workspaces de la organización
    - employee        → solo los workspaces donde es owner_email
    """
    supabase = get_supabase_client()
    if not supabase:
        return []
    try:
        if role in ["admin", "manager"]:
            res = supabase.table("workspaces").select("id,name,type,owner_email").execute()
            return res.data or []
        res = (
            supabase.table("workspaces")
            .select("id,name,type,owner_email")
            .eq("owner_email", email)
            .execute()
        )
        return res.data or []
    except Exception as e:
        print(f"⚠️ get_workspaces_for_user: {e}")
        return []


# ── Riesgo del workspace ──────────────────────────────────────────────────────

def get_workspace_risk_metrics(workspace_id: int, days: int = 7) -> Dict[str, Any]:
    """
    Indicador de riesgo del workspace mediante correlación de Pearson.

    Algoritmo:
      1. risk_base por mensaje = max(emociones negativas)
      2. peso_label = corr(label, risk_base), solo si positiva
      3. msg_risk = suma ponderada de labels (normalizada)
      4. user_risk = media(msg_risk) del usuario
      5. team_risk = media(user_risk) de los miembros con datos
    """
    supabase = get_supabase_client()
    if not supabase:
        return {"status": "error", "error": "Faltan credenciales de Supabase"}

    emails = _fetch_workspace_emails(supabase, workspace_id)
    if not emails:
        return {
            "status": "ok", "risk_score_percentage": 0.0,
            "risk_level": "Verde", "sample_size": 0,
            "message": "Workspace sin miembros", "weights_used": {},
        }

    df = _fetch_team_metrics(supabase, emails, days, workspace_id=workspace_id)
    if df.empty:
        return {
            "status": "ok", "risk_score_percentage": 0.0,
            "risk_level": "Verde", "sample_size": 0,
            "message": "Sin datos en el período", "weights_used": {},
        }

    df["msg_risk"] = _pearson_msg_risk(df)

    per_user_risk = df.groupby("user_email")["msg_risk"].mean()
    risk_pct = float(per_user_risk.mean()) * 100.0
    risk_level = _risk_level(risk_pct)

    # Pesos informativos para el frontend
    label_cols_db = [DB_COLS[l] for l in TARGET_LABELS if DB_COLS[l] in df.columns]
    per_user = df.groupby("user_email")[label_cols_db].mean()
    weights_out = {
        label: round(float(per_user[DB_COLS[label]].mean()), 4)
        for label in TARGET_LABELS if DB_COLS[label] in per_user.columns
    }

    return {
        "status": "ok",
        "workspace_id": workspace_id,
        "days": days,
        "risk_score_percentage": round(risk_pct, 3),
        "risk_level": risk_level,
        "sample_size": int(per_user_risk.shape[0]),
        "weights_used": weights_out,
    }


def get_workspace_risk_trend(workspace_id: int, days: int = 30) -> Dict[str, Any]:
    """Serie temporal de riesgo del workspace agrupada por día."""
    supabase = get_supabase_client()
    if not supabase:
        return {"trend": [], "workspace_id": workspace_id}

    emails = _fetch_workspace_emails(supabase, workspace_id)
    if not emails:
        return {"trend": [], "workspace_id": workspace_id, "message": "Sin miembros"}

    df = _fetch_team_metrics(supabase, emails, days, workspace_id=workspace_id)
    if df.empty:
        return {"trend": [], "workspace_id": workspace_id, "message": "Sin datos en el período"}

    df["msg_risk"] = _pearson_msg_risk(df)
    df["date"] = pd.to_datetime(df["message_timestamp"]).dt.date

    trend = (
        df.groupby("date")["msg_risk"]
        .mean()
        .reset_index()
        .rename(columns={"msg_risk": "risk_score_percentage"})
    )
    trend["risk_score_percentage"] = (trend["risk_score_percentage"] * 100).round(2)
    trend["date"] = trend["date"].astype(str)

    return {"trend": trend.to_dict(orient="records"), "workspace_id": workspace_id}


def get_workspace_members(workspace_id: int) -> List[Dict[str, Any]]:
    """Lista miembros del workspace con alias enmascarado."""
    supabase = get_supabase_client()
    if not supabase:
        return []
    try:
        res = (
            supabase.table("workspace_members")
            .select("user_email")
            .eq("workspace_id", workspace_id)
            .execute()
        )
        return [
            {"alias": (r["user_email"] or "").split("@")[0] or f"miembro_{i}", "included": True}
            for i, r in enumerate(res.data or [], start=1)
        ]
    except Exception as e:
        print(f"⚠️ get_workspace_members: {e}")
        return []


def get_workspace_member_risks(workspace_id: int, days: int = 7) -> Dict[str, Any]:
    """
    Riesgo individual de cada miembro del workspace.
    Usa la misma correlación de Pearson que get_workspace_risk_metrics
    para garantizar coherencia entre el score global y los individuales.
    Los emails se muestran solo como alias (parte antes del @).
    """
    supabase = get_supabase_client()
    if not supabase:
        return {"members": [], "workspace_id": workspace_id}

    emails = _fetch_workspace_emails(supabase, workspace_id)
    if not emails:
        return {"members": [], "workspace_id": workspace_id}

    df = _fetch_team_metrics(supabase, emails, days, workspace_id=workspace_id)
    if df.empty:
        return {
            "members": [
                {"alias": e.split("@")[0], "risk_score_percentage": None,
                 "risk_level": None, "message_count": 0}
                for e in emails
            ],
            "workspace_id": workspace_id,
        }

    df["msg_risk"] = _pearson_msg_risk(df)
    per_user_risk = df.groupby("user_email")["msg_risk"].mean()
    msg_count = df.groupby("user_email").size().rename("msg_count")

    members = []
    for email in emails:
        alias = email.split("@")[0]
        if email in per_user_risk.index:
            pct = round(float(per_user_risk.loc[email]) * 100, 1)
            members.append({
                "alias": alias,
                "risk_score_percentage": pct,
                "risk_level": _risk_level(pct),
                "message_count": int(msg_count.get(email, 0)),
            })
        else:
            members.append({
                "alias": alias,
                "risk_score_percentage": None,
                "risk_level": None,
                "message_count": 0,
            })

    members.sort(key=lambda m: (m["risk_score_percentage"] is None, -(m["risk_score_percentage"] or 0)))
    return {"members": members, "workspace_id": workspace_id, "days": days}