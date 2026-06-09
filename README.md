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

La forma recomendada de ejecutar el proyecto es mediante Docker Compose. De este modo, no es necesario instalar manualmente Python ni Node.js; únicamente hace falta disponer de Docker Desktop, de Git LFS para recuperar el modelo final durante el clon, del fichero `backend/.env` facilitado con la entrega y de conexión a Internet durante el primer arranque.

### 1. Obtener el proyecto

Clona el repositorio y entra en su raíz. No hay ninguna subcarpeta intermedia: `backend/`, `frontend/` y `docker-compose.yml` están directamente en la raíz del repositorio:

```bash
git clone https://github.com/claudiaerguido/TFG-WhySoSerious.git
cd TFG-WhySoSerious
git lfs install
git lfs pull
```

Si Git LFS no está instalado en el equipo, debe instalarse previamente para que el modelo final del backend se descargue junto con el repositorio. El comando `git lfs pull` debe ejecutarse dentro de la carpeta del repositorio clonado.

A continuación, coloca el fichero `backend/.env` facilitado con la entrega de modo que la estructura quede así:

```text
TFG-WhySoSerious/
├── backend/
│   └── .env
├── frontend/
└── docker-compose.yml
```

El `.env` contiene las credenciales del entorno preparado para la evaluación. Por seguridad no forma parte del repositorio público, pero debe estar presente en `backend/.env` **antes** de arrancar el sistema.

### 2. Arrancar con Docker

Desde la raíz del repositorio clonado:

```bash
docker compose up --build
```

La primera ejecución puede tardar varios minutos, ya que Docker construye localmente las imágenes del backend y del frontend a partir de los `Dockerfile` del proyecto. El modelo NLP final queda incluido en el árbol del repositorio gracias a Git LFS, por lo que no es necesario copiar pesos manualmente. Cuando el backend muestre `Application startup complete.`, la aplicación estará lista.

Si la aplicación ya ha sido construida previamente en ese equipo, puede utilizarse después `docker compose up` para arrancarla de nuevo sin reconstruir las imágenes.

| Servicio | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend | http://localhost:8000 |
| Estado del backend | http://localhost:8000/health |
| Documentación de API | http://localhost:8000/docs |

### 3. Iniciar sesión

Abre `http://localhost:5173` y pulsa "Iniciar sesión con Microsoft". Esto redirige a la pantalla de autenticación de Microsoft, donde puede usarse la siguiente cuenta de demostración con rol de administrador (la primera vez puede pedir aceptar los permisos delegados de la aplicación; basta con aceptarlos para continuar):

| Campo | Valor |
|---|---|
| Correo | `javier.torres.tfg@ww5dl.onmicrosoft.com` |
| Contraseña | `123Javi!` |

Si esta cuenta no permite iniciar sesión, puede emplearse esta cuenta alternativa de respaldo:

| Campo | Valor |
|---|---|
| Correo | `ana.martinez.tfg@ww5dl.onmicrosoft.com` |
| Contraseña | `137137137Ana` |

### 4. Qué revisar

Para recorrer el sistema de extremo a extremo, se recomienda comprobar:

1. El dashboard global, con el riesgo agregado de los equipos y proyectos visibles para el rol de administrador.
2. La vista de detalle de un equipo o proyecto, con su evolución temporal.
3. El perfil supervisado de un empleado.
4. `http://localhost:8000/docs`, con la documentación interactiva (OpenAPI) de la API.

Para una checklist más detallada y la solución de problemas habituales (login, modelo, Supabase...), consulta [`GUIA_IMPLANTACION.md`](./GUIA_IMPLANTACION.md).

### Detener la aplicación

```bash
Ctrl+C
docker compose down
```

### Ejecución sin Docker

La ejecución manual se mantiene como alternativa para desarrollo:

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

En otra terminal:

```bash
cd frontend
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

El modelo activo se carga dentro de la imagen Docker del backend desde:

```text
/app/models/final_teams/
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
│   │   └── final_teams/
│   ├── scripts/
│   │   └── training/
│   └── tests/
├── frontend/
│   └── src/
├── docker-compose.yml
└── GUIA_IMPLANTACION.md
```

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

El modelo activo incluido en la imagen Docker del backend es `final_teams`. En desarrollo local, si se desea ejecutar el backend sin Docker, debe existir en `backend/models/final_teams/`. Los scripts de entrenamiento y evaluación se mantienen en `backend/scripts/training/`.

```bash
cd backend
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
