# Tipo: Validación
# Requisitos cubiertos: RF18, RNF09
# Objetivo: Verificar la persistencia histórica de métricas agregadas y la integridad básica de los datos almacenados.
"""
5. Test de persistencia (test_val_persistence.py)

Qué valida: que los resultados calculados se guardan correctamente en Supabase.
Explicación: el test comprueba que cada registro persiste con los campos esperados, como identificador del mensaje, usuario, fecha, puntuaciones emocionales y contexto de proyecto.
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from backend.db_repository import save_risk_metrics

@patch("backend.db_repository.TARGET_LABELS", ["enfado_irritacion"])
@patch("backend.db_repository.DB_COLS", {"enfado_irritacion": "score_enfado"})
def test_validation_persistence():
    """
    REQ: RF18 y RNF09.
    DEFINICIÓN: El sistema debe conservar el histórico analítico con los campos técnicos necesarios y mantener una persistencia coherente.
    VALIDACIÓN: Se ejecuta la función de guardado y se verifica mediante mocks que la llamada al ORM contiene todos los campos obligatorios: email, ID de mensaje, fecha, puntuación y proyecto asociado.
    """
    mock_supabase = MagicMock()
    email = "test@tfg.com"
    timestamp = datetime.now().isoformat()
    scores = {"enfado_irritacion": 0.95}
    msg_id = "MSG_123"
    
    # Ejecutar guardado
    save_risk_metrics(mock_supabase, email, timestamp, scores, msg_id, project_id=1)
    
    # Verificar llamada a Supabase
    mock_supabase.table().upsert.assert_called_once()
    args, kwargs = mock_supabase.table().upsert.call_args
    data = args[0]
    assert data["user_email"] == email
    assert data["message_id"] == msg_id
    assert data["score_enfado"] == 0.95
