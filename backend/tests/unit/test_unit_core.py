import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

# Importaciones de los módulos core
from backend.logic.risk_model import _risk_level, compute_pearson_msg_risk
from backend.services.permissions_service import get_teams_and_projects_for_user
from backend.scheduler_tasks import find_best_project


def test_risk_level_thresholds():
    """1. Test de _risk_level() para Verde/Amarillo/Rojo."""
    assert _risk_level(15.0) == "Verde"
    assert _risk_level(25.0) == "Amarillo"
    assert _risk_level(40.0) == "Rojo"


def test_compute_pearson_msg_risk_valid():
    """2. Test de compute_pearson_msg_risk() con datos válidos (Varianza)."""
    data = {
        "estres_ansiedad": [0.8, 0.2, 0.9], 
        "enfado_irritacion": [0.1, 0.1, 0.2]
    }
    df = pd.DataFrame(data)
    
    risk_series = compute_pearson_msg_risk(df)
    
    assert len(risk_series) == 3
    assert all(0.0 <= x <= 1.0 for x in risk_series)
    assert risk_series[0] > risk_series[1]
    assert risk_series[2] > risk_series[0]


def test_compute_pearson_msg_risk_fallback():
    """3. Test de compute_pearson_msg_risk() sin varianza (Fallback aditivo)."""
    data = {
        "estres_ansiedad": [0.5, 0.5, 0.5], 
        "enfado_irritacion": [0.2, 0.2, 0.2]
    }
    df = pd.DataFrame(data)
    
    risk_series = compute_pearson_msg_risk(df)
    
    assert len(risk_series) == 3
    # Esperamos 0.7 (0.5 + 0.2) según el modelo aditivo conservador para fallbacks
    assert all(x == pytest.approx(0.7) for x in risk_series)


@patch("backend.services.permissions_service.get_supabase_client")
def test_get_teams_and_projects_for_user_admin_returns_all(mock_client):
    """4. Test RBAC: Admin debe recibir todas las entidades (sin filtros)."""
    mock_supabase = MagicMock()
    mock_client.return_value = mock_supabase
    mock_supabase.table().select().execute.return_value.data = [{"id": 1, "name": "Global Team"}]
    
    res = get_teams_and_projects_for_user("admin@tfg.com", "admin")
    
    assert len(res["teams"]) == 1
    assert res["teams"][0]["id"] == 1
    # Verificamos que no se haya llamado a .eq() para admin
    assert mock_supabase.table().select().eq.called is False


@patch("backend.services.permissions_service.get_supabase_client")
def test_get_teams_and_projects_for_user_manager_returns_only_managed(mock_client):
    """5. Test RBAC: Manager solo recibe entidades bajo su responsabilidad directa."""
    mock_supabase = MagicMock()
    mock_client.return_value = mock_supabase
    mock_supabase.table().select().eq().execute.return_value.data = [{"id": 2, "name": "Local Team"}]
    
    res = get_teams_and_projects_for_user("manager@tfg.com", "manager")
    
    assert len(res["teams"]) == 1
    assert res["teams"][0]["name"] == "Local Team"
    # Verificamos que se haya filtrado tanto en equipos como en proyectos
    mock_supabase.table().select().eq.assert_any_call("manager_email", "manager@tfg.com")
    mock_supabase.table().select().eq.assert_any_call("owner_email", "manager@tfg.com")


def test_find_best_project():
    """6. Test de find_best_project() (Algoritmo de contexto y Case-Insensitivity)."""
    all_projects = [
        {"id": 10, "members": ["ana@tfg.com", "carlos@tfg.com"]},
    ]
    
    # Caso 1: Asignación exitosa (Case-Insensitive)
    assert find_best_project(["Ana@tfg.com", "CARLOS@tfg.com"], all_projects) == 10
    
    # Caso 2: Miembro fuera del proyecto
    assert find_best_project(["ana@tfg.com", "desconocido@tfg.com"], all_projects) is None
