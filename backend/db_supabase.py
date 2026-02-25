import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

load_dotenv()

# Labels que maneja tu modelo
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
        supabase.table("risk_metrics").insert(data).execute()
    except Exception as e:
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


def _fetch_team_emails(supabase: Client, team_id: int) -> List[str]:
    """Obtiene los emails de los miembros de un equipo."""
    ut = supabase.table("user_teams").select("user_email").eq("team_id", team_id).execute()
    return [r["user_email"] for r in (ut.data or [])]


def _fetch_team_metrics(supabase: Client, emails: List[str], days: int) -> pd.DataFrame:
    """Obtiene las métricas de riesgo de un conjunto de usuarios en una ventana temporal."""
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    cols = ["user_email", "message_timestamp"] + [DB_COLS[l] for l in TARGET_LABELS]
    rm = (
        supabase.table("risk_metrics")
        .select(",".join(cols))
        .in_("user_email", emails)
        .gte("message_timestamp", since)
        .execute()
    )
    return pd.DataFrame(rm.data or [])


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
    emails = _fetch_team_emails(supabase, team_id)
    if not emails:
        return {
            "status": "ok",
            "risk_score_percentage": 0.0,
            "risk_level": "Verde",
            "sample_size": 0,
            "message": "Equipo sin miembros",
            "weights_used": {},
        }

    # 2) Datos de la ventana temporal
    df = _fetch_team_metrics(supabase, emails, days)
    if df.empty:
        return {
            "status": "ok",
            "risk_score_percentage": 0.0,
            "risk_level": "Verde",
            "sample_size": 0,
            "message": "Sin datos en el período",
            "weights_used": {},
        }

    # 3) Agregar por usuario (cada usuario pesa igual)
    label_cols_db = [DB_COLS[l] for l in TARGET_LABELS if DB_COLS[l] in df.columns]
    per_user = df.groupby("user_email")[label_cols_db].mean()

    # 4) risk_base = media de negativas
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


def get_teams_list() -> Dict[str, Any]:
    """Obtiene la lista de equipos para el selector del frontend."""
    supabase = get_supabase_client()
    if not supabase:
        return {"teams": []}
    try:
        res = supabase.table("teams").select("id, name, manager_email").execute()
        return {"teams": res.data or []}
    except Exception as e:
        print(f"⚠️ Error obteniendo equipos: {e}")
        return {"teams": []}


def get_team_risk_trend(team_id: int, days: int = 30) -> Dict[str, Any]:
    """
    Devuelve la serie temporal de riesgo medio del equipo agrupado por día.
    Útil para la gráfica de tendencia del frontend.
    """
    supabase = get_supabase_client()
    if not supabase:
        return {"trend": [], "team_id": team_id}

    emails = _fetch_team_emails(supabase, team_id)
    if not emails:
        return {"trend": [], "team_id": team_id, "message": "Sin miembros"}

    df = _fetch_team_metrics(supabase, emails, days)
    if df.empty:
        return {"trend": [], "team_id": team_id, "message": "Sin datos en el período"}

    # Columnas de riesgo negativo (excluyendo positivo/neutro)
    neg_db_cols = [DB_COLS[l] for l in NEGATIVE_LABELS if DB_COLS[l] in df.columns]

    # Riesgo simple por fila = media de negativas - positivo_alivio
    df["row_risk"] = df[neg_db_cols].mean(axis=1)
    if DB_COLS["POSITIVO_ALIVIO"] in df.columns:
        df["row_risk"] = (df["row_risk"] - df[DB_COLS["POSITIVO_ALIVIO"]]).clip(lower=0)

    # Agrupar por día
    df["date"] = pd.to_datetime(df["message_timestamp"]).dt.date
    trend = (
        df.groupby("date")["row_risk"]
        .mean()
        .reset_index()
        .rename(columns={"row_risk": "risk_score_percentage"})
    )
    trend["risk_score_percentage"] = (trend["risk_score_percentage"] * 100).round(2)
    trend["date"] = trend["date"].astype(str)

    return {"trend": trend.to_dict(orient="records"), "team_id": team_id}


