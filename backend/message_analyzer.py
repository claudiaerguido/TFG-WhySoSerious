import nlp_model

def analyze_message(text):
    """
    Analiza un mensaje usando el modelo NLP cargado.
    Devuelve None si el texto es muy corto o irrelevante.
    """
    if not text or len(text.strip()) < 4:
        return None
        
    try:
        if nlp_model._model is None:
            return nlp_model.baseline_predict(text)
        return nlp_model.final_predict(text)
    except Exception as e:
        print(f"Error analizando '{text[:20]}...': {e}")
        return None
