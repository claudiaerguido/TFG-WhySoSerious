from transformers import pipeline

def load_classifier():
    # Modelo multilenguaje que entiende algo de español también
    classifier = pipeline(
        "sentiment-analysis",
        model="nlptown/bert-base-multilingual-uncased-sentiment"
    )
    return classifier

def main():
    classifier = load_classifier()

    textos = [
        "Estoy agotado del trabajo y del equipo.",
        "Hoy ha sido un día genial, el proyecto va muy bien.",
        "Estoy empezando a sentirme un poco quemado.",
        "Todo va normal, ni bien ni mal."
    ]

    for t in textos:
        result = classifier(t)[0]  # primer resultado
        label = result["label"]
        score = result["score"]
        print(f"Texto: {t}")
        print(f"  → Predicción: {label} (confianza: {score:.4f})")
        print("-" * 50)

if __name__ == "__main__":
    main()
