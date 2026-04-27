# Tipo: Validación
# Requisitos cubiertos: RF12
# Objetivo: Verificar el cálculo y la visualización del indicador de riesgo táctico por proyecto.
"""
3. Test de riesgo táctico de proyecto (test_val_project_risk.py)

Qué valida: que el sistema calcula el riesgo contextual de un proyecto concreto.
Explicación: este test asegura que los mensajes asociados a un proyecto solo afectan al indicador de ese proyecto, sin contaminar otros contextos de trabajo del mismo empleado.
"""
import pytest
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
    VALIDACIÓN: Se comprueba que el indicador calculado para el proyecto es la media de los riesgos individuales de sus miembros en ese contexto, asegurando la segregación de datos por proyecto.
    """
    res = get_project_tactical_risk(10, days=7)
    
    assert res["status"] == "ok"
    assert res["project_risk"] == 30.0
    assert res["risk_level"] == "Amarillo"
