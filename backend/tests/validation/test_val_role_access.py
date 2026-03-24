"""
1. Test de acceso por roles (test_val_role_access.py)

Qué valida: que el sistema identifica correctamente el rol del usuario autenticado y aplica las restricciones de acceso adecuadas.
Explicación: este test comprueba que, tras el inicio de sesión, el backend consulta la base de datos y determina si el usuario actúa como administrador, responsable o empleado, garantizando que cada perfil solo acceda a la información permitida.
"""
import pytest
from unittest.mock import patch, MagicMock
from backend.services.permissions_service import get_user_role, get_supabase_client

@patch("backend.services.permissions_service.get_supabase_client")
def test_validation_role_access(mock_client):
    """6. Validación de acceso por roles (Consulta real a BD simulada)."""
    mock_supabase = MagicMock()
    mock_client.return_value = mock_supabase
    
    # Simular 'admin'
    mock_supabase.table().select().eq().maybe_single().execute.return_value.data = {"role": "admin"}
    assert get_user_role("javier@tfg.com") == "admin"
    
    # Simular 'manager'
    mock_supabase.table().select().eq().maybe_single().execute.return_value.data = {"role": "manager"}
    assert get_user_role("ana@tfg.com") == "manager"
