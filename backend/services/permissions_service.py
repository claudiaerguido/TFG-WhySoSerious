from typing import List, Dict, Any, Optional
from supabase import Client
from db_client import get_supabase_client

def ensure_org_user(email: str, display_name: str) -> None:
    """Asegura que un usuario existe en la tabla org_users."""
    supabase = get_supabase_client()
    if not supabase or not email: return
    try:
        supabase.table("org_users").upsert(
            {"user_email": email, "display_name": display_name, "role": "employee"},
            on_conflict="user_email",
            ignore_duplicates=True,
        ).execute()
    except Exception as e:
        print(f"⚠️ ensure_org_user error: {e}")


def get_user_role(email: str) -> str:
    """Devuelve el rol del usuario ('admin'|'manager'|'employee')."""
    supabase = get_supabase_client()
    if not supabase or not email: return "employee"
    try:
        res = supabase.table("org_users").select("role").eq("user_email", email).maybe_single().execute()
        return (res.data or {}).get("role", "employee")
    except Exception as e:
        print(f"⚠️ get_user_role error: {e}")
        return "employee"


def get_teams_and_projects_for_user(email: str, role: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Define la visibilidad de dashboards según rol y responsabilidad:
    - admin/manager → ve todo.
    - employee      → ve solo donde es responsable directo (Manager de equipo u Owner de proyecto).
    """
    supabase = get_supabase_client()
    if not supabase: return {"teams": [], "projects": []}
    
    try:
        if role in ["admin", "manager"]:
            res_teams = supabase.table("teams").select("id, name").execute()
            res_projects = supabase.table("projects").select("id, name").execute()
            return {
                "teams": res_teams.data or [],
                "projects": res_projects.data or []
            }
        
        # Filtrado estricto por responsabilidad para empleados
        res_teams = supabase.table("teams").select("id, name").eq("manager_email", email).execute()
        res_projects = supabase.table("projects").select("id, name").eq("owner_email", email).execute()
        
        return {
            "teams": res_teams.data or [], 
            "projects": res_projects.data or []
        }
    except Exception as e:
        print(f"⚠️ get_teams_and_projects_for_user error: {e}")
        return {"teams": [], "projects": []}
