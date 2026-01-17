from abc import ABC, abstractmethod

class NLPModel(ABC):
    """
    Base abstract class for all NLP models in the project.
    """
    
    @abstractmethod
    def predict(self, text: str) -> dict:
        """
        Input: raw text string.
        Output: dict with keys {label, confidence, risk_score, explanation, model_name}
        """
        pass
