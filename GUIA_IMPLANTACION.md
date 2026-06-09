# Guía de implantación

Esta guía recoge los pasos necesarios para poner en marcha Why So Serious en el entorno preparado para la evaluación del TFG. También incluye una sección final con las consideraciones necesarias si se quisiera adaptar el sistema a otra organización.

La vía recomendada para la entrega es Docker Compose, porque reduce el número de pasos manuales y permite ejecutar backend y frontend de forma conjunta.

---

## 1. Ejecución con Docker

### 1.1 Requisitos previos

Antes de arrancar el proyecto es necesario contar con:

| Requisito | Motivo |
|---|---|
| Docker Desktop | Descargar y ejecutar los contenedores |
| `backend/.env` | Cargar credenciales y configuración del entorno |
| Conexión a Internet | Descarga inicial de imágenes y autenticación con Microsoft |

Puede comprobarse que Docker está disponible con:

```bash
docker --version
docker compose version
```

### 1.2 Estructura esperada

Tras clonar el repositorio, su raíz no tiene ninguna subcarpeta intermedia: `backend/`, `frontend/` y `docker-compose.yml` están directamente en la raíz. El fichero `.env` debe colocarse dentro de la carpeta del backend:

```text
<raíz-del-repositorio-clonado>/
└── backend/
    └── .env
```

El modelo utilizado por el backend se incluye dentro de la imagen Docker publicada:

```text
claudiaea/whysoserious-backend:latest
```

Por tanto, para la evaluación no es necesario copiar la carpeta del modelo ni descargar pesos desde Hugging Face durante el arranque, aunque sí debe estar instalado Git LFS para recuperar los archivos del modelo al clonar el repositorio. Si se ejecuta el backend manualmente fuera de Docker, entonces sí debe existir una copia local del modelo en `backend/models/final_teams/`.

### 1.3 Arranque de la aplicación

Desde la raíz del repositorio clonado:

```bash
docker compose up
```

La primera ejecución puede tardar varios minutos. Docker construye localmente las imágenes del frontend y del backend a partir de los `Dockerfile` del repositorio. Cuando aparezca el mensaje `Application startup complete.`, el servidor estará listo para recibir peticiones.

### 1.4 Acceso a los servicios

| Servicio | URL |
|---|---|
| Aplicación web | http://localhost:5173 |
| Backend | http://localhost:8000 |
| Comprobación de estado | http://localhost:8000/health |
| Documentación OpenAPI | http://localhost:8000/docs |

Para detener los contenedores:

```bash
Ctrl+C
docker compose down
```

### 1.5 Comprobación mínima

Una vez arrancado el sistema, se recomienda:

1. Abrir `http://localhost:8000/health`.
2. Confirmar que la respuesta indica `"status": "ok"` y `"model": "loaded"`.
3. Abrir `http://localhost:5173`.
4. Iniciar sesión con Microsoft.
5. Revisar el dashboard y alguna vista de equipo o proyecto.

---

## 2. Ejecución local sin Docker

Este modo se conserva como alternativa para desarrollo o depuración. Para la evaluación se recomienda utilizar Docker.

### 2.1 Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

En Windows, la activación del entorno se realiza con:

```bash
venv\Scripts\activate
```

El backend queda disponible en `http://localhost:8000`.

### 2.2 Frontend

En otra terminal:

```bash
cd frontend
npm install
npm run dev
```

El frontend queda disponible en `http://localhost:5173`. En desarrollo, el cliente consume la API desde `http://localhost:8000`, tal como se define en `frontend/src/api/api.js`.

---

## 3. Configuración del entorno

El backend utiliza el fichero `backend/.env`. En la entrega del TFG este fichero ya contiene las credenciales del entorno preparado para la demostración.

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

| Variable | Descripción |
|---|---|
| `TENANT_ID` | Identificador del tenant de Azure AD |
| `CLIENT_ID` | Identificador de la aplicación registrada |
| `CLIENT_SECRET` | Secreto de cliente de Azure |
| `REDIRECT_URI` | URL de retorno del flujo OAuth |
| `SUPABASE_URL` | URL del proyecto Supabase |
| `SUPABASE_KEY` | Clave `service_role` de Supabase |
| `SESSION_SECRET_KEY` | Clave usada para firmar la sesión |
| `FRONTEND_URL` | URL del cliente web |
| `APP_ORIGIN` | URL pública del backend |

---

## 4. Adaptación a otra organización

Esta sección no es necesaria para la demostración del TFG, pero resume qué habría que cambiar si el sistema se desplegara en un entorno distinto.

