# Tipo: Unitario | Requisitos: RF10, RF11
# Prueba que el motor de riesgo no falla ante datos vacíos, valores fuera de rango o equipos sin empleados operativos.
import pandas as pd
from unittest.mock import patch, MagicMock

from backend.logic.risk_model import compute_pearson_msg_risk
from backend.services.risk_service import get_team_global_risk

def test_risk_engine_empty_data():
    """
    REQ: RF10 (Detectar tono e inferir señales).
    DEFINICIÓN: El sistema debe ser robusto ante la ausencia de datos.
    VALIDACIÓN: El motor devuelve una serie vacía sin lanzar excepción cuando el DataFrame de entrada está vacío.
    """
    df_empty = pd.DataFrame()
    risk_series = compute_pearson_msg_risk(df_empty)
    assert risk_series.empty, "El motor debe devolver una serie vacía, no un error."

def test_risk_engine_out_of_range():
    """
    REQ: RF10 (Detectar tono e inferir señales).
    DEFINICIÓN: El sistema debe ser robusto ante puntuaciones imposibles del modelo NLP (por encima de 1 o por debajo de 0).
    VALIDACIÓN: El resultado final siempre está dentro de [0, 1] aunque la entrada no lo esté.
    """
    data = {
        "estres_ansiedad": [1.5, -0.2], # Valores imposibles de la IA
        "enfado_irritacion": [0.0, 0.0]
    }
    df = pd.DataFrame(data)
    risk_series = compute_pearson_msg_risk(df)
    
    assert all(0.0 <= x <= 1.0 for x in risk_series), "El sistema debe corregir valores fuera de rango [0, 1]"

@patch("backend.services.risk_service.fetch_team_members")
@patch("backend.services.risk_service.get_supabase_client")
def test_team_global_risk_no_employees_media(mock_client, mock_members):
    """
    REQ: RF11 (Calcular y mostrar indicador simple).
    DEFINICIÓN: El riesgo colectivo debe calcularse correctamente incluso en escenarios de personal incompleto.
    VALIDACIÓN: Si no hay empleados operativos con datos, el riesgo de equipo es 0.0 y no se produce un error de división por cero.
    """
    mock_members.return_value = [
        {"user_email": "boss@tfg.com", "role": "manager"} # Solo un manager
    ]
    
    # Simulamos que no hay datos para calcular riesgos individuales
    with patch("backend.services.risk_service.get_employee_global_risk", return_value=None):
        res = get_team_global_risk(99)
        
    assert res["status"] == "ok"
    assert res["team_risk"] == 0.0, "La media debe ser 0.0 si no hay personal operativo con datos."
