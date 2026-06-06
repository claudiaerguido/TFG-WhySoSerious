# Tipo: Validación | Requisitos: RF11
# Objetivo: Comprobar que get_team_global_risk calcula la media de riesgo solo sobre empleados,
# ignorando managers, y que el nivel de semáforo resultante es el correcto.
from unittest.mock import patch, MagicMock
from backend.services.risk_service import get_team_global_risk

@patch("backend.services.risk_service.get_member_projects_breakdown", return_value=[])
@patch("backend.services.risk_service.get_employee_global_risk", side_effect=lambda email, days, s=None, e=None: 0.8 if email == "emp@tfg.com" else 0.2)
@patch("backend.services.risk_service.fetch_team_members", return_value=[
    {"user_email": "emp@tfg.com", "display_name": "Emp", "role": "employee"},
    {"user_email": "man@tfg.com", "display_name": "Man", "role": "manager"}
])
@patch("backend.services.risk_service.get_supabase_client", return_value=MagicMock())
def test_validation_team_global_risk(mock_db, mock_members, mock_emp_risk, mock_breakdown):
    """
    REQ: RF11.
    DEFINICIÓN: El sistema debe mostrar el riesgo del equipo basado en sus integrantes operativos.
    VALIDACIÓN: El manager se excluye del cálculo de la media de equipo. Solo los employees contribuyen al riesgo agregado, y el nivel de semáforo se asigna según los umbrales definidos.
    """
    res = get_team_global_risk(1, days=7)
    
    assert res["status"] == "ok"
    assert res["team_risk"] == 80.0
    assert res["risk_level"] == "Rojo"
