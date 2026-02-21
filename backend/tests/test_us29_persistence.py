import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_supabase import save_risk_metrics, get_supabase_client
from datetime import datetime

def test_persistence():
    print("--- Probando Persistencia en Supabase (US29) ---")
    email = "test.persistencia@ceu.es"
    now = datetime.now().isoformat()
    scores = {"ESTRES_ANSIEDAD": 0.99, "SOBRECARGA_URGENCIA": 0.88, "CANSANCIO_FATIGA": 0.77}
    
    print(f"Guardando métrica falsa para {email}...")
    try:
        save_risk_metrics(email, now, scores)
    except Exception as e:
        print(f"❌ ERROR interno al guardar: {e}")
        return
    
    print("Verificando si existe en base de datos...")
    client = get_supabase_client()
    try:
        res = client.table("risk_metrics").select("*").eq("user_email", email).order("created_at", desc=True).limit(1).execute()
        if res.data:
            print("✅ ÉXITO: El dato se guardó y pudo ser recuperado desde Supabase de forma persistente.")
            print("   Dato recuperado:", res.data[0])
            # Limpiar
            client.table("risk_metrics").delete().eq("user_email", email).execute()
            print("🧹 Dato de prueba limpiado correctamente de la BD.")
        else:
            print("❌ ERROR: No se encontró el dato guardado en Supabase.")
    except Exception as e:
         print(f"❌ ERROR al leer de la base de datos: {e}")

if __name__ == "__main__":
    test_persistence()
