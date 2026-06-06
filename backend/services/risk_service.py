import pandas as pd
from typing import Dict, Any, Optional, List

from db_client import get_supabase_client
from logic.risk_model import compute_pearson_msg_risk, _risk_level
from db_repository import (
    fetch_metrics_for_users,
    fetch_team_members,
    fetch_project_members,
    fetch_user_projects,
    fetch_user_metadata,
)


# ── Helpers internos ────────────────────────────────────────────────────────

def _to_pct(value: Optional[float]) -> Optional[float]:
    """Convierte un riesgo 0..1 a porcentaje con 1 decimal."""
    if value is None:
        return None
    return round(value * 100, 1)


def _compute_mean_risk_from_df(df: pd.DataFrame) -> Optional[float]:
    """
    Calcula la media aritmética del riesgo en escala 0..1 a partir
    de las métricas de mensajes del DataFrame.
    """
    if df.empty:
        return None
    msg_risks = compute_pearson_msg_risk(df)
    return float(msg_risks.mean())


def _compute_daily_trend_from_df(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Genera una serie temporal diaria en porcentaje.
    La tendencia se calcula sobre msg_risk medio por día.
    """
    if df.empty:
        return []

    df = df.copy()
    df["msg_risk"] = compute_pearson_msg_risk(df)
    df["date"] = pd.to_datetime(df["message_timestamp"], format='ISO8601', utc=True).dt.date

    trend = (
        df.groupby("date")["msg_risk"]
        .mean()
        .reset_index()
        .rename(columns={"msg_risk": "risk_score_percentage"})
    )
    trend["risk_score_percentage"] = (trend["risk_score_percentage"] * 100).round(1)
    trend["date"] = trend["date"].astype(str)

    return trend.to_dict(orient="records")


def _visible_name(member: Dict[str, Any]) -> str:
    """Nombre visible para UI, con fallback al prefijo del email."""
    email = member["user_email"]
    return member.get("display_name") or email.split("@")[0]


def _is_operational_member(member: Dict[str, Any]) -> bool:
    """
    Indica si el miembro debe contribuir a medias y tendencias.
    Solo los perfiles 'employee' participan en agregados operativos.
    """
    return member.get("role", "employee") == "employee"


def _compute_per_user_risks(df: pd.DataFrame) -> Dict[str, Optional[float]]:
    """
    Calcula el riesgo medio (escala 0..1) por usuario a partir de un
    DataFrame con mensajes de múltiples usuarios. Evita N queries
    procesando todos los usuarios en una sola pasada de pandas.
    """
    if df.empty:
        return {}
    result: Dict[str, Optional[float]] = {}
    for email, group in df.groupby("user_email"):
        msg_risks = compute_pearson_msg_risk(group.reset_index(drop=True))
        result[email] = float(msg_risks.mean()) if not msg_risks.empty else None
    return result

# ── Modelo de 4 niveles ─────────────────────────────────────────────────────

def get_employee_global_risk(user_email: str, days: int = 7, start_date: str = None, end_date: str = None) -> Optional[float]:
    """
    Nivel 1: Riesgo global de una persona.
    Considera todos sus mensajes dentro de la ventana temporal.
    """
    supabase = get_supabase_client()
    if not supabase:
        return None

    df = fetch_metrics_for_users(
        supabase,
        [user_email],
        days,
        global_mode=True,
        start_date=start_date,
        end_date=end_date,
    )
    return _compute_mean_risk_from_df(df)


def get_employee_project_risk(
    user_email: str,
    project_id: int,
    days: int = 7,
    start_date: str = None,
    end_date: str = None
) -> Optional[float]:
    """
    Nivel 2: Riesgo táctico de una persona dentro de un proyecto.
    Considera únicamente mensajes vinculados a ese project_id.
    """
    supabase = get_supabase_client()
    if not supabase:
        return None

    df = fetch_metrics_for_users(
        supabase,
        [user_email],
        days,
        project_id=project_id,
        global_mode=False,
        start_date=start_date,
        end_date=end_date,
    )
    return _compute_mean_risk_from_df(df)


def get_team_global_risk(team_id: int, days: int = 7, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
    """
    Nivel 3: Riesgo global del equipo.
    Se calcula como la media del riesgo global de sus integrantes operativos.
    Los managers/admins pueden mostrarse en UI, pero no contribuyen a la media.
    """
    supabase = get_supabase_client()
    if not supabase:
        return {"status": "error", "message": "No se pudo conectar a Supabase"}

    members = fetch_team_members(supabase, team_id, start_date=start_date, end_date=end_date)
    if not members:
        return {
            "status": "ok",
            "team_id": team_id,
            "team_risk": 0.0,
            "risk_score_percentage": 0.0,
            "risk_level": _risk_level(0.0),
            "members": [],
        }

    members_risks: List[Dict[str, Any]] = []

    for member in members:
        email = member["user_email"]
        display_name = _visible_name(member)
        risk_01 = get_employee_global_risk(email, days, start_date, end_date)
        risk_pct = _to_pct(risk_01)

        members_risks.append({
            "user_email": email,
            "email": email,
            "display_name": display_name,
            "alias": display_name,  # compatibilidad frontend
            "role": member.get("role", "employee"),
            "global_risk": risk_pct,
            "projects": get_member_projects_breakdown(email, days, start_date, end_date),
        })

    employee_risks = [
        m["global_risk"]
        for m in members_risks
        if m["global_risk"] is not None and m.get("role") == "employee"
    ]
    team_risk = round(sum(employee_risks) / len(employee_risks), 1) if employee_risks else 0.0

    return {
        "status": "ok",
        "team_id": team_id,
        "team_risk": team_risk,
        "risk_score_percentage": team_risk,
        "risk_level": _risk_level(team_risk),  # _risk_level debe esperar porcentaje
        "members": members_risks,
    }


def get_project_tactical_risk(project_id: int, days: int = 7, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
    """
    Nivel 4: Riesgo táctico del proyecto.
    Se calcula como la media del riesgo en proyecto de sus integrantes operativos.
    """
    supabase = get_supabase_client()
    if not supabase:
        return {"status": "error", "message": "No se pudo conectar a Supabase"}

    members = fetch_project_members(supabase, project_id, start_date=start_date, end_date=end_date)
    if not members:
        return {
            "status": "ok",
            "project_id": project_id,
            "project_risk": 0.0,
            "risk_score_percentage": 0.0,
            "risk_level": _risk_level(0.0),
            "members": [],
        }

    members_risks: List[Dict[str, Any]] = []

    for member in members:
        email = member["user_email"]
        display_name = _visible_name(member)
        risk_01 = get_employee_project_risk(email, project_id, days, start_date, end_date)
        risk_pct = _to_pct(risk_01)

        members_risks.append({
            "user_email": email,
            "email": email,
            "display_name": display_name,
            "alias": display_name,  # compatibilidad frontend
            "role": member.get("role", "employee"),
            "project_risk": risk_pct,
        })

    employee_risks = [
        m["project_risk"]
        for m in members_risks
        if m["project_risk"] is not None and m.get("role") == "employee"
    ]
    project_risk = round(sum(employee_risks) / len(employee_risks), 1) if employee_risks else 0.0

    return {
        "status": "ok",
        "project_id": project_id,
        "project_risk": project_risk,
        "risk_score_percentage": project_risk,
        "risk_level": _risk_level(project_risk),  # _risk_level debe esperar porcentaje
        "members": members_risks,
    }


# ── Desgloses y tendencias ──────────────────────────────────────────────────

def get_member_projects_breakdown(user_email: str, days: int = 7, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
    """
    Devuelve el riesgo táctico por proyecto de un miembro.
    Mantiene cálculo dinámico a partir de risk_metrics.
    """
    supabase = get_supabase_client()
    if not supabase:
        return []

    # Para la gestión en el frontend, listamos únicamente los proyectos en los que participa actualmente (end_date es null)
    projects = fetch_user_projects(supabase, user_email, start_date=None, end_date=None)
    breakdown: List[Dict[str, Any]] = []

    for project in projects:
        project_id = project["project_id"]
        project_name = project.get("projects", {}).get("name", f"Proyecto {project_id}")
        risk_01 = get_employee_project_risk(user_email, project_id, days, start_date, end_date)

        breakdown.append({
            "project_id": project_id,
            "project_name": project_name,
            "project_risk": _to_pct(risk_01),
        })

    return breakdown


def get_employee_risk_trend(user_email: str, days: int = 30, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
    """
    Tendencia temporal del riesgo global de un empleado.
    """
    supabase = get_supabase_client()
    if not supabase:
        return {"trend": [], "email": user_email}

    df = fetch_metrics_for_users(supabase, [user_email], days, global_mode=True, start_date=start_date, end_date=end_date)
    return {
        "trend": _compute_daily_trend_from_df(df),
        "email": user_email,
    }


def get_employee_full_profile(user_email: str, days: int = 7, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
    """
    Consolidado de perfil de empleado: metadatos + riesgo global + desglose proyectos.
    """
    supabase = get_supabase_client()
    if not supabase:
        return {"status": "error", "message": "No se pudo conectar a Supabase"}

    metadata = fetch_user_metadata(supabase, user_email)
    risk_01 = get_employee_global_risk(user_email, days, start_date, end_date)
    risk_pct = _to_pct(risk_01)
    breakdown = get_member_projects_breakdown(user_email, days, start_date, end_date)

    display_name = metadata.get("display_name") or user_email.split("@")[0]

    return {
        "status": "ok",
        "email": user_email,
        "display_name": display_name,
        "role": metadata.get("role", "employee"),
        "global_risk": risk_pct,
        "risk_level": _risk_level(risk_pct if risk_pct is not None else 0),
        "projects": breakdown,
    }


def get_team_risk_trend(team_id: int, days: int = 30, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
    """
    Tendencia temporal del equipo.
    Solo considera integrantes operativos (role='employee').
    """
    supabase = get_supabase_client()
    if not supabase:
        return {"trend": [], "team_id": team_id}

    members = fetch_team_members(supabase, team_id, start_date=start_date, end_date=end_date)
    emails = [
        m["user_email"]
        for m in members
        if _is_operational_member(m)
    ]
    if not emails:
        return {"trend": [], "team_id": team_id}

    df = fetch_metrics_for_users(supabase, emails, days, global_mode=True, start_date=start_date, end_date=end_date)
    return {
        "trend": _compute_daily_trend_from_df(df),
        "team_id": team_id,
    }


def get_project_risk_trend(project_id: int, days: int = 30, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
    """
    Tendencia temporal del proyecto.
    Solo considera integrantes operativos (role='employee').
    """
    supabase = get_supabase_client()
    if not supabase:
        return {"trend": [], "project_id": project_id}

    members = fetch_project_members(supabase, project_id, start_date=start_date, end_date=end_date)
    emails = [
        m["user_email"]
        for m in members
        if _is_operational_member(m)
    ]
    if not emails:
        return {"trend": [], "project_id": project_id}

    df = fetch_metrics_for_users(
        supabase,
        emails,
        days,
        project_id=project_id,
        global_mode=False,
        start_date=start_date,
        end_date=end_date,
    )
    return {
        "trend": _compute_daily_trend_from_df(df),
        "project_id": project_id,
    }


def get_project_members_list(project_id: int) -> List[Dict[str, Any]]:
    """
    Lista de miembros del proyecto para UI.
    Mantiene 'alias' por compatibilidad con el frontend actual.
    """
    supabase = get_supabase_client()
    if not supabase:
        return []

    members = fetch_project_members(supabase, project_id)
    output: List[Dict[str, Any]] = []

    for member in members:
        display_name = _visible_name(member)
        output.append({
            "display_name": display_name,
            "alias": display_name,
            "included": True,
        })

    return output


def get_all_teams_and_projects_with_members() -> Dict[str, List[Dict[str, Any]]]:
    """
    Devuelve catálogo de equipos y proyectos con sus miembros.
    Se usa como apoyo para UI y para la lógica de mapeo del scheduler.
    """
    supabase = get_supabase_client()
    if not supabase:
        return {"teams": [], "projects": []}

    try:
        teams_res = supabase.table("teams").select("id, name").execute()
        projects_res = supabase.table("projects").select("id, name").execute()

        teams = teams_res.data or []
        projects = projects_res.data or []

        for team in teams:
            team["members"] = [
                member["user_email"]
                for member in fetch_team_members(supabase, team["id"])
            ]
            team["type"] = "team"

        for project in projects:
            project["members"] = [
                member["user_email"]
                for member in fetch_project_members(supabase, project["id"])
            ]
            project["type"] = "project"

        return {"teams": teams, "projects": projects}

    except Exception as e:
        print(f"get_all_teams_and_projects_with_members error: {e}")
        return {"teams": [], "projects": []}
