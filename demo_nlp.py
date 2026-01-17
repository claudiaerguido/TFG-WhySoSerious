import argparse
from nlp import SentimentHFModel

def run_demo():
    print("=== Iniciando Demo NLP Level 1 ===")
    
    # 1. Carga del modelo
    print("Instanciando SentimentHFModel...")
    model = SentimentHFModel()
    
    # 2. Frases de prueba variadas (ES/EN)
    phrases = [
        "Estoy muy contento con el servicio, es excelente.",         # Very Positive
        "Esto es una basura, no funciona nada.",                     # Very Negative
        "El producto llegó bien, correcto sin más.",                 # Neutral/Positive
        "No tengo una opinión fuerte al respecto.",                  # Neutral
        "I absolutely love this feature! It's amazing.",             # Very Positive (EN)
        "This is terrible, I want a refund now."                     # Very Negative (EN)
    ]
    
    print(f"\nProbando {len(phrases)} frases con modelo: {model.model_name}\n")
    
    for text in phrases:
        prediction = model.predict(text)
        print(f"Texto: '{text}'")
        print(f"  -> Label        : {prediction['label']}")
        print(f"  -> Risk Score   : {prediction['risk_score']}")
        print(f"  -> Confidence   : {prediction['confidence']:.4f}")
        print(f"  -> Explanation  : {prediction['explanation']}")
        print("-" * 50)

if __name__ == "__main__":
    run_demo()
