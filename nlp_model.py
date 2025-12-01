from transformers import pipeline

# Cargamos el modelo solo una vez (global)
_classifier = pipeline(
    "sentiment-analysis",
    model="nlptown/bert-base-multilingual-uncased-sentiment",
    device=-1  # Forzamos CPU para evitar errores en Mac/MPS
)

def predict(text: str):
    """
    Devuelve la predicción del modelo para un solo texto.
    """
    result = _classifier(text)[0]
    return {
        "label": result["label"],
        "score": float(result["score"])
    }

if __name__ == "__main__":
    # Pequeña prueba rápida
    ejemplo = "Estoy muy cansado del trabajo."
    salida = predict(ejemplo)
    print(f"Texto: {ejemplo}")
    print(f"Resultado: {salida}")