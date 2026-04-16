# Tipo: Validación
# Requisitos cubiertos: RF13, RF14
# Objetivo: Verificar que el sistema permite filtrar y visualizar la información por rango de fechas.
"""
7. Test de validación de filtro por fechas (test_val_custom_date.py)

Qué valida: que el sistema procesa  y aplica en la consulta SQL base, 
los parámetros `start_date` y `end_date` correspondientes a la opción "Personalizado".
"""
import pytest
from unittest.mock import patch, MagicMock
from backend.services.risk_service import get_project_tactical_risk

@patch("backend.services.risk_service.get_supabase_client")
@patch("backend.services.risk_service.fetch_project_members")
def test_validation_custom_date_range(mock_members, mock_db_getter):
    """
    REQ: RF13 y RF14. Validación del uso de rangos temporales en la consulta analítica.
    DEFINICIÓN: El usuario puede filtrar la información por un periodo personalizado para observar la evolución o estado en fechas concretas.
    VALIDACIÓN: Se comprueba que al llamar al servicio con fechas explícitas, la consulta resultante al ORM (Supabase) inyecta correctamente los filtros `gte` y `lte` sobre el campo `message_timestamp`.
    """
    mock_supabase = MagicMock()
    mock_db_getter.return_value = mock_supabase
    
    # Un empleado desencadenará la llamada a _compute_mean_risk_from_df -> fetch_metrics_for_users
    mock_members.return_value = [
        {"user_email": "emp@tfg.com", "display_name": "Emp", "role": "employee"}
    ]
    
    # Mocking query chain
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_in = MagicMock()
    mock_gte = MagicMock()
    mock_lte = MagicMock()
    mock_eq = MagicMock()
    mock_exe = MagicMock()
    
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.in_.return_value = mock_in
    mock_in.gte.return_value = mock_gte
    mock_gte.lte.return_value = mock_lte
    mock_lte.eq.return_value = mock_eq
    mock_eq.execute.return_value = mock_exe
    mock_exe.data = [] 
    
    # Ejecutamos el servicio pasándole fechas explícitas (Priorizarán sobre el days natural)
    res = get_project_tactical_risk(project_id=1, days=0, start_date="2026-01-01", end_date="2026-03-31")
    
    assert res["status"] == "ok"
    
    # Comprobar aserción de que construimos el SQL final mediante ORM con el GTE y LTE de Supabase
    mock_in.gte.assert_called_with("message_timestamp", "2026-01-01")
    mock_gte.lte.assert_called_with("message_timestamp", "2026-03-31T23:59:59.999Z")
