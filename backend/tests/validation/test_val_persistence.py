# Tipo: Validación | Requisitos: RF18, RNF09
# Objetivo: Comprobar que save_risk_metrics construye correctamente el registro antes de
# persistirlo en Supabase — los campos obligatorios (email, message_id, puntuación, proyecto)
# deben estar presentes y mapeados a las columnas correctas de la base de datos.
from datetime import datetime
from unittest.mock import patch, MagicMock
from backend.db_repository import save_risk_metrics

@patch("backend.db_repository.TARGET_LABELS", ["enfado_irritacion"])
@patch("backend.db_repository.DB_COLS", {"enfado_irritacion": "score_enfado"})
def test_validation_persistence():
    """
    REQ: RF18 y RNF09.
    DEFINICIÓN: El sistema debe conservar el histórico analítico con los campos técnicos necesarios y mantener una persistencia coherente.
    VALIDACIÓN: La llamada a upsert incluye user_email, message_id, la puntuación mapeada al nombre de columna correcto y el project_id.
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
