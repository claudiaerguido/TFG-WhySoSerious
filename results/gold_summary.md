# Informe de Evaluación del Modelo (Gold Set)

**Dataset:** `../data/teams_goldset_120.csv`
**Muestras Totales:** 120

## 1. Desempeño por Clase
| Etiqueta | Precisión | Recall | F1-Score | Soporte |
|---|---|---|---|---|
| TRISTEZA | 0.500 | 0.800 | 0.615 | 5.0 |
| ESTRES_ANSIEDAD | 0.727 | 0.533 | 0.615 | 30.0 |
| ENFADO_IRRITACION | 0.667 | 0.800 | 0.727 | 5.0 |
| SOBRECARGA_URGENCIA | 0.591 | 0.867 | 0.703 | 30.0 |
| CANSANCIO_FATIGA | 0.529 | 0.600 | 0.562 | 15.0 |
| POSITIVO_ALIVIO | 0.600 | 0.600 | 0.600 | 5.0 |
| NEUTRO | 0.800 | 0.933 | 0.862 | 30.0 |
| **MICRO AVG** | 0.657 | 0.750 | 0.700 | 120.0 |
| **MACRO AVG** | 0.631 | 0.733 | 0.669 | 120.0 |

## 2. Análisis de Errores Críticos
### ⚠️ Falsos Positivos: Sobrecarga (Alarmas Injustificadas)
- `Actualizo la bibliografía esta semana y lo subo después.` (Prob: 0.986) -> Real: ['NEUTRO']
- `Voy completando la sección de resultados y lo subo al final.` (Prob: 0.993) -> Real: ['NEUTRO']
- `Estoy con la cabeza dando vueltas y no paro.` (Prob: 0.995) -> Real: ['ESTRES_ANSIEDAD']
- `Estoy en alerta constante y me agota.` (Prob: 0.981) -> Real: ['ESTRES_ANSIEDAD']
- `Me bloqueo y me quedo mirando la pantalla sin avanzar.` (Prob: 0.995) -> Real: ['ESTRES_ANSIEDAD']
- `No consigo concentrarme por la preocupación.` (Prob: 0.517) -> Real: ['ESTRES_ANSIEDAD']
- `Siento presión en el pecho y la mente a mil.` (Prob: 0.952) -> Real: ['ESTRES_ANSIEDAD']
- `Me está entrando pánico con la defensa.` (Prob: 0.995) -> Real: ['ESTRES_ANSIEDAD']
- `Tengo taquicardia y necesito calmarme ya.` (Prob: 0.983) -> Real: ['ESTRES_ANSIEDAD']
- `Cada notificación me dispara la ansiedad.` (Prob: 0.437) -> Real: ['ESTRES_ANSIEDAD']

### ❌ Falsos Negativos: Sobrecarga (Riesgos No Detectados)
- `Queda por integrar y el profesor lo revisa mañana a primera hora.` (Prob: 0.181) -> Pred: ['NEUTRO']
- `El test de integración sigue rojo y no queda tiempo.` (Prob: 0.064) -> Pred: ['NEUTRO']
- `Estoy apagando fuegos todo el día; no avanzo.` (Prob: 0.015) -> Pred: ['CANSANCIO_FATIGA']
- `Queda por hacer la validación final y el plazo es ya.` (Prob: 0.172) -> Pred: ['NEUTRO']

## 3. Análisis de Patrones Lingüísticos
| Grupo de Patrones | Conteo de Errores Específicos |
|---|---|
| **Neutros Adversarios** (pendiente, revisar...) | FP Sobrecarga: **0** |
| **Sobrecarga Explícita** (urgente, plazo...) | FN Sobrecarga: **2** |

## 4. Validación de KPIs (Criterios de Aceptación)
- ✅ **KPI A:** Robustez ante 'Neutros Adversarios' (FP <= 2). Actual: 0
- ✅ **KPI B:** Sensibilidad en Sobrecarga (Recall >= 0.8). Actual: 0.867
