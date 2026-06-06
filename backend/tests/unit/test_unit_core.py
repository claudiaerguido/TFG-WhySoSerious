# Tests del motor de riesgo (Pearson), semaforización, permisos RBAC y asignación de proyecto.
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from backend.logic.risk_model import _risk_level, compute_pearson_msg_risk
from backend.services.permissions_service import get_teams_and_projects_for_user
from backend.scheduler_tasks import find_best_project


def test_risk_level_thresholds():
    """
    REQ: RF11 (Indicador simple de riesgo).
    DEFINICIÓN: El sistema debe categorizar el riesgo en niveles visuales (semaforización).
    VALIDACIÓN: Los valores numéricos se asignan a Verde, Amarillo y Rojo según los umbrales definidos.
    """
    assert _risk_level(15.0) == "Verde"
    assert _risk_level(25.0) == "Amarillo"
    assert _risk_level(40.0) == "Rojo"


def test_compute_pearson_msg_risk_valid():
    """
    REQ: RF10 (Detectar tono e inferir señales).
    DEFINICIÓN: El sistema debe procesar las métricas de NLP para calcular un indicador de riesgo.
    VALIDACIÓN: El motor Pearson genera puntuaciones normalizadas en [0, 1] y ordena correctamente los mensajes por intensidad.
    """
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
    """
    REQ: RF10 (Detectar tono e inferir señales).
    DEFINICIÓN: Robustez del motor ante falta de varianza estadística.
    VALIDACIÓN: Cuando no hay varianza para calcular Pearson, el sistema cae al fallback de risk_base en vez de producir un resultado inválido.
    """
    data = {
        "estres_ansiedad": [0.5, 0.5, 0.5], 
        "enfado_irritacion": [0.2, 0.2, 0.2]
    }
    df = pd.DataFrame(data)
    
    risk_series = compute_pearson_msg_risk(df)
    
    assert len(risk_series) == 3
    # El fallback actual devuelve `risk_base`, es decir, la máxima señal negativa
    # tras aplicar la calibración operativa del modelo.
    assert all(x == pytest.approx(0.5) for x in risk_series)


@patch("backend.services.permissions_service.get_supabase_client")
def test_get_teams_and_projects_for_user_admin_returns_all(mock_client):
    """
    REQ: RF06 (Visibilidad ajustada al ámbito de responsabilidad).
    DEFINICIÓN: El administrador debe tener visibilidad total de la organización.
    VALIDACIÓN: Para un rol 'admin', la consulta no aplica filtros por email — devuelve todos los equipos y proyectos.
    """
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
    """
    REQ: RF06 (Visibilidad ajustada al ámbito de responsabilidad).
    DEFINICIÓN: Los responsables (managers) solo ven datos de sus equipos/proyectos.
    VALIDACIÓN: La lógica de permisos aplica filtros por manager_email y owner_email para limitar la visibilidad al ámbito del manager.
    """
    mock_supabase = MagicMock()
    mock_client.return_value = mock_supabase
    mock_supabase.table().select().eq().execute.return_value.data = [
        {"team_id": 2, "teams": {"name": "Local Team"}}
    ]

    res = get_teams_and_projects_for_user("manager@tfg.com", "manager")

    assert len(res["teams"]) == 1
    assert res["teams"][0]["name"] == "Local Team"
    mock_supabase.table().select().eq.assert_any_call("manager_email", "manager@tfg.com")
    mock_supabase.table().select().eq.assert_any_call("owner_email", "manager@tfg.com")


def test_find_best_project():
    """
    REQ: RF04 y RF19 (Parcial).
    DEFINICIÓN: El sistema debe contextualizar los mensajes en el proyecto correspondiente durante el procesamiento automático.
    VALIDACIÓN: El algoritmo asigna el proyecto correcto cuando los miembros del chat son un subconjunto del proyecto, y devuelve None si no hay coincidencia.
    """
    all_projects = [
        {"id": 10, "members": ["ana@tfg.com", "carlos@tfg.com"]},
    ]
    
    # Caso 1: Asignación exitosa (Case-Insensitive)
    assert find_best_project(["Ana@tfg.com", "CARLOS@tfg.com"], all_projects) == 10
    
    # Caso 2: Miembro fuera del proyecto
    assert find_best_project(["ana@tfg.com", "desconocido@tfg.com"], all_projects) is None
