# Reporte Fase B.1: Escalado Manual y Refinamiento

## 1. Resumen Ejecutivo
*   **Enfoque:** Se abandonó la generación sintética por un **Escalado Manual** de alta calidad (300 ejemplos totales).
*   **Estrategia:** Oversampling agresivo (5x) para clases débiles (Sobrecarga, Cansancio) + Ajuste de Hiperparámetros (LR 5e-5, 15 Epochs).
*   **Resultado Final:** **F1 Micro 0.74** (Evaluación en Split Manual).
    *   Mejora masiva en clases críticas: Sobrecarga (0.0 -> 0.55), Cansancio (0.0 -> 0.70).
    *   Neutros Trampa gestionados correctamente (Precision Neutro: 0.94).

## 2. Metodología
### Dataset Manual Ampliado
Se crearon manuales 300 ejemplos divididos en 4 Batches focales:
1.  **Batch 1:** Enfado y Sobrecarga explícita.
2.  **Batch 2:** Etiquetas Mixtas (Sobrecarga + Estrés) y Alivio.
3.  **Batch 3:** Síntomas físicos (Estrés) y Burnout (Cansancio).
4.  **Batch 4:** "Neutros Trampa" (frases laborales sin emoción) y casos complejos.

### Configuración del Entrenamiento
*   **Modelo Base:** `final_xed` (Bert Multilingual Fine-tuned en XED).
*   **Oversampling:** Las clases `SOBRECARGA_URGENCIA` y `CANSANCIO_FATIGA` se duplicaron invertidamente (5x) en el dataloader para despertar las neuronas inactivas.
*   **Learning Rate:** Se incrementó a `5e-5` para permitir mayor plasticidad.
*   **Epochs:** 15 (con Early Stopping implícito guardando el mejor modelo).

## 3. Resultados Detallados (Validation Split)

| Etiqueta | F1 Score | Precision | Recall | Análisis |
| :--- | :--- | :--- | :--- | :--- |
| **POSITIVO_ALIVIO** | **1.00** | 1.00 | 1.00 | Detección perfecta ("Funciona", "Gracias"). |
| **NEUTRO** | **0.91** | 0.94 | 0.88 | Gran robustez ante frases técnicas o informativas. |
| **CANSANCIO_FATIGA** | **0.70** | 0.73 | 0.67 | Resuelto el problema de detección nula. |
| **ESTRES_ANSIEDAD** | **0.69** | 0.56 | 0.91 | Muy sensible (alto Recall), detecta casi todo el estrés, a costa de algo de precisión. |
| **TRISTEZA** | **0.67** | 0.73 | 0.62 | Consistente, aunque menos prioritario. |
| **SOBRECARGA_URGENCIA**| **0.55** | 0.43 | 0.75 | **Mejora crítica**. Detecta bien (Recall 0.75) pero a veces confunde con estrés puro. |
| **ENFADO_IRRITACION** | **0.50** | 0.50 | 0.50 | Balanceado, pero mejorable con más ejemplos de "Enfado sutil". |

**Global F1 Micro:** 0.74

## 4. Conclusión y Siguientes Pasos
El modelo ha superado las limitaciones de la Fase B (donde Sobrecarga era invisible). Ahora es un detector robusto y sensible en el dominio Teams académico.

**Acciones Completadas:**
*   [x] Escalado de datos manual.
*   [x] Corrección de bias de neuronas muertas (Oversampling).
*   [x] Validación exitosa (>0.70 F1).
*   [x] Recuperación de espacio en disco (Checkpoints limpiados).

**Recomendación:** Proceder a **Fase C (Integración)** o despliegue, ya que el modelo cumple los requisitos de rendimiento.
