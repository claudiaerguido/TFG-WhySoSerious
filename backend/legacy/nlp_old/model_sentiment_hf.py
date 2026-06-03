from transformers import pipeline
from .base import NLPModel

# Singleton cache for the pipeline
_SENTIMENT_PIPELINE = None

def get_sentiment_pipeline():
    global _SENTIMENT_PIPELINE
    if _SENTIMENT_PIPELINE is None:
        print("Loading SentimentHFModel pipeline (tabularisai/multilingual-sentiment-analysis)...")
        # device=-1 forzamos CPU
        _SENTIMENT_PIPELINE = pipeline(
            "text-classification",
            model="tabularisai/multilingual-sentiment-analysis",
            device=-1
        )
    return _SENTIMENT_PIPELINE

class SentimentHFModel(NLPModel):
    def __init__(self):
        self.pipeline = get_sentiment_pipeline()
        self.model_name = "sentiment_hf"

    def predict(self, text: str) -> dict:
        results = self.pipeline(text)
        result = results[0]  # Pipeline returns a list
        
        label_raw = result['label']
        score = float(result['score'])

        # Mapping: label_raw -> risk_score (0..100)
        label_lower = label_raw.lower()
        
        risk_score = 50
        map_label = label_raw
        explanation = f"Detectado: {label_raw}"

        # Model specific mapping for 'tabularisai/multilingual-sentiment-analysis'
        if "5 stars" in label_lower or "very positive" in label_lower:
            map_label = "Very Positive"
            risk_score = 10
        elif "4 stars" in label_lower or "positive" in label_lower:
            map_label = "Positive"
            risk_score = 25
        elif "3 stars" in label_lower or "neutral" in label_lower:
            map_label = "Neutral"
            risk_score = 50
        elif "2 stars" in label_lower or "negative" in label_lower:
            map_label = "Negative"
            risk_score = 75
        elif "1 star" in label_lower or "very negative" in label_lower:
            map_label = "Very Negative"
            risk_score = 90
        
        # Generic Fallback
        elif "positive" in label_lower:
            map_label = "Positive"
            risk_score = 25
        elif "negative" in label_lower:
            map_label = "Negative"
            risk_score = 75
        elif "neutral" in label_lower:
            map_label = "Neutral"
            risk_score = 50

        return {
            "model_name": self.model_name,
            "label": map_label,
            "confidence": score,
            "risk_score": risk_score,
            "explanation": explanation
        }
