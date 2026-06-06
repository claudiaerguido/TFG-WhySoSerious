# Tipo: Validación | Requisitos: RF12
# Objetivo: Comprobar que get_project_tactical_risk calcula el riesgo táctico como la media
# de los riesgos individuales de los empleados en ese proyecto, sin mezclar datos de otros contextos.
from unittest.mock import patch, MagicMock
from backend.services.risk_service import get_project_tactical_risk

@patch("backend.services.risk_service.get_employee_project_risk", side_effect=[0.4, 0.2])
@patch("backend.services.risk_service.fetch_project_members", return_value=[
    {"user_email": "e1@tfg.com", "role": "employee"},
    {"user_email": "e2@tfg.com", "role": "employee"}
])
@patch("backend.services.risk_service.get_supabase_client", return_value=MagicMock())
def test_validation_tactical_project_risk(mock_db, mock_members, mock_emp_proj_risk):
    """
    REQ: RF12.
    DEFINICIÓN: El sistema debe mostrar el riesgo táctico de un proyecto concreto.
    VALIDACIÓN: El riesgo del proyecto es la media de los riesgos de sus empleados en ese contexto — en este caso (0.4 + 0.2) / 2 = 30.0% → Amarillo.
    """
    res = get_project_tactical_risk(10, days=7)
    
    assert res["status"] == "ok"
    assert res["project_risk"] == 30.0
    assert res["risk_level"] == "Amarillo"
