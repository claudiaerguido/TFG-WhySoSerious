import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

def get_supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("❌ Faltan credenciales de Supabase en .env")
        return None
    return create_client(url, key)

def save_risk_metrics(user_email, timestamp, scores):
    supabase = get_supabase_client()
    if not supabase:
        return

    data = {
        "user_email": user_email,
        "message_timestamp": timestamp,
        "estres_ansiedad": scores.get("ESTRES_ANSIEDAD", 0),
        "sobrecarga_urgencia": scores.get("SOBRECARGA_URGENCIA", 0),
        "enfado_irritacion": scores.get("ENFADO_IRRITACION", 0),
        "cansancio_fatiga": scores.get("CANSANCIO_FATIGA", 0),
        "positivo_alivio": scores.get("POSITIVO_ALIVIO", 0),
        "neutro": scores.get("NEUTRO", 0)
    }

    try:
        # Usamos la API de Supabase (más fiable que conexión directa a DB)
        response = supabase.table("risk_metrics").insert(data).execute()
        # print(f"✅ Guardado en Supabase: {user_email}")
    except Exception as e:
        print(f"⚠️ Error guardando en Supabase: {e}")
