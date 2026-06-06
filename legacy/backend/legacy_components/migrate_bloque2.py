import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
from db_client import get_supabase_client

def migrate_bloque2():
    supabase = get_supabase_client()
    if not supabase:
        print("Error: No se pudo conectar a Supabase")
        return

    print("=== MIGRACIÓN DE DATOS: BLOQUE 2 ===")

    # 1. MIGRAR EQUIPOS (Desarrollo, QA)
    print("\n[1/4] Migrando equipos...")
    res_ws_teams = supabase.table("workspaces").select("id, name, owner_email").eq("type", "team").neq("id", 100).execute()
    teams_data = res_ws_teams.data or []
    if teams_data:
        # Renombramos owner_email a manager_email para la tabla teams
        formatted_teams = [{"id": t['id'], "name": t['name'], "manager_email": t['owner_email']} for t in teams_data]
        supabase.table("teams").upsert(formatted_teams).execute()
        print(f"  ✅ {len(formatted_teams)} equipos migrados.")
    else:
        print("  ⚠️ No hay equipos para migrar.")

    # 2. MIGRAR MEMBRESÍA DE EQUIPOS
    print("\n[2/4] Migrando miembros de equipos...")
    team_ids = [t['id'] for t in teams_data]
    if team_ids:
        res_wm = supabase.table("workspace_members").select("*").in_("workspace_id", team_ids).execute()
        wm_data = res_wm.data or []
        if wm_data:
            formatted_members = [
                {
                    "team_id": m['workspace_id'], 
                    "user_email": m['user_email'], 
                    "role": "member", 
                    "created_at": m['created_at']
                } for m in wm_data
            ]
            supabase.table("user_teams").upsert(formatted_members).execute()
            print(f"  ✅ {len(formatted_members)} membresías de equipo migradas.")
    else:
        print("  ⚠️ No se pueden migrar miembros sin equipos.")

    # 3. MIGRAR PROYECTOS (PRJ-Alpha, PRJ-Beta)
    print("\n[3/4] Migrando proyectos...")
    res_ws_projects = supabase.table("workspaces").select("id, name, owner_email, created_at").eq("type", "project").execute()
    projects_data = res_ws_projects.data or []
    if projects_data:
        supabase.table("projects").upsert(projects_data).execute()
        print(f"  ✅ {len(projects_data)} proyectos migrados.")
    else:
        print("  ⚠️ No hay proyectos para migrar.")

    # 4. MIGRAR MEMBRESÍA DE PROYECTOS
    print("\n[4/4] Migrando miembros de proyectos...")
    project_ids = [p['id'] for p in projects_data]
    if project_ids:
        res_wm_proj = supabase.table("workspace_members").select("*").in_("workspace_id", project_ids).execute()
        wm_proj_data = res_wm_proj.data or []
        if wm_proj_data:
            formatted_proj_members = [
                {
                    "project_id": m['workspace_id'], 
                    "user_email": m['user_email'], 
                    "created_at": m['created_at']
                } for m in wm_proj_data
            ]
            supabase.table("project_members").upsert(formatted_proj_members).execute()
            print(f"  ✅ {len(formatted_proj_members)} membresías de proyecto migradas.")
    else:
        print("  ⚠️ No se pueden migrar miembros sin proyectos.")

    # SINCRONIZACIÓN DE SECUENCIAS (Visualización)
    print("\n=== VERIFICACIÓN FINAL EN SUPABASE ===")
    
    final_teams = supabase.table("teams").select("name").execute().data
    final_projects = supabase.table("projects").select("name").execute().data
    
    print(f"Equipos actuales: {[t['name'] for t in (final_teams or [])]}")
    print(f"Proyectos actuales: {[p['name'] for p in (final_projects or [])]}")

if __name__ == "__main__":
    migrate_bloque2()
