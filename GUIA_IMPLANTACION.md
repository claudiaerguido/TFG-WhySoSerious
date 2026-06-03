# Guía de Implantación — Why So Serious

Sistema de monitorización de riesgo psicosocial para Microsoft Teams.

---

## Arranque rápido

Una vez completada la configuración, el sistema requiere **dos terminales abiertas simultáneamente**:

**Terminal 1 — Backend:**
```bash
cd ceu-whysoserious/backend
source venv/bin/activate        # Windows: venv\Scripts\activate
uvicorn main:app --reload
# Disponible en http://localhost:8000
```

**Terminal 2 — Frontend:**
```bash
cd ceu-whysoserious/frontend
npm run dev
# Disponible en http://localhost:5173
```

Abre el navegador en `http://localhost:5173` e inicia sesión con tu cuenta de Microsoft.

> Para producción, usa `npm run build` en el frontend y despliega la carpeta `dist/` en tu servidor web. El backend se puede servir sin `--reload`.

---

## Qué necesitas antes de empezar

| Requisito | Para qué sirve |
|---|---|
| Tenant de Microsoft 365 con Teams activo | El sistema lee los mensajes de Teams de tu organización |
| Cuenta de administrador de Azure AD | Para registrar la aplicación y darle permisos |
| Cuenta en [Supabase](https://supabase.com) (gratuita) | Base de datos donde se guardan los análisis |
| Servidor con Python 3.9+ y Node.js 18+ | Para ejecutar el backend y el frontend |

---

## Paso 1 — Registrar la aplicación en Azure AD

El sistema necesita que Microsoft le dé permiso para leer los mensajes de Teams. Para eso hay que registrar una "aplicación" en el portal de Azure.

1. Entra en [portal.azure.com](https://portal.azure.com) con una cuenta de administrador.
2. Ve a **Azure Active Directory → Registros de aplicaciones → Nueva registro**.
3. Ponle un nombre (por ejemplo, `WhySoSerious`) y selecciona **Cuentas de este directorio organizativo únicamente**.
4. En **URI de redireccionamiento**, selecciona `Web` e introduce:
   ```
   http://<tu-dominio>/auth/callback
   ```
   (en local: `http://localhost:8000/auth/callback`)
5. Pulsa **Registrar**.

### 1.1 Anotar los identificadores

Una vez creada la app, anota estos tres valores — los necesitarás más adelante:

- **Id. de directorio (inquilino)** → será tu `TENANT_ID`
- **Id. de aplicación (cliente)** → será tu `CLIENT_ID`

### 1.2 Crear el secreto de cliente

1. En el menú de la app, ve a **Certificados y secretos → Nuevo secreto de cliente**.
2. Ponle una descripción y elige una caducidad.
3. Copia el **Valor** que aparece — será tu `CLIENT_SECRET`. Solo se muestra una vez.

### 1.3 Asignar permisos de API

El sistema necesita dos tipos de permisos:

**Permisos delegados** (para el login de los usuarios del dashboard):

| Permiso | Motivo |
|---|---|
| `User.Read` | Leer el perfil del usuario que inicia sesión |
| `Chat.Read` | Leer los chats del usuario |
| `ChatMessage.Read` | Leer los mensajes de esos chats |

**Permisos de aplicación** (para el análisis nocturno automático, sin usuario):

| Permiso | Motivo |
|---|---|
| `User.Read.All` | Listar todos los usuarios de la organización |
| `Chat.Read.All` | Leer chats de cualquier usuario |
| `ChatMessage.Read.All` | Leer mensajes de cualquier chat |

Para añadirlos: **Permisos de API → Agregar un permiso → Microsoft Graph**.

> Los permisos de aplicación requieren que un administrador pulse **Conceder consentimiento de administrador** después de añadirlos. Sin este paso, el análisis nocturno no funcionará.

---

## Paso 2 — Configurar Supabase

Supabase es la base de datos donde el sistema guarda los resultados de los análisis.

1. Crea un proyecto en [supabase.com](https://supabase.com).
2. Ve a **Settings → API** y anota:
   - **Project URL** → será tu `SUPABASE_URL`
   - **service_role key** → será tu `SUPABASE_KEY` (usa la `service_role`, no la `anon`)

### 2.1 Crear las tablas

En el editor SQL de Supabase (**SQL Editor → New query**), ejecuta lo siguiente:

```sql
-- Usuarios de la organización
CREATE TABLE org_users (
    user_email  TEXT PRIMARY KEY,
    display_name TEXT,
    role        TEXT DEFAULT 'employee'
);

-- Equipos
CREATE TABLE teams (
    id   SERIAL PRIMARY KEY,
    name TEXT NOT NULL
);

-- Asignación usuario-equipo
CREATE TABLE user_teams (
    user_email TEXT REFERENCES org_users(user_email),
    team_id    INTEGER REFERENCES teams(id),
    PRIMARY KEY (user_email, team_id)
);

-- Proyectos
CREATE TABLE projects (
    id   SERIAL PRIMARY KEY,
    name TEXT NOT NULL
);

-- Asignación usuario-proyecto
CREATE TABLE project_members (
    user_email TEXT REFERENCES org_users(user_email),
    project_id INTEGER REFERENCES projects(id),
    PRIMARY KEY (user_email, project_id)
);

-- Métricas de riesgo por mensaje
CREATE TABLE risk_metrics (
    id                  BIGSERIAL PRIMARY KEY,
    message_id          TEXT UNIQUE NOT NULL,
    user_email          TEXT,
    message_timestamp   TIMESTAMPTZ,
    project_id          INTEGER REFERENCES projects(id),
    workspace_id        INTEGER,
    estres_ansiedad     FLOAT DEFAULT 0,
    enfado_irritacion   FLOAT DEFAULT 0,
    sobrecarga_urgencia FLOAT DEFAULT 0,
    cansancio_fatiga    FLOAT DEFAULT 0,
    neutro              FLOAT DEFAULT 0
);

-- Configuración general de la organización
CREATE TABLE org_settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);
```

---

## Paso 3 — Configurar el backend

### 3.1 Instalar dependencias

```bash
cd ceu-whysoserious/backend
python -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3.2 Crear el fichero de configuración

Crea un fichero llamado `.env` dentro de `ceu-whysoserious/backend/` con este contenido:

```env
# Azure AD
TENANT_ID=<id de directorio anotado en el paso 1>
CLIENT_ID=<id de aplicación anotado en el paso 1>
CLIENT_SECRET=<secreto creado en el paso 1.2>
REDIRECT_URI=http://<tu-dominio>/auth/callback

# Supabase
SUPABASE_URL=<url del proyecto de supabase>
SUPABASE_KEY=<service_role key de supabase>

# Sesiones (pon cualquier cadena larga y aleatoria)
SESSION_SECRET_KEY=cambia_esto_por_una_clave_secreta_larga

# URLs (ajusta a tu dominio en producción)
FRONTEND_URL=http://localhost:5173
APP_ORIGIN=http://localhost:8000
```

### 3.3 Arrancar el servidor

```bash
uvicorn main:app --reload
# Disponible en http://localhost:8000
```

---

## Paso 4 — Configurar el frontend

### 4.1 Instalar dependencias

```bash
cd ceu-whysoserious/frontend
npm install
```

### 4.2 Apuntar al backend

Si vas a desplegar en producción (no en local), edita `src/api/api.js` y cambia la primera línea:

```js
// Cambia esto:
const BASE_URL = "http://localhost:8000";

// Por la URL real de tu backend:
const BASE_URL = "https://tu-dominio.com";
```

### 4.3 Arrancar el frontend

```bash
npm run dev
# Disponible en http://localhost:5173
```

---

## Paso 5 — Primera configuración en el dashboard

1. Abre el dashboard en el navegador y haz login con una cuenta de administrador de tu organización.
2. Ve a la sección **Administración** y crea los equipos y proyectos de tu organización.
3. Asigna usuarios a equipos y proyectos.
4. Asigna roles a los usuarios:
   - `admin` — acceso total, puede gestionar equipos y lanzar análisis
   - `manager` — puede ver el dashboard de riesgo de su equipo
   - `employee` — sin acceso al dashboard

### 5.1 Lanzar el primer análisis

El análisis nocturno se ejecuta automáticamente cada día a las 02:00. Para lanzarlo manualmente la primera vez, ve a **Administración → Lanzar análisis ahora**.

La primera ejecución analizará las últimas 25 horas de mensajes. A partir de ahí, cada ejecución retoma desde donde dejó la anterior.

---

## Mantenimiento

### El análisis no se ejecutó

Si el servidor estuvo caído durante la hora programada, no hay problema: la próxima ejecución detecta automáticamente que hay mensajes sin analizar y los recupera desde la última ejecución correcta.

### Añadir nuevos usuarios

Los usuarios nuevos se añaden desde el panel de **Administración** del dashboard. Es necesario asignarles un rol para que puedan acceder.

### El secreto de Azure caduca

Los secretos de cliente de Azure tienen fecha de caducidad. Cuando caduque, crea uno nuevo en el portal de Azure y actualiza `CLIENT_SECRET` en el fichero `.env`. Reinicia el backend para que lo cargue.

---

## Requisitos de hardware

El sistema incluye un modelo de inteligencia artificial (transformer) que se carga en memoria al arrancar el backend. Esto tiene un impacto directo en los requisitos del servidor:

| Recurso | Mínimo recomendado |
|---|---|
| RAM | 6 GB libres |
| CPU | 4 núcleos |
| Almacenamiento | 5 GB (modelo ~3 GB + dependencias) |
| Python | 3.9 — versiones superiores pueden tener incompatibilidades con PyTorch |

> Si el servidor no tiene suficiente RAM, el backend arrancará pero el análisis de mensajes fallará silenciosamente. En los logs aparecerá un mensaje de tipo `AVISO: Modelo final no cargado`.

---

## Adaptación para tu organización

### Filtro de usuarios

Por defecto el sistema solo analiza usuarios cuyo email contiene `.tfg@`. Este filtro existe por motivos del proyecto académico original y **debe cambiarse** antes de usar el sistema en una organización real.

Edita `backend/scheduler_tasks.py` y modifica esta línea:

```python
# Línea original (solo analiza usuarios .tfg):
TFG_FILTER = ".tfg@"

# Cámbiala por un fragmento del dominio de tu organización:
TFG_FILTER = "@tuempresa.com"
```

Si quieres analizar a todos los usuarios sin filtro, cambia también la línea que lo aplica:

```python
# Antes (con filtro):
tfg_users = [u for u in raw_users if TFG_FILTER in (u.get("userPrincipalName", "").lower())]

# Después (sin filtro):
tfg_users = raw_users
```

---

## Verificación — comprobar que todo funciona

### El backend arranca correctamente

Abre `http://localhost:8000/docs` en el navegador. Debería aparecer la documentación de la API. Si no carga, revisa los logs del terminal.

### El modelo NLP se cargó

En los logs del backend al arrancar deberías ver:
```
Modelo de Emociones cargado correctamente.
```
Si en cambio ves `AVISO: Modelo final no cargado`, el servidor no tiene suficiente RAM o la carpeta `models/final_teams/` está vacía o mal ubicada.

### La conexión con Azure funciona

Entra al dashboard y haz login. Si Azure devuelve un error `redirect_uri_mismatch`, el valor de `REDIRECT_URI` en el `.env` no coincide con el configurado en el portal de Azure — deben ser idénticos.

### La conexión con Supabase funciona

Ve a **Administración** en el dashboard. Si ves un error de conexión, comprueba que `SUPABASE_URL` y `SUPABASE_KEY` son correctos y que las tablas están creadas (paso 2.1).

### El análisis nocturno funciona

Lanza un análisis manual desde **Administración → Lanzar análisis ahora** y comprueba los logs. Deberías ver algo como:
```
Procesando X usuarios
Análisis completado en XX.Xs
Resumen: X analizados, X guardados, 0 errores.
```
Si el contador de usuarios es 0, revisa el filtro de usuarios descrito en la sección anterior.

---

## Resumen de variables de entorno

| Variable | Obligatoria | Descripción |
|---|---|---|
| `TENANT_ID` | Sí | ID del directorio de Azure AD |
| `CLIENT_ID` | Sí | ID de la app registrada en Azure |
| `CLIENT_SECRET` | Sí | Secreto de la app de Azure |
| `REDIRECT_URI` | Sí | URL de callback OAuth (`/auth/callback`) |
| `SUPABASE_URL` | Sí | URL del proyecto Supabase |
| `SUPABASE_KEY` | Sí | Service role key de Supabase |
| `SESSION_SECRET_KEY` | Sí | Clave para firmar las cookies de sesión |
| `FRONTEND_URL` | No | URL del frontend (por defecto: `http://localhost:5173`) |
| `APP_ORIGIN` | No | URL del backend (por defecto: `http://localhost:8000`) |
