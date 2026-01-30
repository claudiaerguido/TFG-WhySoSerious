# Reporte de Resultados - Fase A (Modelo XED Mixto)

## 1. Resumen de Métricas (Test XED Mix)
Métricas calculadas sobre el split de validación (10%) incluyendo ejemplos emocionales y neutros.

| Métrica | Valor | Comentario |
| :--- | :--- | :--- |
| **F1 Micro** | **0.58** | Validado en escenario realista (con neutros). |
| **F1 Macro** | 0.36 | Mejorado gracias a la reparación de la clase Neutro. |

### Desglose por Etiqueta (Threshold 0.5)

| Etiqueta | F1 | Precision | Recall | Análisis |
| :--- | :--- | :--- | :--- | :--- |
| **ENFADO** | 0.64 | 0.72 | 0.58 | Sigue siendo sólido. |
| **POSITIVO** | **0.71** | 0.85 | 0.61 | Muy preciso. |
| **TRISTEZA** | 0.42 | 0.72 | 0.30 | Alta precisión, bajo recall (necesita threshold bajo). |
| **ESTRES** | 0.18 | 0.73 | 0.10 | **Atención:** A 0.5 pierde mucho. Ver análisis de umbral. |
| **NEUTRO** | **0.59** | 0.49 | 0.74 | **¡REPARADO!** Recall alto (0.74). Tiende a sobre-predicir (Prec 0.49), corregible en Fase B. |

### 🔍 Análisis de Umbrales (Calibración)
Se realizó un barrido de 0.1 a 0.9 para optimizar F1.

*   **ESTRES:** Umbral **0.2** es óptimo.
    *   F1 sube de 0.18 -> **0.51**.
    *   Recall sube de 0.10 -> **0.58**.
    *   *Acción Fase B: Usar umbral específico relajado para Estrés/Ansiedad.*

*   **NEUTRO:** Umbral **0.7** mejora precisión.
    *   A 0.5: F1 0.59 (Prec 0.49).
    *   A 0.7: F1 **0.62** (Prec 0.65).
    *   *Acción Fase B: Filtrar neutros "débiles" subiendo el umbral.*

---

## 2. Análisis Mini-Test (Dataset Teams 25)

Evaluación cualitativa sobre 25 frases del dominio universitario. Se evalúan solo las 5 etiquetas activas.

### ✅ Aciertos Clave
1. **Tristeza Detectada**: 
   - *"Me he quedado sin ganas de nada..."* -> **TRISTEZA** (Match).
2. **Positivo Claro**: 
   - *"Buen trabajo equipo, la presentación ha salido genial..."* -> **POSITIVO** (Match).
3. **Respeto a Etiquetas No Entrenadas**: 
   - *"Me faltan un montón de cosas..."* (Gold: Sobrecarga) -> **Predicción: Ninguna (0,0,0,0,0)**. 
   - **Éxito**: El modelo no alucina emociones cuando es pura sobrecarga. Esto facilita la Fase B.

### ⚠️ Errores y Retos (Para Fase B)
1. **Confusión Positivo/Neutro**:
   - *"Ok, lo reviso ahora..."* -> Pred: **POSITIVO** (Gold: Neutro).
   - Palabras como "Ok", "Gracias" activan POSITIVO. Necesitamos subir el umbral o entrenar Neutro con frases de Teams.
2. **Sarcasmo**:
   - *"Genial, otra vez han cambiado los requisitos..."* -> Pred: **POSITIVO** (Gold: Enfado).
   - El modelo ve "Genial" y dispara alegría. Requiere fine-tuning contextual.
3. **Recall de Estrés**:
   - *"Estoy muy nervioso con la presentación..."* -> Pred: **Ninguna** (Gold: Estrés).
   - "Nervioso" no fue suficiente para activar el umbral de ESTRES (entrenado con "Fear"). Necesitamos inyectar vocabulario de ansiedad en Fase B.

## 3. Conclusión Fase A
El modelo es **robusto en emociones primarias (Enfado, Alegría, Tristeza)** y seguro (preciso) ya que no suele inventar etiquetas.
Los fallos en Estrés y Neutro son esperados y se corregirán al introducir el dataset nativo de Teams (Fase B).