# ═══════════════════════════════════════════════════════════════
#  WORKSPACE SYSTEM — org_users · workspaces · workspace_members
# ═══════════════════════════════════════════════════════════════

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
    """Devuelve el role del usuario ('admin'|'manager'|'employee'). Default: 'employee'."""
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
    Visibilidad según rol y propiedad:
    - admin / manager → todos los workspaces (visión global de la organización)
    - employee        → SOLO los workspaces donde es owner_email
                        (Ana ve PRJ-Alpha, Carlos ve PRJ-Beta, Irene ve QA)
    """
    supabase = get_supabase_client()
    if not supabase:
        return []
    try:
        if role in ["admin", "manager"]:
            # Dirección / administrador → visión completa
            res = supabase.table("workspaces").select("id,name,type,owner_email").execute()
            return res.data or []

        # employee: solo los workspaces donde este usuario es el jefe (owner)
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



def _fetch_workspace_emails(supabase: Client, workspace_id: int) -> List[str]:
    """Obtiene los emails de los miembros de un workspace."""
    res = (
        supabase.table("workspace_members")
        .select("user_email")
        .eq("workspace_id", workspace_id)
        .execute()
    )
    return [r["user_email"] for r in (res.data or [])]


def get_workspace_risk_metrics(workspace_id: int, days: int = 7) -> Dict[str, Any]:
    """Indicador de riesgo del workspace usando el mismo algoritmo de correlación que los equipos."""
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

    df = _fetch_team_metrics(supabase, emails, days)
    if df.empty:
        return {
            "status": "ok", "risk_score_percentage": 0.0,
            "risk_level": "Verde", "sample_size": 0,
            "message": "Sin datos en el período", "weights_used": {},
        }

    label_cols_db = [DB_COLS[l] for l in TARGET_LABELS if DB_COLS[l] in df.columns]
    per_user = df.groupby("user_email")[label_cols_db].mean()

    neg_db_cols = [DB_COLS[l] for l in NEGATIVE_LABELS if DB_COLS[l] in per_user.columns]
    per_user["risk_base"] = per_user[neg_db_cols].mean(axis=1)

    weights = {}
    for label in TARGET_LABELS:
        col = DB_COLS[label]
        weights[label] = _safe_corr(per_user[col], per_user["risk_base"]) if col in per_user.columns else 0.0
    weights = _normalize_weights(weights)

    per_user["user_risk"] = 0.0
    for label in TARGET_LABELS:
        col = DB_COLS[label]
        if col in per_user.columns:
            per_user["user_risk"] += weights[label] * per_user[col]
    per_user["user_risk"] = per_user["user_risk"].clip(lower=0.0, upper=1.0)

    risk_pct = float(per_user["user_risk"].mean()) * 100.0
    risk_level = "Rojo" if risk_pct >= 66 else ("Amarillo" if risk_pct >= 33 else "Verde")

    return {
        "status": "ok",
        "workspace_id": workspace_id,
        "days": days,
        "risk_score_percentage": round(risk_pct, 3),
        "risk_level": risk_level,
        "sample_size": int(per_user.shape[0]),
        "weights_used": {k: round(v, 4) for k, v in weights.items()},
    }


def get_workspace_risk_trend(workspace_id: int, days: int = 30) -> Dict[str, Any]:
    """Serie temporal de riesgo medio del workspace agrupado por día."""
    supabase = get_supabase_client()
    if not supabase:
        return {"trend": [], "workspace_id": workspace_id}

    emails = _fetch_workspace_emails(supabase, workspace_id)
    if not emails:
        return {"trend": [], "workspace_id": workspace_id, "message": "Sin miembros"}

    df = _fetch_team_metrics(supabase, emails, days)
    if df.empty:
        return {"trend": [], "workspace_id": workspace_id, "message": "Sin datos en el período"}

    neg_db_cols = [DB_COLS[l] for l in NEGATIVE_LABELS if DB_COLS[l] in df.columns]
    df["row_risk"] = df[neg_db_cols].mean(axis=1)
    if DB_COLS["POSITIVO_ALIVIO"] in df.columns:
        df["row_risk"] = (df["row_risk"] - df[DB_COLS["POSITIVO_ALIVIO"]]).clip(lower=0)

    df["date"] = pd.to_datetime(df["message_timestamp"]).dt.date
    trend = (
        df.groupby("date")["row_risk"]
        .mean()
        .reset_index()
        .rename(columns={"row_risk": "risk_score_percentage"})
    )
    trend["risk_score_percentage"] = (trend["risk_score_percentage"] * 100).round(2)
    trend["date"] = trend["date"].astype(str)

    return {"trend": trend.to_dict(orient="records"), "workspace_id": workspace_id}


def get_workspace_members(workspace_id: int) -> List[Dict[str, Any]]:
    """
    Lista miembros del workspace con email enmascarado y estado 'incluido'.
    Sin scores individuales (privacidad).
    """
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
        members = []
        for i, r in enumerate(res.data or [], start=1):
            email = r["user_email"]
            # Enmascarar: muestra solo el alias (parte antes del @)
            alias = email.split("@")[0] if email else f"miembro_{i}"
            members.append({"alias": alias, "included": True})
        return members
    except Exception as e:
        print(f"⚠️ get_workspace_members: {e}")
        return []