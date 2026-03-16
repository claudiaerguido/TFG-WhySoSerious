import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
from supabase import Client
from logic.risk_model import DB_COLS, TARGET_LABELS

# ── Miembros ───────────────────────────────────────────────────────────────

def fetch_team_members(supabase: Client, team_id: int) -> List[Dict[str, str]]:
    """Emails y nombres reales de los miembros de un equipo (Manual Join)."""
    try:
        res_memb = supabase.table("user_teams").select("user_email").eq("team_id", team_id).execute()
        emails = [r["user_email"] for r in (res_memb.data or [])]
        if not emails: return []

        res_users = supabase.table("org_users").select("user_email, display_name").in_("user_email", emails).execute()
        user_map = {u["user_email"]: u.get("display_name") for u in (res_users.data or [])}

        return [
            {"user_email": email, "display_name": user_map.get(email)}
            for email in emails
        ]
    except Exception as e:
        print(f"⚠️ fetch_team_members error: {e}")
        return []


def fetch_project_members(supabase: Client, project_id: int) -> List[Dict[str, str]]:
    """Emails y nombres reales de los miembros de un proyecto (Manual Join)."""
    try:
        res_memb = supabase.table("project_members").select("user_email").eq("project_id", project_id).execute()
        emails = [r["user_email"] for r in (res_memb.data or [])]
        if not emails: return []

        res_users = supabase.table("org_users").select("user_email, display_name").in_("user_email", emails).execute()
        user_map = {u["user_email"]: u.get("display_name") for u in (res_users.data or [])}

        return [
            {"user_email": email, "display_name": user_map.get(email)}
            for email in emails
        ]
    except Exception as e:
        print(f"⚠️ fetch_project_members error: {e}")
        return []


# ── Métricas ───────────────────────────────────────────────────────────────

def fetch_metrics_for_users(
    supabase: Client,
    emails: List[str],
    days: int,
    project_id: int = None,
    global_mode: bool = False,
    workspace_id: int = None  # Parámetro legacy para compatibilidad con código antiguo
) -> pd.DataFrame:
    """Recupera métricas de riesgo filtradas por usuarios. Soporta IDs legacy de workspaces."""
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    cols = ["user_email", "message_timestamp"] + [DB_COLS[l] for l in TARGET_LABELS]
    
    q = (
        supabase.table("risk_metrics")
        .select(",".join(cols))
        .in_("user_email", emails)
        .gte("message_timestamp", since)
    )
    
    if not global_mode:
        if project_id is not None:
            q = q.eq("project_id", project_id)
        elif workspace_id is not None:
            q = q.eq("workspace_id", workspace_id)
        else:
            q = q.is_("project_id", "null")
            
    return pd.DataFrame(q.execute().data or [])


def save_risk_metrics(
    supabase: Client,
    user_email: str,
    timestamp: str,
    scores: Dict[str, Any],
    message_id: str,
    project_id: int = None,
) -> None:
    """Guarda las métricas de un mensaje en Supabase."""
    data: Dict[str, Any] = {
        "user_email": user_email,
        "message_timestamp": timestamp,
        "message_id": message_id,
        "project_id": project_id,
        "workspace_id": project_id  # Legacy compat
    }

    for label in TARGET_LABELS:
        data[DB_COLS[label]] = float(scores.get(label, 0) or 0)

    try:
        supabase.table("risk_metrics").upsert(data, on_conflict="message_id").execute()
    except Exception as e:
        if "duplicate" not in str(e).lower() and "unique" not in str(e).lower():
            print(f"⚠️ Error guardando message_id={message_id}: {e}")
