import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from db_client import get_supabase_client
import pandas as pd

def diagnose_teams():
    supabase = get_supabase_client()
    if not supabase:
        print("Error: No se pudo conectar a Supabase")
        return

    print("=== DIAGNÓSTICO DE MODELOS DE EQUIPO ===")

    # 1. Obtener Teams (Modelo Oficial a Futuro)
    try:
        res_teams = supabase.table("teams").select("*").execute()
        df_teams = pd.DataFrame(res_teams.data or [])
        print(f"\nTabla 'teams': {len(df_teams)} registros")
        if not df_teams.empty:
            print(df_teams[['id', 'name']])
    except Exception as e:
        print(f"Error cargando 'teams': {e}")
        df_teams = pd.DataFrame()

    # 2. Obtener User-Teams
    try:
        res_ut = supabase.table("user_teams").select("*").execute()
        df_ut = pd.DataFrame(res_ut.data or [])
        print(f"\nTabla 'user_teams': {len(df_ut)} membresías")
    except Exception as e:
        print(f"Error cargando 'user_teams': {e}")
        df_ut = pd.DataFrame()

    # 3. Obtener Workspaces de tipo 'team' (Modelo Legacy)
    try:
        res_ws_teams = supabase.table("workspaces").select("*").eq("type", "team").execute()
        df_ws_teams = pd.DataFrame(res_ws_teams.data or [])
        print(f"\nTabla 'workspaces' (type='team'): {len(df_ws_teams)} registros")
        if not df_ws_teams.empty:
            print(df_ws_teams[['id', 'name']])
    except Exception as e:
        print(f"Error cargando 'workspaces': {e}")
        df_ws_teams = pd.DataFrame()

    # 4. Obtener Workspace Members para esos equipos
    try:
        res_wm = supabase.table("workspace_members").select("*").execute()
        df_wm = pd.DataFrame(res_wm.data or [])
        
        # Filtrar solo miembros de los workspaces de tipo team
        team_ws_ids = set(df_ws_teams['id'].tolist()) if not df_ws_teams.empty else set()
        df_wm_teams = df_wm[df_wm['workspace_id'].isin(team_ws_ids)]
        print(f"\nTabla 'workspace_members' (para equipos): {len(df_wm_teams)} membresías")
    except Exception as e:
        print(f"Error cargando 'workspace_members': {e}")
        df_wm_teams = pd.DataFrame()

    # 5. Análisis Detallado de Membresías
    print("\n=== DETALLE DE MEMBRESÍAS ===")
    
    print("\n[Modelo Nuevo] Tabla 'teams':")
    for _, row in df_teams.iterrows():
        m = df_ut[df_ut['team_id'] == row['id']]['user_email'].tolist() if not df_ut.empty else []
        print(f"  - {row['name']} (ID: {row['id']}): {m}")

    print("\n[Modelo Legacy] 'workspaces' (type='team'):")
    for _, row in df_ws_teams.iterrows():
        m = df_wm_teams[df_wm_teams['workspace_id'] == row['id']]['user_email'].tolist() if not df_wm_teams.empty else []
        print(f"  - {row['name']} (ID: {row['id']}): {m}")

    # 6. Proyectos (Para confirmar migración)
    res_projects = supabase.table("workspaces").select("*").eq("type", "project").execute()
    df_projects = pd.DataFrame(res_projects.data or [])
    print(f"\nTablar 'workspaces' (type='project'): {len(df_projects)} registros")
    for _, row in df_projects.iterrows():
        m = df_wm[df_wm['workspace_id'] == row['id']]['user_email'].tolist() if not df_wm.empty else []
        print(f"  - {row['name']} (ID: {row['id']}): {m}")

if __name__ == "__main__":
    diagnose_teams()
