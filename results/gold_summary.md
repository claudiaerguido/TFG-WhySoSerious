# Informe de Evaluación del Modelo (Gold Set)

**Dataset:** `../data/teams_goldset_120.csv`
**Muestras Totales:** 120

## 1. Desempeño por Clase
| Etiqueta | Precisión | Recall | F1-Score | Soporte |
|---|---|---|---|---|
| TRISTEZA | 0.278 | 1.000 | 0.435 | 5.0 |
| ESTRES_ANSIEDAD | 0.710 | 0.733 | 0.721 | 30.0 |
| ENFADO_IRRITACION | 0.286 | 0.400 | 0.333 | 5.0 |
| SOBRECARGA_URGENCIA | 0.600 | 0.800 | 0.686 | 30.0 |
| CANSANCIO_FATIGA | 0.778 | 0.467 | 0.583 | 15.0 |
| POSITIVO_ALIVIO | 1.000 | 1.000 | 1.000 | 5.0 |
| NEUTRO | 0.900 | 0.900 | 0.900 | 30.0 |
| **MICRO AVG** | 0.657 | 0.767 | 0.708 | 120.0 |
| **MACRO AVG** | 0.650 | 0.757 | 0.665 | 120.0 |

## 2. Análisis de Errores Críticos
### ⚠️ Falsos Positivos: Sobrecarga (Alarmas Injustificadas)
- `Cuando podáis, echad un ojo a la documentación y me decís.` (Prob: 0.612) -> Real: ['NEUTRO']
- `Tengo que actualizar las dependencias, pero lo haré más adelante.` (Prob: 0.373) -> Real: ['NEUTRO']
- `Me tiembla la mano al escribir y estoy muy tenso.` (Prob: 0.960) -> Real: ['ESTRES_ANSIEDAD']
- `No puedo dejar de pensar en si lo voy a hacer mal.` (Prob: 0.988) -> Real: ['ESTRES_ANSIEDAD']
- `Me sudan las manos solo de abrir el documento.` (Prob: 0.778) -> Real: ['ESTRES_ANSIEDAD']
- `Me bloqueo y me quedo mirando la pantalla sin avanzar.` (Prob: 0.906) -> Real: ['ESTRES_ANSIEDAD']
- `Me siento a punto de explotar de los nervios.` (Prob: 0.993) -> Real: ['ESTRES_ANSIEDAD']
- `Cada notificación me dispara la ansiedad.` (Prob: 0.452) -> Real: ['ESTRES_ANSIEDAD']
- `Me mareo un poco del estrés; necesito parar.` (Prob: 0.734) -> Real: ['ESTRES_ANSIEDAD']
- `No he descansado nada y estoy funcionando a medias.` (Prob: 0.789) -> Real: ['CANSANCIO_FATIGA']

### ❌ Falsos Negativos: Sobrecarga (Riesgos No Detectados)
- `Queda por integrar y el profesor lo revisa mañana a primera hora.` (Prob: 0.006) -> Pred: ['NEUTRO']
- `Se nos ha caído el servidor justo antes de subirlo.` (Prob: 0.004) -> Pred: ['ENFADO_IRRITACION']
- `Voy tarde con el informe y la reunión es en 10 minutos.` (Prob: 0.007) -> Pred: ['NEUTRO']
- `Si hoy no lo cerramos, suspendemos seguro.` (Prob: 0.020) -> Pred: ['TRISTEZA']
- `Esto tiene máxima prioridad; todo lo demás puede esperar.` (Prob: 0.006) -> Pred: ['ENFADO_IRRITACION']
- `El PR es crítico y sin él no podemos continuar.` (Prob: 0.047) -> Pred: ['ESTRES_ANSIEDAD']

## 3. Análisis de Patrones Lingüísticos
| Grupo de Patrones | Conteo de Errores Específicos |
|---|---|
| **Neutros Adversarios** (pendiente, revisar...) | FP Sobrecarga: **0** |
| **Sobrecarga Explícita** (urgente, plazo...) | FN Sobrecarga: **1** |

## 4. Validación de KPIs (Criterios de Aceptación)
- ✅ **KPI A:** Robustez ante 'Neutros Adversarios' (FP <= 2). Actual: 0
- ✅ **KPI B:** Sensibilidad en Sobrecarga (Recall >= 0.8). Actual: 0.800
