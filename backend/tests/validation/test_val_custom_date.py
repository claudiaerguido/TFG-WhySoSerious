# Tipo: Validación | Requisitos: RF14
# Objetivo: Comprobar que get_project_tactical_risk propaga start_date y end_date
# correctamente a la consulta de Supabase cuando el usuario elige el filtro "Personalizado".
from unittest.mock import patch, MagicMock
from backend.services.risk_service import get_project_tactical_risk

@patch("backend.services.risk_service.get_supabase_client")
@patch("backend.services.risk_service.fetch_project_members")
def test_validation_custom_date_range(mock_members, mock_db_getter):
    """
    REQ: RF14. Validación del uso de rangos temporales en la consulta analítica.
    DEFINICIÓN: El usuario puede filtrar la información por un periodo personalizado para observar la evolución o estado en fechas concretas.
    VALIDACIÓN: Con fechas explícitas, la consulta a Supabase aplica los filtros gte y lte sobre message_timestamp con los valores correctos.
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
    
    # Las fechas explícitas tienen prioridad sobre el parámetro days
    res = get_project_tactical_risk(project_id=1, days=0, start_date="2026-01-01", end_date="2026-03-31")
    
    assert res["status"] == "ok"
    
    # Verificar que la cadena ORM lleva gte y lte con los valores correctos
    mock_in.gte.assert_called_with("message_timestamp", "2026-01-01")
    mock_gte.lte.assert_called_with("message_timestamp", "2026-03-31T23:59:59.999Z")
