# Why So Serious

> Sistema de monitorización de riesgos psicosociales para entornos de trabajo basado en Microsoft Teams.

**Why So Serious** analiza las comunicaciones de un equipo en Teams, detecta patrones de estrés, sobrecarga y fatiga mediante un clasificador de emociones propio (transformer fine-tuneado), y los visualiza en un dashboard de riesgo para que los responsables puedan actuar antes de que el problema escale.

---

## Tabla de Contenidos

- [Guía de Instalación para el Tribunal](#guia-de-instalacion-para-el-tribunal)
- [Motivación](#motivacion)
- [Arquitectura](#arquitectura)
- [Pipeline NLP](#pipeline-nlp)
- [Motor de Riesgo](#motor-de-riesgo)
- [Stack Tecnológico](#stack-tecnologico)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Variables de Entorno](#variables-de-entorno)
- [Tests](#tests)
- [Entrenamiento del Modelo](#entrenamiento-del-modelo)
- [Métricas del Modelo](#metricas-del-modelo)
- [API — Endpoints Principales](#api--endpoints-principales)

---

## Guía de Instalación para el Tribunal

### Método recomendado — Docker (un solo comando)

Solo se necesita **Docker Desktop** instalado. No hace falta instalar manualmente Python ni Node.js en el equipo de evaluación, aunque sí es necesario disponer del fichero `.env` entregado junto al proyecto y de conexión a Internet para el arranque inicial y la autenticación corporativa.

Descarga Docker Desktop en [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) e instálalo. Verifica que está corriendo:

```bash
docker --version
```

#### Archivos incluidos en la entrega

El paquete de entrega incluye todo lo necesario:

| Archivo | Descripción |
|---|---|
| `ceu-whysoserious/` (carpeta o ZIP) | Código fuente completo + modelo NLP (~2.5 GB) |
| `backend/.env` | Credenciales del proyecto (Supabase + Azure) |

> El fichero `.env` se entrega junto al ZIP. Debe estar en `ceu-whysoserious/backend/.env` antes de ejecutar el siguiente paso.

#### Paso 1 — Situar el `.env`

Copia el fichero `.env` recibido dentro de la carpeta `backend/`:

```
ceu-whysoserious/
└── backend/
    └── .env   ← aquí
```

#### Paso 2 — Arrancar la aplicación

```bash
cd ceu-whysoserious
docker compose up --build
```

La primera vez tarda **10–15 minutos** (descarga dependencias y prepara el modelo). Las siguientes veces arranca mucho más rápido con `docker compose up`.

Cuando aparezca en la terminal:

```
Application startup complete.
```

la aplicación está lista.

#### Paso 3 — Acceder

1. Abre el navegador en **[http://localhost:5173](http://localhost:5173)**
2. Haz clic en **"Iniciar sesión con Microsoft"**
3. Usa las credenciales de la cuenta de demostración facilitadas con la entrega
4. Serás redirigido al dashboard de riesgo con datos reales

Para parar la aplicación: `Ctrl+C` en la terminal, luego `docker compose down`.

#### Qué revisar durante la demo

Una vez iniciada la sesión, el recorrido mínimo recomendado es:

1. **Dashboard**: comprobar que se muestran indicadores agregados y tarjetas de estado general.
2. **Equipos y proyectos**: abrir un equipo o proyecto visible y verificar el detalle con su tendencia temporal.
3. **Perfil individual supervisado**: acceder, con la cuenta autorizada, a la vista individual restringida para comprobar que el control de acceso y el desglose por proyectos funcionan correctamente.

#### Solución de problemas — Docker

| Síntoma | Causa probable | Solución |
|---|---|---|
| `docker: command not found` | Docker Desktop no instalado o no iniciado | Abre Docker Desktop y espera a que el icono deje de girar |
| `failed to read dockerfile` | No estás dentro de `ceu-whysoserious/` | Ejecuta `cd ceu-whysoserious` antes del comando |
| El build falla con error de red | Sin conexión a internet durante el build | Conecta a internet y repite `docker compose up --build` |
| `http://localhost:5173` no carga | Contenedores aún arrancando | Espera a ver `Application startup complete.` en la terminal |
| Login falla con error de Microsoft | `.env` mal colocado o incompleto | Verifica que `backend/.env` existe con las variables correctas |
| `"model": "loading"` en `/health` tras 2 min | Build incompleto | Para con `Ctrl+C`, ejecuta `docker compose up --build` de nuevo |

---

### Método alternativo — Sin Docker

Si no puedes instalar Docker, puedes levantar la aplicación manualmente con **Python 3.10+** y **Node.js 18+**.

<details>
<summary>Ver instrucciones de instalación manual</summary>

Verifica que están instalados:

```bash
python --version   # debe mostrar 3.10+
node --version     # debe mostrar v18+
```

**Backend** — abre una terminal:

```bash
cd ceu-whysoserious/backend
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows CMD
pip install -r requirements.txt
uvicorn main:app --reload
```

El backend estará en **http://localhost:8000**. Verifica con `http://localhost:8000/health` (espera `"model": "loaded"`).

**Frontend** — abre una segunda terminal:

```bash
cd ceu-whysoserious/frontend
npm install
npm run dev
```

El frontend estará en **http://localhost:5173**.

| Síntoma | Solución |
|---|---|
| `ModuleNotFoundError` | Activa el entorno virtual antes de `uvicorn` |
| `"model": "loading"` tras 1 min | Comprueba que `backend/models/final_teams/` contiene `model.safetensors` |
| Frontend en blanco | Asegúrate de que el backend responde antes de abrir el navegador |

</details>

---

## Motivacion

Los riesgos psicosociales (estrés crónico, agotamiento, sobrecarga de trabajo) son la primera causa de baja laboral en Europa, pero son invisibles hasta que ya es tarde. Las encuestas de bienestar llegan tarde y tienen baja tasa de respuesta. Las comunicaciones del equipo, en cambio, son una señal continua y objetiva.

**Why So Serious** convierte esa señal en inteligencia accionable: sin leer mensajes individuales, sin violar la privacidad, solo agregando emociones a nivel de equipo y proyecto.

---

## Arquitectura

```
Microsoft Teams
      │
      │  (Microsoft Graph API — OAuth 2.0)
      ▼
┌─────────────────────────────────────────────┐
│               Backend (FastAPI)              │
│                                             │
│  ┌──────────────┐    ┌───────────────────┐  │
│  │  NLP Model   │───▶│   Risk Engine     │  │
│  │ (Transformer)│    │ (Pearson scoring) │  │
│  └──────────────┘    └───────────────────┘  │
│          │                    │             │
│          ▼                    ▼             │
│  ┌──────────────────────────────────────┐   │
│  │          Supabase (PostgreSQL)       │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  APScheduler → Pipeline nocturno (02:00)    │
└─────────────────────────────────────────────┘
      │
      │  REST API (cookie auth)
      ▼
┌─────────────────────────────────────────────┐
│            Frontend (React + Vite)           │
│                                             │
│  Dashboard · Equipos · Proyectos · Empleados│
└─────────────────────────────────────────────┘
```

---

## Pipeline NLP

El clasificador de emociones es un transformer fine-tuneado sobre mensajes de Teams en español. Implementa clasificación **multilabel**: un mensaje puede activar varias etiquetas simultáneamente.

### Etiquetas

| Etiqueta              | Descripción                              | Rol en el riesgo      |
|-----------------------|------------------------------------------|-----------------------|
| `ESTRES_ANSIEDAD`     | Estrés agudo, preocupación, pánico       | Señal operativa       |
| `SOBRECARGA_URGENCIA` | Presión de plazos, volumen de trabajo    | Señal operativa       |
| `CANSANCIO_FATIGA`    | Agotamiento, desgaste acumulado          | Señal operativa       |
| `ENFADO_IRRITACION`   | Frustración, conflicto                   | Señal operativa       |
| `NEUTRO`              | Mensajes informativos sin carga afectiva | Línea base            |

Las cuatro señales operativas son las que alimentan el **observatorio de riesgo**. `TRISTEZA` y `POSITIVO_ALIVIO` fueron descartadas por no ser relevantes en contexto de riesgo psicosocial laboral.

### Umbrales dinámicos

Los umbrales de decisión por etiqueta se calibran automáticamente y se almacenan en `backend/thresholds.json`. Si una probabilidad cae por debajo del umbral de su etiqueta, no contribuye al cálculo de riesgo (supresión de ruido).

### Prueba rápida del NLP

Una vez el backend está en marcha, puedes probar el modelo directamente:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Estoy agotado y no llego a los plazos", "model": "final"}'
```

---

## Motor de Riesgo

El algoritmo **Whysoserious** convierte los scores del modelo NLP en un semáforo de riesgo:

```
Verde    →  riesgo < 20 %
Amarillo →  20 % ≤ riesgo < 35 %
Rojo     →  riesgo ≥ 35 %
```

### Metodología (`risk_model.py`)

1. **Calibración**: Se suprimen intensidades por debajo del umbral calibrado para cada etiqueta.
2. **`risk_base`**: Para cada mensaje, se toma la intensidad máxima de cualquier señal operativa (el «peor» indicador).
3. **Pesos dinámicos (Pearson)**: Se calcula la correlación de Pearson entre cada señal operativa y `risk_base`. Esto determina qué emoción domina el contexto actual del equipo.
4. **`msg_risk`**: Suma ponderada y normalizada al rango [0, 1].
5. **Agregación**: A partir de `msg_risk`, el sistema calcula primero riesgos individuales medios. Después, el riesgo de proyecto se obtiene como la media del riesgo contextual de sus miembros operativos en ese proyecto, mientras que el riesgo de equipo se calcula como la media del riesgo global de sus integrantes operativos.

---

## Stack Tecnologico

### Backend
| Tecnología | Uso |
|---|---|
| **FastAPI** | API REST, middleware de sesión |
| **Transformers (HuggingFace)** | Inferencia del modelo NLP |
| **PyTorch** | Backend de cómputo del modelo |
| **APScheduler** | Pipeline nocturno (02:00) |
| **Supabase** | Base de datos PostgreSQL + cliente Python |
| **requests** | Integración HTTP con Microsoft Graph y flujos OAuth 2.0 |
| **python-dotenv** | Gestión de variables de entorno |

### Frontend
| Tecnología | Uso |
|---|---|
| **React 18 + Vite** | SPA y build tool |
| **MUI v7** | Librería de componentes |
| **TanStack Query** | Fetching y caché de datos |
| **React Router v6** | Enrutado con auth guard |

---

## Estructura del Proyecto

```
ceu-whysoserious/
├── backend/
│   ├── main.py                  # FastAPI app — rutas y middleware
│   ├── nlp_model.py             # Inferencia del transformer
│   ├── scheduler_tasks.py       # Pipeline nocturno
│   ├── thresholds.json          # Umbrales calibrados por etiqueta
│   ├── .env                     # Credenciales (NO en git — incluido en entrega)
│   ├── auth/
│   │   ├── auth_graph_web.py    # OAuth flujo web (usuario)
│   │   └── auth_graph_app.py    # Auth app-only (pipeline)
│   ├── logic/
│   │   └── risk_model.py        # Algoritmo Whysoserious (Pearson)
│   ├── services/
│   │   ├── risk_service.py      # Agregación de riesgo para la API
│   │   └── permissions_service.py # RBAC — roles y accesos
│   ├── db_client.py             # Inicialización del cliente Supabase
│   ├── db_repository.py         # CRUD — todas las queries a Supabase
│   ├── models/
│   │   └── final_teams/         # Modelo fine-tuneado (~2.5 GB — incluido en entrega)
│   ├── scripts/
│   │   └── training/            # Scripts de entrenamiento y evaluación
│   └── tests/
│       ├── unit/                # Tests del motor de riesgo y RBAC
│       └── validation/          # Tests de año fiscal, proyectos, privacidad
│
└── frontend/
    └── src/
        ├── api/api.js               # Cliente HTTP único (credentials: include)
        ├── context/AuthContext.jsx  # Estado de sesión global
        ├── main.jsx                 # Router + auth guard
        └── pages/
            ├── Dashboard/           # Vista principal de riesgo global
            ├── Teams/               # Vista por equipo
            ├── ProjectDetail/       # Detalle de proyecto con tendencia temporal
            ├── EmployeeProfile/     # Perfil de empleado y desglose por proyecto
            └── Login/               # Pantalla de autenticación Microsoft
```

---

## Variables de Entorno

El fichero `backend/.env` se entrega junto al código. Su estructura es:

```env
# Azure AD (Microsoft Graph — OAuth 2.0)
TENANT_ID=<tenant-id>
CLIENT_ID=<app-client-id>
CLIENT_SECRET=<app-client-secret>
REDIRECT_URI=http://localhost:8000/auth/callback

# Supabase (base de datos)
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_KEY=<service-role-key>
```

> No es necesario crear ninguna cuenta ni registrar ninguna aplicación en Azure — las credenciales del `.env` apuntan al tenant y a la base de datos del proyecto.

---

## Tests

Los tests se ejecutan desde `ceu-whysoserious/` para que `conftest.py` inyecte correctamente los paths.

```bash
cd ceu-whysoserious

# Todos los tests
pytest

# Solo unitarios
pytest backend/tests/unit/

# Solo validación
pytest backend/tests/validation/

# Un test concreto
pytest backend/tests/unit/test_unit_core.py::test_risk_level_thresholds
```

### Suites

| Suite | Qué cubre |
|---|---|
| `tests/unit/` | Motor de riesgo (Pearson), RBAC, robustez del NLP |
| `tests/validation/` | Año fiscal, riesgo por proyecto, privacidad, control de acceso |
| `tests/legacy/` | Smoke tests de autenticación |

---

## Entrenamiento del Modelo

El modelo activo está en `backend/models/final_teams/` (incluido en el paquete de entrega). Para reentrenar desde cero:

```bash
cd ceu-whysoserious/backend
source venv/bin/activate

# Entrenar (~20 min en GPU)
python scripts/training/train_teams.py

# Evaluar en el gold set
python scripts/training/evaluate_goldset.py
```

Los datasets de entrenamiento están en `data/` (raíz del proyecto):

| Archivo | Muestras | Uso |
|---|---|---|
| `teams_train_manual.csv` | 714 | Entrenamiento |
| `teams_val_manual.csv` | 170 | Validación durante training |
| `teams_goldset_120.csv` | 173 | Evaluación final (held-out — no usar para generar ejemplos) |

### Decisiones de entrenamiento

- `TRISTEZA` y `POSITIVO_ALIVIO` excluidas — no relevantes en psicología ocupacional
- `SOBRECARGA_URGENCIA` excluida del oversampling — ya era la clase mayoritaria (30%); solo `CANSANCIO_FATIGA` recibe boost 5×
- `ENFADO_IRRITACION` incluida en el núcleo operativo

---

## Metricas del Modelo

Evaluación sobre `teams_goldset_120.csv` (173 muestras — held-out):

| Etiqueta              | Precisión | Recall | F1-Score |
|-----------------------|-----------|--------|----------|
| ESTRES_ANSIEDAD       | 0.789     | 0.698  | 0.800    |
| SOBRECARGA_URGENCIA   | 0.786     | 0.825  | 0.816    |
| CANSANCIO_FATIGA      | 0.632     | 0.960  | 0.773    |
| ENFADO_IRRITACION     | 0.812     | 0.929  | 0.815    |
| NEUTRO                | 0.889     | 0.816  | **0.848** |
| **Macro AVG**         | —         | —      | **0.810** |

### KPI de aceptación

- **Robustez ante Neutros Adversarios** (mensajes neutrales mal clasificados como Sobrecarga): `FP = 1` ✅ (umbral ≤ 2)

---

## API — Endpoints Principales

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Estado del servidor y carga del modelo |
| `POST` | `/predict` | Prueba manual del motor NLP |
| `GET` | `/api/me` | Perfil del usuario en sesión |
| `GET` | `/login` | Inicia flujo OAuth con Microsoft |
| `GET` | `/auth/callback` | Callback OAuth, crea sesión |
| `GET` | `/logout` | Cierra sesión |
| `GET` | `/api/my/workspaces` | Equipos y proyectos accesibles por el usuario |
| `GET` | `/api/teams/risk` | Riesgo del equipo con tendencia temporal |
| `GET` | `/api/projects/risk` | Riesgo táctico de un proyecto |
| `GET` | `/api/employees/profile` | Perfil completo de riesgo de un empleado |
| `POST` | `/api/admin/trigger-analysis` | Dispara el pipeline manualmente |

> Todos los endpoints (excepto `/health` y `/predict`) requieren sesión activa. La autorización está gestionada por RBAC (`permissions_service.py`); los roles se almacenan en Supabase.

---

## Licencia

Proyecto académico — Trabajo de Fin de Grado, CEU Universidad San Pablo.
