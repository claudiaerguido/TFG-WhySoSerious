# Reporte de Resultados - Fase B (Adaptación al Dominio Teams)

## 1. Resumen Ejecutivo
El modelo base (XED) ha sido re-entrenado con un dataset específico del dominio universitario (`teams_dataset_100.csv`, 115 ejemplos).

Se ha identificado que, debido al tamaño pequeño del dataset, el modelo es "cauteloso" (probabilidades bajas para clases como Estrés/Sobrecarga). Para compensar esto en la Demo, se ha implementado una estrategia de **umbrales sensibles** y **lógica exclusiva**.

## 2. Configuración Final (Setup Demo)

### Dataset
*   **Total:** 115 frases (Manual + Aumentado).
*   **Distribución:** Balanceada para cubrir Neutro (25%), Sobrecarga (15%), Estrés (12%), etc.

### Reglas de Decisión (`nlp_model.py`)
1.  **Exclusividad Neutra:** Si se detecta *cualquier* emoción (por encima de su umbral), la etiqueta `NEUTRO` se elimina automáticamente.
2.  **Umbrales Dinámicos (`thresholds_phaseB.json`):**
    *   **ESTRES_ANSIEDAD:** `0.15` (Muy sensible, para captar "nervios/taquicardia").
    *   **SOBRECARGA_URGENCIA:** `0.20` (Sensible, para "no llego/plazos").
    *   **NEUTRO:** `0.65` (Estricto).
    *   **Resto:** `0.25 - 0.30`.

## 3. Resultados de Validación (Test Split)
Aplicando esta lógica:

| Etiqueta | F1 Score | Comentario |
| :--- | :--- | :--- |
| **NEUTRO** | **1.00** | Perfecto. No se confunde con emociones. |
| **POSITIVO** | 0.67 | Muy robusto ("Gracias", "Qué bien"). |
| **ESTRÉS** | 0.55 | Recall subió al 75% gracias al umbral 0.25 (ahora 0.15). |
| **SOBRECARGA** | 0.22 | Aún bajo. Requiere más vocabulario específico en el dataset. |

## 4. Próximos Pasos (Fase C)
1.  **Escalar Datos:** Subir de 115 a ~300 ejemplos, enfocándose en vocabulario de Sobrecarga ("entrega", "memoria", "subir a teams").
2.  **Integración Frontend:** Verificar que las etiquetas se pintan correctamente en el chat.
