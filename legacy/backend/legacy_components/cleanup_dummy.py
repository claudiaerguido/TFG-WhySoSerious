import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from db_client import get_supabase_client

def cleanup_dummy_data():
    supabase = get_supabase_client()
    if not supabase:
        print("Error: No se pudo conectar a Supabase")
        return

    print("=== LIMPIEZA DE DATOS DUMMY (Bloque 1.1) ===")

    # 1. Identificar IDs de Equipos de prueba por nombre o ID
    try:
        res = supabase.table("teams").select("id, name").execute()
        teams = res.data or []
        dummy_ids = [t['id'] for t in teams if t['id'] in [1, 2] or t['name'] in ['Equipo A', 'Equipo B']]
        
        if not dummy_ids:
            print("No se seleccionaron IDs dummy para eliminar o ya están limpios.")
        else:
            print(f"Eliminando relaciones en 'user_teams' para IDs: {dummy_ids}")
            supabase.table("user_teams").delete().in_("team_id", dummy_ids).execute()
            
            print(f"Eliminando equipos en 'teams' para IDs: {dummy_ids}")
            supabase.table("teams").delete().in_("id", dummy_ids).execute()
            
            print("✅ Limpieza completada con éxito.")
            
    except Exception as e:
        print(f"Error durante la limpieza: {e}")

if __name__ == "__main__":
    cleanup_dummy_data()
