# Informe de Evaluación del Modelo (Gold Set)

**Dataset:** `../../data/teams_goldset_120.csv`
**Muestras Totales:** 173

## 1. Desempeño por Clase
| Etiqueta | Precisión | Recall | F1-Score | Soporte |
|---|---|---|---|---|
| TRISTEZA | 0.000 | 0.000 | 0.000 | 0.0 |
| ESTRES_ANSIEDAD | 0.810 | 0.791 | 0.800 | 43.0 |
| ENFADO_IRRITACION | 0.812 | 0.929 | 0.867 | 14.0 |
| SOBRECARGA_URGENCIA | 0.853 | 0.725 | 0.784 | 40.0 |
| CANSANCIO_FATIGA | 0.741 | 0.800 | 0.769 | 25.0 |
| POSITIVO_ALIVIO | 0.000 | 0.000 | 0.000 | 0.0 |
| NEUTRO | 0.878 | 0.878 | 0.878 | 49.0 |
| **MICRO AVG** | 0.827 | 0.813 | 0.820 | 171.0 |
| **MACRO AVG** | 0.585 | 0.589 | 0.585 | 171.0 |

## 2. Análisis de Errores Críticos
### Falsos Positivos: Sobrecarga (Alarmas Injustificadas)
- `Necesitamos un fix de emergencia antes de la demo.` (Prob: 0.922) -> Real: ['NEUTRO']
- `Estoy con el pulso a mil y no sé cómo bajarlo.` (Prob: 0.983) -> Real: ['ESTRES_ANSIEDAD']
- `tengo una carga en el coche que pesa muchísimo` (Prob: 0.993) -> Real: ['NEUTRO']
- `tengo q sacar el informe la presentacion y el codigo todo para hoy` (Prob: 0.996) -> Real: ['NEUTRO']
- `estoy molido y encima me revienta q nadie eche una mano` (Prob: 0.796) -> Real: ['ENFADO_IRRITACION', 'CANSANCIO_FATIGA']

### Falsos Negativos: Sobrecarga (Riesgos No Detectados)
- `Esto es bloqueante: si no mergeamos ya, no sale la entrega.` (Prob: 0.006) -> Pred: ['ENFADO_IRRITACION']
- `Nos han cambiado los requisitos y la entrega es esta noche.` (Prob: 0.121) -> Pred: []
- `Si no lo arreglamos ahora, se rompe producción.` (Prob: 0.002) -> Pred: ['NEUTRO']
- `Queda por integrar y el profesor lo revisa mañana a primera hora.` (Prob: 0.003) -> Pred: ['NEUTRO']
- `El test de integración sigue rojo y no queda tiempo.` (Prob: 0.013) -> Pred: ['NEUTRO']
- `Se nos ha caído el servidor justo antes de subirlo.` (Prob: 0.002) -> Pred: []
- `Si hoy no lo cerramos, suspendemos seguro.` (Prob: 0.130) -> Pred: ['ESTRES_ANSIEDAD']
- `Estoy apagando fuegos todo el día; no avanzo.` (Prob: 0.048) -> Pred: ['ESTRES_ANSIEDAD']
- `es una sobrecarga de tareas brutal` (Prob: 0.026) -> Pred: []
- `plazos imposibles otra vez asi no se puede trabajar` (Prob: 0.039) -> Pred: ['ENFADO_IRRITACION']

## 3. Análisis de Patrones Lingüísticos
| Grupo de Patrones | Conteo de Errores Específicos |
|---|---|
| **Neutros Adversarios** (pendiente, revisar...) | FP Sobrecarga: **0** |
| **Sobrecarga Explícita** (urgente, plazo...) | FN Sobrecarga: **4** |

## 4. Validación de KPIs (Criterios de Aceptación)
- OK **KPI A:** Robustez ante 'Neutros Adversarios' (FP <= 2). Actual: 0
- NO OK **KPI B:** Sensibilidad en Sobrecarga (Recall >= 0.8). Actual: 0.725
