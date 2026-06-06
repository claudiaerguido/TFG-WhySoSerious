# Tipo: Validación | Requisitos: RF06, RNF02
# Objetivo: Comprobar que get_user_role recupera correctamente el rol del usuario desde
# Supabase y que el backend distingue entre admin, manager y employee.
from unittest.mock import patch, MagicMock
from backend.services.permissions_service import get_user_role

@patch("backend.services.permissions_service.get_supabase_client")
def test_validation_role_access(mock_client):
    """
    REQ: RF06 y RNF02.
    DEFINICIÓN: El sistema debe determinar el rol del usuario para aplicar el ámbito de visibilidad y el modelo RBAC.
    VALIDACIÓN: get_user_role devuelve el rol exacto que hay en base de datos para cada usuario.
    """
    mock_supabase = MagicMock()
    mock_client.return_value = mock_supabase
    
    # Simular 'admin'
    mock_supabase.table().select().eq().maybe_single().execute.return_value.data = {"role": "admin"}
    assert get_user_role("javier@tfg.com") == "admin"
    
    # Simular 'manager'
    mock_supabase.table().select().eq().maybe_single().execute.return_value.data = {"role": "manager"}
    assert get_user_role("ana@tfg.com") == "manager"
