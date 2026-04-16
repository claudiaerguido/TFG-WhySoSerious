# Tipo: Validación
# Requisitos cubiertos: RF07, RF08, RF09, RNF03, RNF04, RNF05
# Objetivo: Verificar el cumplimiento de las políticas de privacidad, minimización de datos y protección frente a reidentificación.

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from backend.db_repository import save_risk_metrics, fetch_metrics_for_users

def test_privacy_minimization_persistence():
    """
    RF07, RNF03: Verifica que NUNCA se persiste el texto original de los mensajes.
    El sistema solo debe guardar el ID del mensaje y las puntuaciones numéricas.
    """
    mock_supabase = MagicMock()
    email = "test@tfg.com"
    scores = {"ENFADO_IRRITACION": 0.5}
    
    # Ejecutamos el guardado
    save_risk_metrics(mock_supabase, email, "2026-04-11T12:00:00Z", scores, "MSG_001")
    
    # Verificamos que los datos enviados a Supabase no contienen ninguna clave de texto
    args, _ = mock_supabase.table().upsert.call_args
    data_persisted = args[0]
    
    # Claves prohibidas (no deben existir en la tabla de métricas)
    prohibited_keys = ["text", "content", "body", "original_text", "message_text"]
    for key in prohibited_keys:
        assert key not in data_persisted, f"ERROR DE PRIVACIDAD: Se intentó persistir el campo sensible '{key}'"
    
    print("✅ Minimización confirmada: No se detectan campos de texto original en el guardado.")

def test_privacy_aggregation_extraction():
    """
    RF08, RNF04: Verifica que la extracción de métricas solo devuelve datos numéricos y técnicos.
    Utiliza los nombres reales de las columnas en Supabase.
    """
    mock_supabase = MagicMock()
    # Simulamos que la BD devuelve columnas reales (según logic/risk_model.py)
    mock_supabase.table().select().in_().gte().execute.return_value.data = [
        {
            "user_email": "u1@tfg.com", 
            "enfado_irritacion": 0.5, 
            "estres_ansiedad": 0.2,
            "message_timestamp": "2026-04-11T12:00:00Z"
        }
    ]
    
    df = fetch_metrics_for_users(mock_supabase, ["u1@tfg.com"], 7)
    
    # Comprobamos que en el DataFrame resultante no hay rastro de contenido textual
    sensitive_columns = ["text", "content", "body", "message_text"]
    for col in sensitive_columns:
        assert col not in df.columns, f"ERROR DE PRIVACIDAD: El DataFrame de métricas expone el campo '{col}'"

def test_privacy_empty_data_handling():
    """
    RNF05 (Parcial): Verifica que el sistema maneja correctamente la ausencia de datos.
    Nota: Actualmente el sistema no aplica un umbral mínimo (ej: >5 mensajes), 
    pero sí bloquea el cálculo si la muestra es nula.
    """
    from backend.services.risk_service import _compute_mean_risk_from_df
    
    # Caso 1: DataFrame con datos
    df_data = pd.DataFrame({"enfado_irritacion": [0.5, 0.6], "estres_ansiedad": [0.1, 0.2]})
    risk = _compute_mean_risk_from_df(df_data)
    assert risk is not None
    
    # Caso 2: DataFrame vacío
    df_empty = pd.DataFrame()
    assert _compute_mean_risk_from_df(df_empty) is None
