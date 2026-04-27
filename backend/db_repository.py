import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
from supabase import Client
from logic.risk_model import DB_COLS, TARGET_LABELS

# ── Miembros y Estructura ──────────────────────────────────────────────────

def _fetch_members_from_table(supabase: Client, table_name: str, id_column: str, id_value: int, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
    """Helper genérico para obtener miembros cruzando una tabla con 'org_users'."""
    try:
        q = supabase.table(table_name).select("user_email").eq(id_column, id_value)
        
        # Filtro temporal SCD:
        # Si no hay start_date ni end_date de la query, queremos los miembros actuales (end_date IS NULL)
        if not start_date and not end_date:
            q = q.is_("end_date", "null")
        else:
            # Si piden un rango temporal [start_date, end_date]
            # El miembro estaba activo si: su start_date <= query.end_date Y (su end_date >= query.start_date O es nulo)
            effective_end = end_date or datetime.utcnow().isoformat()
            q = q.lte("start_date", effective_end)
            if start_date:
                q = q.or_(f"end_date.gte.{start_date},end_date.is.null")

        res_memb = q.execute()
        emails = [r["user_email"] for r in (res_memb.data or [])]
        if not emails: return []

        res_users = supabase.table("org_users").select("user_email, display_name, role").in_("user_email", emails).execute()
        user_map = {u["user_email"]: u for u in (res_users.data or [])}

        return [
            {
                "user_email": email, 
                "display_name": user_map.get(email, {}).get("display_name"),
                "role": user_map.get(email, {}).get("role", "employee")
            }
            for email in emails
        ]
    except Exception as e:
        print(f"⚠️ _fetch_members_from_table error [{table_name}]: {e}")
        return []

def fetch_user_metadata(supabase: Client, user_email: str) -> Dict[str, Any]:
    """Obtiene el nombre visible y el rol de un usuario."""
    try:
        res = supabase.table("org_users").select("display_name, role").eq("user_email", user_email).single().execute()
        return res.data or {}
    except Exception as e:
        print(f"⚠️ fetch_user_metadata error [{user_email}]: {e}")
        return {}

def fetch_team_members(supabase: Client, team_id: int, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
    """Obtiene los integrantes de un equipo."""
    return _fetch_members_from_table(supabase, "user_teams", "team_id", team_id, start_date, end_date)

def fetch_project_members(supabase: Client, project_id: int, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
    """Obtiene los integrantes de un proyecto."""
    return _fetch_members_from_table(supabase, "project_members", "project_id", project_id, start_date, end_date)

def fetch_user_projects(supabase: Client, user_email: str, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
    """Lista los proyectos donde participa un usuario."""
    try:
        q = supabase.table("project_members").select("project_id, projects(name)").eq("user_email", user_email)
        
        if not start_date and not end_date:
            q = q.is_("end_date", "null")
        else:
            effective_end = end_date or datetime.utcnow().isoformat()
            q = q.lte("start_date", effective_end)
            if start_date:
                q = q.or_(f"end_date.gte.{start_date},end_date.is.null")
                
        res = q.execute()
        return res.data or []
    except Exception as e:
        print(f"⚠️ fetch_user_projects error: {e}")
        return []

# ── Gestión de Proyectos (US-20) ───────────────────────────────────────────

def add_user_to_project(supabase: Client, user_email: str, project_id: int) -> bool:
    """Asocia un usuario a un proyecto (Evita duplicados vía upsert)."""
    try:
        # Al añadir, aseguramos que end_date sea NULL (por si vuelve a entrar) y start_date sea actual
        # En vez de upsert directo, comprobamos si ya está activo. Para simplificar, hacemos upsert
        # asumiendo que on_conflict actualice los datos. 
        # Supabase no soporta on_conflict parcial en upsert sin configurarlo bien, 
        # así que es mejor buscar primero si existe un registro cerrado.
        
        # En la práctica, el upsert actualiza el end_date a null.
        supabase.table("project_members").upsert({
            "user_email": user_email,
            "project_id": project_id,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": None
        }, on_conflict="user_email,project_id").execute()
        return True
    except Exception as e:
        print(f"⚠️ add_user_to_project error: {e}")
        return False

def remove_user_from_project(supabase: Client, user_email: str, project_id: int) -> bool:
    """Desasocia un usuario de un proyecto."""
    try:
        # SCD: En lugar de borrar, ponemos fecha de fin
        supabase.table("project_members").update({
            "end_date": datetime.utcnow().isoformat()
        }).eq("user_email", user_email).eq("project_id", project_id).is_("end_date", "null").execute()
        return True
    except Exception as e:
        print(f"⚠️ remove_user_from_project error: {e}")
        return False

def fetch_all_projects_catalog(supabase: Client) -> List[Dict[str, Any]]:
    """Obtiene el catálogo completo de proyectos (ID y Nombre)."""
    try:
        res = supabase.table("projects").select("id, name").order("name").execute()
        return res.data or []
    except Exception as e:
        print(f"⚠️ fetch_all_projects_catalog error: {e}")
        return []

# ── Métricas y Persistencia ────────────────────────────────────────────────

def fetch_metrics_for_users(
    supabase: Client,
    emails: List[str],
    days: int,
    project_id: int = None,
    global_mode: bool = False,
    workspace_id: int = None, # Compatibilidad Legacy: Fase A
    start_date: str = None,
    end_date: str = None
) -> pd.DataFrame:
    """Recupera métricas de riesgo filtradas por usuario y tiempo."""
    try:
        cols = ["user_email", "message_timestamp"] + [DB_COLS[l] for l in TARGET_LABELS]
        
        q = (
            supabase.table("risk_metrics")
            .select(",".join(cols))
            .in_("user_email", emails)
        )
        
        # Asegurar que end_date incluya todo el día final (hasta 23:59:59)
        effective_end = end_date
        if effective_end and len(effective_end) == 10:
            effective_end = f"{effective_end}T23:59:59.999Z"

        if start_date and effective_end:
            q = q.gte("message_timestamp", start_date).lte("message_timestamp", effective_end)
        elif start_date:
            q = q.gte("message_timestamp", start_date)
        elif effective_end:
            q = q.lte("message_timestamp", effective_end)
        else:
            since = (datetime.utcnow() - timedelta(days=days)).isoformat()
            q = q.gte("message_timestamp", since)
        
        if not global_mode:
            if project_id is not None:
                q = q.eq("project_id", project_id)
            elif workspace_id is not None:
                q = q.eq("workspace_id", workspace_id)
            else:
                q = q.is_("project_id", "null")
                
        return pd.DataFrame(q.execute().data or [])
    except Exception as e:
        print(f"⚠️ fetch_metrics_for_users error: {e}")
        return pd.DataFrame()

def save_risk_metrics(
    supabase: Client,
    user_email: str,
    timestamp: str,
    scores: Dict[str, Any],
    message_id: str,
    project_id: int = None,
) -> None:
    """Guarda los scores de riesgo de un mensaje en la base de datos."""
    # Los scores deben estar en el diccionario antes del upsert
    data: Dict[str, Any] = {
        "user_email": user_email,
        "message_timestamp": timestamp,
        "message_id": message_id,
        "project_id": project_id,
        "workspace_id": project_id # Compatibilidad Legacy: Fase A
    }

    for label in TARGET_LABELS:
        data[DB_COLS[label]] = float(scores.get(label, 0) or 0)

    try:
        supabase.table("risk_metrics").upsert(data, on_conflict="message_id").execute()
    except Exception as e:
        if "duplicate" not in str(e).lower() and "unique" not in str(e).lower():
            print(f"⚠️ save_risk_metrics error message_id={message_id}: {e}")

# ── Configuración Global ───────────────────────────────────────────────────

def fetch_org_settings(supabase: Client) -> Dict[str, Any]:
    """Recupera la configuración global de la organización."""
    try:
        res = supabase.table("org_settings").select("*").execute()
        return {item["key"]: item["value"] for item in (res.data or [])}
    except Exception as e:
        print(f"⚠️ fetch_org_settings error: {e}")
        return {}

def save_org_settings(supabase: Client, settings: Dict[str, Any]) -> bool:
    """Guarda la configuración global en la tabla org_settings."""
    try:
        data = [{"key": k, "value": str(v)} for k, v in settings.items()]
        if data:
            supabase.table("org_settings").upsert(data, on_conflict="key").execute()
        return True
    except Exception as e:
        print(f"⚠️ save_org_settings error: {e}")
        return False
