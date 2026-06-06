import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from db_client import get_supabase_client

def check_schema():
    supabase = get_supabase_client()
    if not supabase:
        print("Error: No se pudo conectar a Supabase")
        return

    tables = ["user_teams", "workspace_members", "risk_metrics"]
    for table in tables:
        print(f"\n--- Estructura de '{table}' ---")
        try:
            # Una forma sencilla de ver columnas en Supabase/PostgREST es pedir 1 fila
            res = supabase.table(table).select("*").limit(1).execute()
            if res.data:
                print(f"Columnas detectadas: {list(res.data[0].keys())}")
            else:
                print("Tabla vacía, no se pueden detectar columnas por datos.")
        except Exception as e:
            print(f"Error al consultar '{table}': {e}")

if __name__ == "__main__":
    check_schema()
