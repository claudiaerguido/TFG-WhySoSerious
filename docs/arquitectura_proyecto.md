
# Estructura del Proyecto y Explicación de Archivos

Este documento detalla los componentes clave del sistema de detección de emociones desarrollado para el TFG.

---

## 1. Entrenamiento y Mejora del Modelo (Training)

### `train_teams.py` (Entrenamiento Base - Fase B)
*   **Función:** Es el script principal que entrenó el modelo base (`final_teams_b1`).
*   **Qué hace:**
    *   Carga el modelo pre-entrenado (por ejemplo, `Mistral-Small-Instruct` o `PlanTL-GOB-ES` adaptado).
    *   Lee el dataset de entrenamiento base (ej: `teams_es_augmented_500.csv` o `teams_train_manual.csv`).
    *   Implementa **Oversampling** (duplica ejemplos de clases minoritarias como Sobrecarga/Fatiga) para equilibrar el aprendizaje.
    *   Realiza el entrenamiento supervisado (Fine-tuning) optimizando la métrica F1-Micro.
    *   **Importancia:** Sentó las bases del conocimiento del modelo sobre el dominio de Teams.

### `train_polish.py` (Refinamiento Final)
*   **Función:** Script de "pulido" (Fine-tuning ligero) que usamos al final.
*   **Qué hace:**
    *   Parte del modelo ya entrenado por `train_teams.py` (para no empezar de cero).
    *   Entrena solo unas pocas épocas (3-5) con una tasa de aprendizaje muy baja (`2e-5`).
    *   Incorpora los **ejemplos manuales** (Correcciones de usuario: "Voy tarde" = Sobrecarga, "Pendiente" = Neutro).
    *   **Importancia:** Fue clave para alcanzar el **80% de Recall** en Sobrecarga y eliminar falsos positivos en neutros sin destruir el conocimiento previo.

---

## 2. Inferencia y Lógica de Negocio (El "Cerebro")

### `nlp_model.py`
*   **Función:** Es el núcleo inteligente del sistema. Define CÓMO se hacen las predicciones.
*   **Componentes Clave:**
    *   **`baseline_predict`**: Ejecuta el modelo original de Hugging Face (estrellas) mediante `pipeline` para comparativa.
    *   **`final_predict`**: Ejecuta nuestro modelo de emociones final.
    *   **Lógica Híbrida**:
        *   **Temperature Scaling**: Suaviza las probabilidades extremas.
        *   **Umbrales Dinámicos**: Aplica los cortes definidos en el JSON.
        *   **Fallback a Neutro**: Si ninguna emoción supera su umbral, devuelve "Neutro (Por defecto)" para evitar "alucinaciones".
        *   **Neutral Gating**: Si la probabilidad de Neutro es muy alta (>0.75), suprime detecciones de emociones débiles (<0.45) para reducir ruido.

### `thresholds_phaseB.json`
*   **Función:** Archivo de configuración "en caliente".
*   **Qué contiene:** Los valores límite para cada emoción (ej: `SOBRECARGA: 0.35`, `ESTRES: 0.25`).
*   **Importancia:** Permite ajustar la sensibilidad ("agresividad") del sistema en producción sin tener que volver a entrenar ni tocar código Python.

---

## 3. Interfaz y Conexión (Backend API)

### `main.py`
*   **Función:** Servidor Web (FastAPI) que expone el modelo al mundo.
*   **Qué hace:**
    *   Levanta un servicio HTTP en el puerto 8000.
    *   Recibe las peticiones POST en `/predict`.
    *   Lee el parámetro `model="baseline"` o `model="final"` y enruta la petición a la función adecuada de `nlp_model.py`.
    *   Devuelve la respuesta JSON estructurada para que la entienda el Frontend o el Bot de Teams.

---

## 4. Validación y Calidad (Testing)

### `evaluate_goldset.py`
*   **Función:** El "Examen Final" automatizado.
*   **Qué hace:**
    *   Carga el **Gold Set** (`teams_goldset_120.csv`), que es un conjunto de frases "intocables" etiquetadas verazmente por humanos.
    *   Pasa cada frase por `nlp_model.py` (simulando producción real con lógica de umbrales).
    *   Calcula métricas rigurosas (Precision, Recall, F1).
    *   Verifica reglas de negocio automática ("¿Se colaron neutros como Sobrecarga?", "¿Detectamos al menos el 80% de urgencias?").
    *   Genera el reporte `gold_summary.md`.

---

## Resumen del Flujo de Datos

1.  **Datos** (`csv`) -> **Entrenamiento** (`train_teams.py` -> `train_polish.py`) -> **Modelo Final** (`models/final_teams`).
2.  **Usuario** -> **API** (`main.py`) -> **Lógica** (`nlp_model.py` + `thresholds.json`) -> **Predicción**.
3.  **Calidad** -> **Evaluación** (`evaluate_goldset.py`) -> **Reporte de Auditoría**.
