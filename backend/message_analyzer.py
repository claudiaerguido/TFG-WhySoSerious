import nlp_model

def analyze_message(text):
    """
    Analiza un mensaje usando el modelo NLP cargado.
    Devuelve None si el texto es muy corto o irrelevante.
    """
    if not text or len(text.strip()) < 4:
        return None
        
    try:
        # Usamos la predicción final (multilabel)
        result = nlp_model.final_predict(text)
        return result
    except Exception as e:
        print(f"Error analizando '{text[:20]}...': {e}")
        return None
