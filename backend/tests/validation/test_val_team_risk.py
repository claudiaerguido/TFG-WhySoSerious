# Tipo: Validación
# Requisitos cubiertos: RF11
# Objetivo: Verificar el cálculo y la visualización del indicador de riesgo global por equipo.
"""
2. Test de riesgo global de equipo (test_val_team_risk.py)

Qué valida: que el sistema calcula correctamente el indicador agregado de riesgo de un equipo.
Explicación: el test verifica que se obtiene una media representativa del riesgo de los integrantes operativos del equipo y que los perfiles de supervisión no alteran el resultado agregado.
"""
import pytest
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
    VALIDACIÓN: Se verifica que el cálculo de riesgo de equipo ignora perfiles de gestión (managers) y realiza una media ponderada correcta de los empleados, resultando en un nivel de riesgo (rojo/amarillo/verde) esperado.
    """
    res = get_team_global_risk(1, days=7)
    
    assert res["status"] == "ok"
    assert res["team_risk"] == 80.0
    assert res["risk_level"] == "Rojo"
