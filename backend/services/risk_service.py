import pandas as pd
from typing import Dict, Any, Optional, List
from db_client import get_supabase_client
from logic.risk_model import compute_pearson_msg_risk, _risk_level
from db_repository import fetch_metrics_for_users, fetch_team_members, fetch_project_members

# ── Helpers de Agregación ──────────────────────────────────────────────────

def _compute_mean_risk_from_df(df: pd.DataFrame) -> Optional[float]:
    """Calcula la media del riesgo desde un DataFrame de métricas."""
    if df.empty: return None
    msg_risks = compute_pearson_msg_risk(df)
    return float(msg_risks.mean())


def _compute_daily_trend_from_df(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Genera una serie temporal diaria desde un DataFrame de métricas."""
    if df.empty: return []
    df = df.copy()
    df["msg_risk"] = compute_pearson_msg_risk(df)
    df["date"] = pd.to_datetime(df["message_timestamp"]).dt.date
    
    trend = (
        df.groupby("date")["msg_risk"]
        .mean()
        .reset_index()
        .rename(columns={"msg_risk": "risk_score_percentage"})
    )
    trend["risk_score_percentage"] = (trend["risk_score_percentage"] * 100).round(2)
    trend["date"] = trend["date"].astype(str)
    return trend.to_dict(orient="records")


# ── Riesgo: Modelo de 4 Niveles ──────────────────────────────────────────────

def get_employee_global_risk(user_email: str, days: int = 7) -> Optional[float]:
    """Nivel 1: Riesgo Global de una PERSONA (Media de TODOS sus mensajes)."""
    supabase = get_supabase_client()
    if not supabase: return None
    df = fetch_metrics_for_users(supabase, [user_email], days, global_mode=True)
    return _compute_mean_risk_from_df(df)


def get_employee_project_risk(user_email: str, project_id: int, days: int = 7) -> Optional[float]:
    """Nivel 2: Riesgo Táctico de una PERSONA en un PROYECTO."""
    supabase = get_supabase_client()
    if not supabase: return None
    df = fetch_metrics_for_users(supabase, [user_email], days, project_id=project_id, global_mode=False)
    return _compute_mean_risk_from_df(df)


def get_team_global_risk(team_id: int, days: int = 7) -> Dict[str, Any]:
    """Nivel 3: Riesgo Global del EQUIPO."""
    supabase = get_supabase_client()
    if not supabase: return {"status": "error"}
    
    members = fetch_team_members(supabase, team_id)
    if not members: return {"status": "ok", "risk_score_percentage": 0.0, "members": []}
    
    members_risks = []
    for m in members:
        email = m["user_email"]
        risk = get_employee_global_risk(email, days)
        members_risks.append({
            "user_email": email,
            "email": email,
            "display_name": m["display_name"],
            "alias": m["display_name"] or email.split("@")[0],
            "global_risk": round(risk * 100, 2) if risk is not None else None,
            "projects": get_member_projects_breakdown(email, days)
        })
    
    valid_risks = [m["global_risk"] for m in members_risks if m["global_risk"] is not None]
    team_risk = sum(valid_risks) / len(valid_risks) if valid_risks else 0.0
    
    return {
        "status": "ok",
        "team_id": team_id,
        "team_risk": round(team_risk, 2),
        "risk_score_percentage": round(team_risk, 2),
        "risk_level": _risk_level(team_risk),
        "members": members_risks
    }


def get_project_global_risk(project_id: int, days: int = 7) -> Dict[str, Any]:
    """Nivel 4: Riesgo Táctico de un PROYECTO (Media de los riesgos en proyecto de sus miembros)."""
    supabase = get_supabase_client()
    if not supabase: return {"status": "error"}
    
    members = fetch_project_members(supabase, project_id)
    if not members: return {"status": "ok", "risk_score_percentage": 0.0, "members": []}
    
    members_risks = []
    for m in members:
        email = m["user_email"]
        risk = get_employee_project_risk(email, project_id, days)
        members_risks.append({
            "user_email": email,
            "email": email,
            "display_name": m["display_name"],
            "alias": m["display_name"] or email.split("@")[0],
            "project_risk": round(risk * 100, 2) if risk is not None else None
        })
        
    valid_risks = [m["project_risk"] for m in members_risks if m["project_risk"] is not None]
    project_risk = sum(valid_risks) / len(valid_risks) if valid_risks else 0.0
    
    return {
        "status": "ok",
        "project_id": project_id,
        "project_risk": round(project_risk, 2),
        "risk_score_percentage": round(project_risk, 2),
        "risk_level": _risk_level(project_risk),
        "members": members_risks
    }


# ── Desgloses y Tendencias ──────────────────────────────────────────────────

def get_member_projects_breakdown(user_email: str, days: int = 7) -> List[Dict[str, Any]]:
    """Desglose de riesgo por proyecto para un miembro específico."""
    supabase = get_supabase_client()
    if not supabase: return []
    res = supabase.table("project_members").select("project_id, projects(name)").eq("user_email", user_email).execute()
    projects = res.data or []
    
    breakdown = []
    for p in projects:
        p_id = p["project_id"]
        p_name = p.get("projects", {}).get("name", f"Proyecto {p_id}")
        risk = get_employee_project_risk(user_email, p_id, days)
        breakdown.append({
            "project_id": p_id,
            "project_name": p_name,
            "project_risk": round(risk * 100, 2) if risk is not None else None
        })
    return breakdown


def get_team_risk_trend(team_id: int, days: int = 30) -> Dict[str, Any]:
    """Serie temporal de riesgo del EQUIPO."""
    supabase = get_supabase_client()
    if not supabase: return {"trend": [], "team_id": team_id}
    members = fetch_team_members(supabase, team_id)
    emails = [m["user_email"] for m in members]
    if not emails: return {"trend": [], "team_id": team_id}
    df = fetch_metrics_for_users(supabase, emails, days, global_mode=True)
    return {"trend": _compute_daily_trend_from_df(df), "team_id": team_id}


def get_project_risk_trend(project_id: int, days: int = 30) -> Dict[str, Any]:
    """Serie temporal de riesgo del PROYECTO."""
    supabase = get_supabase_client()
    if not supabase: return {"trend": [], "project_id": project_id}
    members = fetch_project_members(supabase, project_id)
    emails = [m["user_email"] for m in members]
    if not emails: return {"trend": [], "project_id": project_id}
    df = fetch_metrics_for_users(supabase, emails, days, project_id=project_id, global_mode=False)
    return {"trend": _compute_daily_trend_from_df(df), "project_id": project_id}


def get_project_members_list(project_id: int) -> List[Dict[str, Any]]:
    """Lista miembros del proyecto con alias enmascarado (para UI)."""
    supabase = get_supabase_client()
    if not supabase: return []
    members = fetch_project_members(supabase, project_id)
    return [
        {"alias": m["user_email"].split("@")[0] or f"miembro_{i}", "included": True}
        for i, m in enumerate(members, start=1)
    ]


def get_all_workspaces_with_members() -> Dict[str, List[Dict[str, Any]]]:
    """Devuelve todos los equipos y proyectos con su lista de miembros."""
    supabase = get_supabase_client()
    if not supabase: return {"teams": [], "projects": []}
    try:
        res_teams = supabase.table("teams").select("id, name").execute()
        teams = res_teams.data or []
        for t in teams:
            t["members"] = [m["user_email"] for m in fetch_team_members(supabase, t["id"])]
            t["type"] = "team"
            
        res_projects = supabase.table("projects").select("id, name").execute()
        projects = res_projects.data or []
        for p in projects:
            p["members"] = [m["user_email"] for m in fetch_project_members(supabase, p["id"])]
            p["type"] = "project"
            
        return {"teams": teams, "projects": projects}
    except Exception as e:
        print(f"⚠️ get_all_workspaces_with_members error: {e}")
        return {"teams": [], "projects": []}
