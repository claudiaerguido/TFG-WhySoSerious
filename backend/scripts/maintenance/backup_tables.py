import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import json
from db_client import get_supabase_client

def backup_tables():
    supabase = get_supabase_client()
    if not supabase:
        print("Error: No se pudo conectar a Supabase")
        return

    tables = ["teams", "user_teams", "workspaces", "workspace_members", "risk_metrics"]
    backup_path = "/Users/vicente-erguido-benitez-kit-digital/.gemini/antigravity/brain/61567848-7c98-4cc6-b50c-77ab68144de2/backups"
    
    if not os.path.exists(backup_path):
        os.makedirs(backup_path)

    for table in tables:
        print(f"Haciendo backup de '{table}'...")
        try:
            # Paginación simple si es muy grande (ej: risk_metrics)
            # Para este TFG asumimos volumen manejable en un solo fetch
            res = supabase.table(table).select("*").execute()
            
            data = res.data or []
            file_path = os.path.join(backup_path, f"{table}_backup.json")
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"  - Guardado: {len(data)} filas en {file_path}")
            
        except Exception as e:
            print(f"  - Error en {table}: {e}")

if __name__ == "__main__":
    backup_tables()
