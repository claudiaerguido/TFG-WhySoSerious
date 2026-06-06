# Why So Serious

Sistema de evaluación agregada de riesgo psicosocial en equipos de trabajo a partir de comunicaciones corporativas autorizadas en Microsoft Teams.

Este proyecto se ha desarrollado como Trabajo de Fin de Grado. Su objetivo no es leer ni interpretar conversaciones individuales, sino transformar señales lingüísticas ya existentes en indicadores agregados que ayuden a observar situaciones de sobrecarga, estrés, fatiga o conflicto dentro de equipos y proyectos. La solución combina autenticación corporativa, ingesta controlada mediante Microsoft Graph, inferencia con un modelo transformer fine-tuneado, cálculo de riesgo y visualización web con control de acceso por rol.

---

## Contenido

- [Ejecución para evaluación](#ejecucion-para-evaluacion)
- [Motivación](#motivacion)
- [Arquitectura general](#arquitectura-general)
- [Pipeline NLP](#pipeline-nlp)
- [Motor de riesgo](#motor-de-riesgo)
- [Stack tecnológico](#stack-tecnologico)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Variables de entorno](#variables-de-entorno)
- [Validación y tests](#validacion-y-tests)
- [Entrenamiento del modelo](#entrenamiento-del-modelo)
- [Métricas del modelo](#metricas-del-modelo)
- [Endpoints principales](#endpoints-principales)

---

## Ejecución para evaluación

La forma recomendada de ejecutar el proyecto es mediante Docker Compose. De este modo, el tribunal no necesita instalar manualmente Python ni Node.js; únicamente debe disponer de Docker Desktop, del fichero `backend/.env` facilitado con la entrega y de conexión a Internet durante el primer arranque.

### Arranque con Docker

Desde la raíz del repositorio:

```bash
cd ceu-whysoserious
docker compose up --build
```

La primera ejecución puede tardar varios minutos, ya que se construyen las imágenes del backend y del frontend. Cuando el backend muestre `Application startup complete.`, la aplicación estará lista.

| Servicio | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend | http://localhost:8000 |
| Estado del backend | http://localhost:8000/health |
| Documentación de API | http://localhost:8000/docs |

Para detener la aplicación:

```bash
Ctrl+C
docker compose down
```

### Archivos necesarios

El paquete de entrega debe conservar esta estructura:

```text
ceu-whysoserious/
├── backend/
│   ├── .env
│   └── models/
│       └── final_teams_backup_0806/
├── frontend/
└── docker-compose.yml
```

El fichero `.env` contiene las credenciales del entorno preparado para la evaluación. Por seguridad, no forma parte del repositorio público, pero debe estar presente en `backend/.env` antes de arrancar el sistema.

### Ejecución sin Docker

La ejecución manual se mantiene como alternativa para desarrollo:

```bash
cd ceu-whysoserious/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

En otra terminal:

```bash
cd ceu-whysoserious/frontend
npm install
npm run dev
```

---

## Motivación

Los riesgos psicosociales en el trabajo suelen hacerse visibles tarde: cuando ya se han producido ausencias, rotación, conflictos o deterioro del rendimiento. Las encuestas de clima y bienestar aportan información útil, pero dependen de la participación activa del empleado y no siempre capturan cambios progresivos en el día a día.

Why So Serious explora una vía complementaria. Parte de comunicaciones corporativas autorizadas, extrae únicamente señales numéricas mediante PLN y las agrega por equipo y proyecto. La intención es ofrecer una herramienta preventiva, no un mecanismo de vigilancia individual. Por ello, el diseño evita persistir el texto original de los mensajes y restringe las vistas según el rol del usuario.

---

## Arquitectura general

```text
Microsoft Teams
      |
      | Microsoft Graph API
      v
Backend FastAPI
      |
      | Limpieza HTML e inferencia NLP
      v
Modelo transformer multilabel
      |
      | Scores emocionales
      v
Motor de riesgo
      |
      | Métricas agregadas
      v
Supabase PostgreSQL
      |
      | REST API con sesión autenticada
      v
Frontend React + Vite
```

El backend concentra la autenticación, la comunicación con Microsoft Graph, la inferencia del modelo, el cálculo del riesgo y el acceso a Supabase. El frontend se centra en la consulta visual de los resultados: dashboard global, equipos, proyectos, detalle temporal y perfil individual supervisado.

---

## Pipeline NLP

El módulo NLP utiliza un transformer fine-tuneado sobre mensajes de trabajo en español. La inferencia es multilabel, por lo que un mismo mensaje puede activar varias señales emocionales al mismo tiempo.

El modelo activo se carga desde:

```text
backend/models/final_teams_backup_0806/
```

### Etiquetas

| Etiqueta | Descripción | Papel en el sistema |
|---|---|---|
| `ESTRES_ANSIEDAD` | Estrés, presión emocional o preocupación | Señal operativa |
| `SOBRECARGA_URGENCIA` | Exceso de carga, urgencia o presión por plazos | Señal operativa |
| `CANSANCIO_FATIGA` | Agotamiento, desgaste o falta de energía | Señal operativa |
| `ENFADO_IRRITACION` | Frustración, tensión o conflicto | Señal operativa |
| `NEUTRO` | Mensajes informativos sin carga emocional relevante | Fallback y línea base |

La implementación aplica umbrales por etiqueta, definidos en `backend/thresholds.json`. Si ninguna señal operativa supera su umbral, el resultado se considera `NEUTRO`. No se utiliza un sistema de expresiones regulares ni patrones léxicos para rescatar etiquetas: la decisión depende de la inferencia del modelo y del filtrado por umbral.

### Prueba rápida

Con el backend arrancado:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Estoy agotada y no llego a los plazos", "model": "final"}'
```

---

## Motor de riesgo

El motor de riesgo convierte los scores emocionales en un indicador interpretable por equipo, proyecto o empleado supervisado. La escala final se expresa como porcentaje y se clasifica en tres niveles:

```text
Verde    riesgo < 20 %
Amarillo 20 % <= riesgo < 35 %
Rojo     riesgo >= 35 %
```

La lógica principal se encuentra en `backend/logic/risk_model.py`. De forma resumida:

1. Se descartan intensidades que no superan el umbral de su etiqueta.
2. Para cada mensaje se calcula un riesgo base a partir de la señal operativa más intensa.
3. Se estima la correlación de Pearson entre cada señal y el riesgo base para ponderar las señales que más acompañan al riesgo observado.
4. Se obtiene un riesgo por mensaje normalizado.
5. Los riesgos se agregan por empleado, proyecto y equipo, respetando los permisos de consulta.

Esta aproximación permite que el peso de cada señal no sea completamente fijo, sino que se ajuste al comportamiento observado en el conjunto analizado.

---

## Stack tecnológico

### Backend

| Tecnología | Uso |
|---|---|
| FastAPI | API REST, rutas y middleware de sesión |
| Transformers | Carga e inferencia del modelo NLP |
| PyTorch | Ejecución del modelo transformer |
| APScheduler | Programación de la ingesta automática |
| Supabase | Persistencia sobre PostgreSQL |
| requests | Integración HTTP con Microsoft Graph |
| python-dotenv | Lectura de variables de entorno |

### Frontend

| Tecnología | Uso |
|---|---|
| React 19 + Vite | Aplicación SPA y build del cliente |
| Material UI v7 | Componentes de interfaz |
| TanStack Query | Consulta y caché de datos |
| React Router v7 | Navegación y protección de rutas |
| Recharts | Visualización de tendencias |

---

## Estructura del proyecto

```text
ceu-whysoserious/
├── backend/
│   ├── main.py
│   ├── nlp_model.py
│   ├── scheduler_tasks.py
│   ├── thresholds.json
│   ├── auth/
│   ├── logic/
│   ├── services/
│   ├── models/
│   │   └── final_teams_backup_0806/
│   ├── scripts/
│   │   └── training/
│   └── tests/
├── frontend/
│   └── src/
├── docs/
├── legacy/
├── docker-compose.yml
└── GUIA_IMPLANTACION.md
```

La carpeta `legacy/` conserva material histórico, prototipos y resultados de fases anteriores. No forma parte del flujo activo de ejecución ni se incluye en el contexto Docker.

---

## Variables de entorno

El backend lee su configuración desde `backend/.env`:

```env
TENANT_ID=<tenant-id>
CLIENT_ID=<client-id>
CLIENT_SECRET=<client-secret>
REDIRECT_URI=http://localhost:8000/auth/callback

SUPABASE_URL=<supabase-url>
SUPABASE_KEY=<supabase-service-role-key>

SESSION_SECRET_KEY=<clave-larga-aleatoria>
FRONTEND_URL=http://localhost:5173
APP_ORIGIN=http://localhost:8000
```

En la entrega del TFG, estas credenciales corresponden al entorno preparado para la demostración. Si el proyecto se adapta a otra organización, deben sustituirse por valores propios de Azure AD y Supabase.

---

## Validación y tests

Las pruebas automatizadas cubren la lógica de riesgo, el control de acceso, la privacidad y varios casos de agregación temporal.

Desde la raíz del repositorio:

```bash
pytest
```

También pueden ejecutarse por bloques:

```bash
pytest backend/tests/unit/
pytest backend/tests/validation/
pytest backend/tests/legacy/
```

| Suite | Cobertura principal |
|---|---|
| `unit/` | Motor de riesgo, RBAC y robustez básica |
| `validation/` | Riesgo por equipo/proyecto, año fiscal, privacidad y persistencia |
| `legacy/` | Smoke test del flujo de autenticación |

---

## Entrenamiento del modelo

El modelo activo incluido en la entrega es `backend/models/final_teams_backup_0806/`. Los scripts de entrenamiento y evaluación se mantienen en `backend/scripts/training/`.

```bash
cd ceu-whysoserious/backend
source venv/bin/activate
python scripts/training/train_teams.py
python scripts/training/evaluate_goldset.py
```

Los datasets están en la carpeta `data/`, situada en la raíz del proyecto:

| Archivo | Uso |
|---|---|
| `teams_train_manual.csv` | Entrenamiento |
| `teams_val_manual.csv` | Validación durante entrenamiento |
| `teams_goldset_120.csv` | Evaluación final mantenida aparte |

Durante el desarrollo se descartaron etiquetas que no aportaban valor directo al riesgo psicosocial observado, como `TRISTEZA` o `POSITIVO_ALIVIO`, y se mantuvo un núcleo operativo centrado en estrés, sobrecarga, fatiga e irritación.

---

## Métricas del modelo

Evaluación sobre `teams_goldset_120.csv`:

| Etiqueta | Precisión | Recall | F1-score |
|---|---:|---:|---:|
| `ESTRES_ANSIEDAD` | 0.789 | 0.698 | 0.800 |
| `SOBRECARGA_URGENCIA` | 0.786 | 0.825 | 0.816 |
| `CANSANCIO_FATIGA` | 0.632 | 0.960 | 0.773 |
| `ENFADO_IRRITACION` | 0.812 | 0.929 | 0.815 |
| `NEUTRO` | 0.889 | 0.816 | 0.848 |
| Macro avg | | | 0.810 |

Estas métricas deben interpretarse como una validación offline del clasificador lingüístico. La validación del impacto organizativo real queda fuera del alcance del TFG y requeriría un estudio empírico posterior.

---

## Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Estado del backend y carga del modelo |
| `POST` | `/predict` | Prueba manual del clasificador NLP |
| `GET` | `/api/me` | Usuario autenticado |
| `GET` | `/login` | Inicio del flujo OAuth |
| `GET` | `/auth/callback` | Callback OAuth |
| `GET` | `/logout` | Cierre de sesión |
| `GET` | `/api/my/workspaces` | Equipos y proyectos visibles |
| `GET` | `/api/teams/risk` | Riesgo agregado por equipo |
| `GET` | `/api/projects/risk` | Riesgo agregado por proyecto |
| `GET` | `/api/employees/profile` | Perfil supervisado de empleado |
| `POST` | `/api/admin/trigger-analysis` | Lanzamiento manual de la ingesta |

Salvo `/health` y `/predict`, los endpoints requieren sesión activa. La autorización se aplica desde `permissions_service.py`, de acuerdo con el rol y el ámbito organizativo del usuario.

---

## Licencia

Proyecto académico desarrollado como Trabajo de Fin de Grado en CEU Universidad San Pablo.
