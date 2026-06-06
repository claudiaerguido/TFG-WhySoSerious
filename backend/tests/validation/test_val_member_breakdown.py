# Tipo: Validación | Requisitos: RF08, RF12 (Parcial)
# Objetivo: Comprobar que get_member_projects_breakdown devuelve el riesgo de un empleado
# desglosado por proyecto, sin mezclar datos entre proyectos distintos.
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
    REQ: RF08 y RF12 (Parcial).
    DEFINICIÓN: El sistema debe permitir a perfiles de gestión autorizados consultar el detalle individual y desglosar el riesgo de un empleado por proyecto.
    VALIDACIÓN: El servicio consulta los proyectos del usuario, calcula el riesgo en cada uno por separado y devuelve una lista con el nombre y el riesgo de cada proyecto.
    """
    breakdown = get_member_projects_breakdown("emp@tfg.com")
    
    assert len(breakdown) == 2
    assert breakdown[0]["project_name"] == "Alpha"
    assert breakdown[0]["project_risk"] == 90.0
    assert breakdown[1]["project_name"] == "Beta"
    assert breakdown[1]["project_risk"] == 10.0
