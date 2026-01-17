from .base import NLPModel

class FineTunedModel(NLPModel):
    def __init__(self):
        # TODO: Cargar pesos del modelo fine-tuned (Nivel 3)
        pass

    def predict(self, text: str) -> dict:
        # TODO: Implementar lógica de predicción con modelo propio
        raise NotImplementedError("FineTunedModel no está implementado todavía (Nivel 3).")
