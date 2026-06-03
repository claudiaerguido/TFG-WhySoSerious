from .base import NLPModel

class ZeroShotModel(NLPModel):
    def __init__(self):
        # TODO: Implementar carga de modelo Zero-Shot (Nivel 2)
        # ej: pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        pass

    def predict(self, text: str) -> dict:
        # TODO: Implementar lógica de predicción
        raise NotImplementedError("ZeroShotModel no está implementado todavía (Nivel 2).")