### 4.1 Registro en Azure AD

Debe crearse un registro de aplicación en Azure AD y configurar el callback:

```text
http://localhost:8000/auth/callback
```

En un despliegue real, `localhost` tendría que sustituirse por el dominio correspondiente.

Los permisos delegados permiten el inicio de sesión de usuarios:

| Permiso | Finalidad |
|---|---|
| `User.Read` | Leer el perfil del usuario autenticado |
| `Chat.Read` | Acceder a chats autorizados para el usuario |
| `ChatMessage.Read` | Leer mensajes autorizados |

Los permisos de aplicación permiten la ingesta automática:

| Permiso | Finalidad |
|---|---|
| `User.Read.All` | Listar usuarios de la organización |
| `Chat.Read.All` | Leer chats organizativos autorizados |
| `ChatMessage.Read.All` | Leer mensajes organizativos autorizados |

Los permisos de aplicación requieren consentimiento de administrador.

### 4.2 Supabase

El sistema utiliza Supabase como acceso gestionado a PostgreSQL. Las tablas principales son:

```sql
CREATE TABLE org_users (
    user_email TEXT PRIMARY KEY,
    display_name TEXT,
    role TEXT DEFAULT 'employee'
);

CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE user_teams (
    user_email TEXT REFERENCES org_users(user_email),
    team_id INTEGER REFERENCES teams(id),
    PRIMARY KEY (user_email, team_id)
);

CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE project_members (
    user_email TEXT REFERENCES org_users(user_email),
    project_id INTEGER REFERENCES projects(id),
    PRIMARY KEY (user_email, project_id)
);

CREATE TABLE risk_metrics (
    id BIGSERIAL PRIMARY KEY,
    message_id TEXT UNIQUE NOT NULL,
    user_email TEXT,
    message_timestamp TIMESTAMPTZ,
    project_id INTEGER REFERENCES projects(id),
    workspace_id INTEGER,
    estres_ansiedad FLOAT DEFAULT 0,
    enfado_irritacion FLOAT DEFAULT 0,
    sobrecarga_urgencia FLOAT DEFAULT 0,
    cansancio_fatiga FLOAT DEFAULT 0,
    neutro FLOAT DEFAULT 0
);

CREATE TABLE org_settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
```

---

## 5. Ingesta automática

El backend incluye una tarea programada con APScheduler. Esta tarea puede ejecutarse de forma periódica y también puede lanzarse manualmente desde el panel de administración.

En `backend/scheduler_tasks.py` se mantiene un filtro propio del entorno académico:

```python
TFG_FILTER = ".tfg@"
```

Este filtro limita la ingesta a los usuarios preparados para la demostración. En una implantación real tendría que cambiarse por el dominio de la organización o eliminarse si se desea analizar a todos los usuarios autorizados.

---

## 6. Solución de problemas

| Síntoma | Posible causa | Revisión recomendada |
|---|---|---|
| `docker: command not found` | Docker no está instalado o no está arrancado | Abrir Docker Desktop |
| No se encuentra `docker-compose.yml` | El comando se ha ejecutado fuera de la raíz del repositorio clonado | Entrar en la carpeta donde están `backend/`, `frontend/` y `docker-compose.yml` |
| El frontend no carga | Los contenedores todavía están arrancando | Esperar a `Application startup complete.` |
| Falla el login con Microsoft | `.env` incompleto o callback incorrecto | Revisar Azure y `REDIRECT_URI` |
| `/health` muestra `"model": "loading"` | El modelo no se ha cargado | Revisar los logs del contenedor backend |
| El análisis procesa 0 usuarios | El filtro `.tfg@` no coincide | Revisar `TFG_FILTER` |
| Error de Supabase | Credenciales o tablas incorrectas | Revisar `SUPABASE_URL`, `SUPABASE_KEY` y esquema |

---

## 7. Notas sobre la entrega

El despliegue de evaluación utiliza imágenes Docker construidas localmente a partir del código del repositorio. Durante esa construcción, el backend incorpora el modelo `final_teams`, mientras que el frontend genera y sirve la aplicación ya compilada. Los ficheros `.dockerignore` se conservan para desarrollo y reconstrucción local de imágenes, excluyendo elementos que no son necesarios para ejecutar la aplicación, como logs, resultados antiguos, caches y tests.

Por diseño, el sistema no persiste el texto original de los mensajes. La base de datos conserva únicamente métricas numéricas y metadatos necesarios para la agregación y consulta posterior.
