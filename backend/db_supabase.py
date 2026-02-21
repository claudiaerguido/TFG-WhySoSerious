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

def save_risk_metrics(user_email, timestamp, scores, message_id):
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
        "neutro": scores.get("NEUTRO", 0),
        "message_id": message_id
    }

    try:
        # Usamos la API de Supabase (más fiable que conexión directa a DB)
        response = supabase.table("risk_metrics").insert(data).execute()
        # print(f"✅ Guardado en Supabase: {user_email}")
    except Exception as e:
        print(f"⚠️ Error guardando en Supabase: {e}")

def get_team_risk_metrics(team_id: int, days: int = 7):
    """
    US11 MVP: Llama a una función RPC de Supabase para calcular el riesgo medio
    del equipo en los últimos N días.
    """
    supabase = get_supabase_client()
    if not supabase:
        return {"error": "Faltan credenciales de Supabase"}
        
    try:
        if team_id is None:
            return {"error": "Se requiere un team_id para esta consulta."}

        # Llamar a la función RPC (Remote Procedure Call) en Supabase
        # que calcula la media por usuario y luego la media global.
        print(f"[SUPABASE DB] 🔎 Ejecutando RPC 'get_team_risk' con args: p_team_id={team_id}, p_days={days}")
        response = supabase.rpc("get_team_risk", {"p_team_id": team_id, "p_days": days}).execute()
        print(f"[SUPABASE DB] 📊 Datos puros devueltos por RPC: {response.data}")
        
        # El RPC devuelve una lista con un diccionario: [{'team_risk': 0.85, 'users_included': 3}]
        data = response.data
        if not data or len(data) == 0:
             return {"status": "ok", "risk_score_percentage": 0, "risk_level": "Verde", "sample_size": 0, "message": "No hay datos"}
             
        # Convertimos el índice (0 a 1) en porcentaje (0 a 100)
        risk_score = data[0].get("team_risk", 0) * 100
        users_count = data[0].get("users_included", 0)
        
        # 3. Lógica de "Semáforo"
        risk_level = "Verde"
        if risk_score > 66:
            risk_level = "Rojo"
        elif risk_score >= 33:
            risk_level = "Amarillo"
            
        return {
            "status": "ok",
            "risk_score_percentage": round(risk_score, 3),
            "risk_level": risk_level,
            "sample_size": users_count
        }
        
    except Exception as e:
        print(f"⚠️ Error leyendo métricas del equipo: {e}")
        return {"error": str(e)}
