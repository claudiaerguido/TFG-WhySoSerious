import pytest
from nlp import SentimentHFModel

@pytest.fixture(scope="module")
def nlp_model():
    """Fixture para cargar el modelo una sola vez para todos los tests del módulo."""
    print("\nCargando modelo NLP para tests...")
    return SentimentHFModel()

@pytest.mark.slow
def test_sentiment_prediction_structure(nlp_model):
    """Verifica que la respuesta tenga todas las claves requeridas."""
    text = "Esto es una prueba de funcionamiento."
    result = nlp_model.predict(text)
    
    expected_keys = ["model_name", "label", "confidence", "risk_score", "explanation"]
    for key in expected_keys:
        assert key in result, f"Falta la clave {key} en la respuesta"

@pytest.mark.slow
def test_sentiment_ranges(nlp_model):
    """Verifica que los valores numéricos estén en rangos válidos."""
    text = "Todo va genial."
    result = nlp_model.predict(text)
    
    # Confidence 0..1
    assert 0.0 <= result["confidence"] <= 1.0, "Confidence fuera de rango [0, 1]"
    
    # Risk Score 0..100
    assert 0 <= result["risk_score"] <= 100, "Risk Score fuera de rango [0, 100]"

@pytest.mark.slow
def test_label_not_empty(nlp_model):
    """Verifica que la label no esté vacía."""
    text = "Texto neutral."
    result = nlp_model.predict(text)
    
    assert result["label"] is not None
    assert isinstance(result["label"], str)
    assert len(result["label"]) > 0
