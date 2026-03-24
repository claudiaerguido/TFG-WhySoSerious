"""
2. Test de riesgo global de equipo (test_val_team_risk.py)

Qué valida: que el sistema calcula correctamente el indicador agregado de riesgo de un equipo.
Explicación: el test verifica que se obtiene una media representativa del riesgo de los integrantes operativos del equipo y que los perfiles de supervisión no alteran el resultado agregado.
"""
import pytest
from unittest.mock import patch, MagicMock
from backend.services.risk_service import get_team_global_risk

@patch("backend.services.risk_service.get_member_projects_breakdown", return_value=[])
@patch("backend.services.risk_service.get_employee_global_risk", side_effect=lambda email, days: 0.8 if email == "emp@tfg.com" else 0.2)
@patch("backend.services.risk_service.fetch_team_members", return_value=[
    {"user_email": "emp@tfg.com", "display_name": "Emp", "role": "employee"},
    {"user_email": "man@tfg.com", "display_name": "Man", "role": "manager"}
])
@patch("backend.services.risk_service.get_supabase_client", return_value=MagicMock())
def test_validation_team_global_risk(mock_db, mock_members, mock_emp_risk, mock_breakdown):
    """7. Validación de riesgo global de equipo (excluye perfiles no employee)."""
    res = get_team_global_risk(1, days=7)
    
    assert res["status"] == "ok"
    assert res["team_risk"] == 80.0
    assert res["risk_level"] == "Rojo"
