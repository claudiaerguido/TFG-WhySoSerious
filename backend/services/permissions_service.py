from typing import List, Dict, Any
from db_client import get_supabase_client

def ensure_org_user(email: str, display_name: str) -> None:
    """
    Asegura la existencia del usuario en la tabla 'org_users'.
    Se ejecuta tras el login exitoso via Microsoft Graph.
    """
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
    """
    Recupera el rol administrativo del usuario ('admin'|'manager'|'employee').
    """
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
    Implementa el modelo de visibilidad basado en responsabilidad (RBAC):
    - 'admin': Visibilidad global de la organización.
    - 'manager'/'employee': Visibilidad limitada a entidades bajo su gestión directa
      (donde figura como 'manager_email' en equipos u 'owner_email' en proyectos).
    """
    supabase = get_supabase_client()
    if not supabase: return {"teams": [], "projects": []}
    
    try:
        # 1. Acceso de administrador: total
        if role == "admin":
            res_t = supabase.table("teams").select("id, name").execute()
            res_p = supabase.table("projects").select("id, name").execute()
            return {"teams": res_t.data or [], "projects": res_p.data or []}
        
        # 2. Acceso por responsabilidad (Managers y Employees)
        # Un Manager funcional solo ve lo que gestiona, no toda la empresa.
        res_t = supabase.table("teams").select("id, name").eq("manager_email", email).execute()
        res_p = supabase.table("projects").select("id, name").eq("owner_email", email).execute()
        
        return {
            "teams": res_t.data or [], 
            "projects": res_p.data or []
        }
    except Exception as e:
        print(f"⚠️ get_teams_and_projects_for_user error: {e}")
        return {"teams": [], "projects": []}
