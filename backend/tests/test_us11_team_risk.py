import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_supabase import get_team_risk_metrics

def test_team_risk():
    print("--- Probando Indicador de Riesgo por Equipo (US11) ---")
    team_id = 1
    days = 30
    print(f"Consultando riesgo agrupado para team_id={team_id} en los últimos {days} días (llamada RPC directa)...")
    
    try:
        res = get_team_risk_metrics(team_id, days)
        if "error" in res:
            print(f"❌ ERROR en la consulta de riesgo: {res['error']}")
        else:
            print(f"✅ ÉXITO: Resultado obtenido correctamente.")
            print(f"   Riesgo General: {res.get('risk_level')}")
            print(f"   Porcentaje: {res.get('risk_score_percentage')}%")
            print(f"   Muestra: {res.get('sample_size')} usuarios analizados en el rango.")
    except Exception as e:
        print(f"❌ ERROR fatal al contactar backend/BD: {e}")

if __name__ == "__main__":
    test_team_risk()
