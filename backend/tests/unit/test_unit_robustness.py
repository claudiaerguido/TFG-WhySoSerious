"""
7. Test de robustez (test_unit_robustness.py)

Qué valida: que el sistema es resiliente ante datos inusuales, vacíos o fuera de rango.
Explicación: estas pruebas aseguran que el software no se detenga ante errores (robusto) y que maneje con elegancia situaciones como equipos sin miembros operativos o puntuaciones imposibles de IA.
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from backend.logic.risk_model import compute_pearson_msg_risk
from backend.services.risk_service import get_team_global_risk

def test_risk_engine_empty_data():
    """Falla con elegancia si no hay mensajes que analizar."""
    df_empty = pd.DataFrame()
    risk_series = compute_pearson_msg_risk(df_empty)
    assert risk_series.empty, "El motor debe devolver una serie vacía, no un error."

def test_risk_engine_out_of_range():
    """Limpia datos basura (puntuaciones > 1.0) mediante clip."""
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
    """Evita divisiones por cero si un equipo no tiene 'employees' con datos."""
    mock_members.return_value = [
        {"user_email": "boss@tfg.com", "role": "manager"} # Solo un manager
    ]
    
    # Simulamos que no hay datos para calcular riesgos individuales
    with patch("backend.services.risk_service.get_employee_global_risk", return_value=None):
        res = get_team_global_risk(99)
        
    assert res["status"] == "ok"
    assert res["team_risk"] == 0.0, "La media debe ser 0.0 si no hay personal operativo con datos."
