# Tipo: Validación
# Requisitos cubiertos: RF12, RF13, RF15
# Objetivo: Verificar el desglose por miembro y proyecto dentro de la visualización analítica.
"""
6. Test de desglose por miembro (test_val_member_breakdown.py)

Qué valida: que el sistema ofrece trazabilidad individual del riesgo por proyecto.
Explicación: este test comprueba que, al analizar un miembro concreto, el sistema puede desglosar su riesgo entre los distintos proyectos en los que participa, evitando mezclas incorrectas entre contextos.
"""
import pytest
from unittest.mock import patch, MagicMock
from backend.services.risk_service import get_member_projects_breakdown

@patch("backend.services.risk_service.get_employee_project_risk", side_effect=[0.9, 0.1])
@patch("backend.services.risk_service.fetch_user_projects", return_value=[
    {"project_id": 1, "projects": {"name": "Alpha"}},
    {"project_id": 2, "projects": {"name": "Beta"}},
])
@patch("backend.services.risk_service.get_supabase_client", return_value=MagicMock())
def test_validation_member_breakdown(mock_db, mock_projects, mock_emp_proj_risk):
    """
    REQ: RF12 (Visiones agregadas) y RF15 (Perfil propio del empleado - Parcial).
    DEFINICIÓN: El sistema debe desglosar el riesgo de un empleado por proyecto para ofrecer visibilidad detallada.
    VALIDACIÓN: Verifica que el servicio de desglose consulta los proyectos del usuario y calcula el riesgo individual para cada uno, devolviendo una estructura que separa el impacto por contexto táctico.
    """
    breakdown = get_member_projects_breakdown("emp@tfg.com")
    
    assert len(breakdown) == 2
    assert breakdown[0]["project_name"] == "Alpha"
    assert breakdown[0]["project_risk"] == 90.0
    assert breakdown[1]["project_name"] == "Beta"
    assert breakdown[1]["project_risk"] == 10.0
