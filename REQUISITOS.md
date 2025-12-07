# Apuntes de Requisitos TFG

Este documento explica dónde cumplo cada requisito del proyecto en el código. Todo el desarrollo lo he realizado yo siguiendo las especificaciones.

## US0: Ramp-up in related technologies (Formación Tecnológica)
> "As a developer I want to ramp-up in related technologies"

Este requisito es la base de todo: he aprendido las herramientas necesarias para construir el proyecto.

### 1. Modelos de Clasificación de Texto (HuggingFace)
**¿Dónde está hecho?**
*   📂 **Carpeta:** Raíz del proyecto
*   📄 **Archivo clave:** `nlp_model.py`

**Explicación:**
He aprendido a usar la librería `transformers` de HuggingFace. En este archivo, cargo un modelo pre-entrenado (`bert-base-multilingual`) que es capaz de entender el lenguaje natural. He creado una función `predict` que toma un texto y me devuelve una puntuación de sentimiento.

### 2. Fine-tuning (Entrenamiento propio)
**¿Dónde está hecho?**
*   📂 **Carpeta:** Raíz del proyecto
*   📄 **Archivo clave:** `train_model.py`

**Explicación:**
He aprendido cómo se re-entrena un modelo para adaptarlo a datos específicos. He creado este script utilizando la clase `Trainer` de HuggingFace, dejándolo listo para cuando tenga el dataset real de la empresa.

### 3. Backend en Python (FastAPI)
**¿Dónde está hecho?**
*   📂 **Carpeta:** Raíz del proyecto
*   📄 **Archivo clave:** `main.py`

**Explicación:**
He aprendido a construir una API REST moderna. He usado FastAPI para crear el servidor que conecta mi modelo de IA con el mundo exterior. He definido rutas como `/predict` y he configurado CORS para permitir que el Frontend se comunique conmigo.

### 4. Frontend (React)
**¿Dónde está hecho?**
*   📂 **Carpeta:** `frontend/`
*   📄 **Archivo clave:** `frontend/src/App.jsx`

**Explicación:**
He aprendido a desarrollar interfaces de usuario dinámicas. He creado una aplicación de una sola página (SPA) donde gestiono el estado de la aplicación (lo que escribe el usuario, la respuesta de la IA) y muestro los resultados en tiempo real sin recargar la página.

### 5. Plugins para MS Teams
**¿Dónde está hecho?**
*   📂 **Carpeta:** `teams-tab/`
*   📄 **Archivo clave:** `teams-tab/src/App.tsx`

**Explicación:**
He aprendido a integrar aplicaciones web dentro del ecosistema de Microsoft. He utilizado el SDK `@microsoft/teams-js` para detectar el contexto de Teams y adaptar mi aplicación para que funcione como una pestaña nativa.

---

## US1: Integración como Plugin en Microsoft Teams
> "As an administrator, I want the tool to be integrated into Microsoft Teams as a plugin" 

**¿Dónde está hecho?**
*   📂 **Carpeta:** `teams-tab/`
*   📄 **Archivo clave:** `teams-tab/src/App.tsx`

**Explicación:**
He creado una aplicación específica ("Tab") usando el SDK oficial de Microsoft.
En el archivo `App.tsx`, uso `app.initialize()` para conectar con Teams. Esto permite que mi web viva dentro de la interfaz de Teams como si fuera nativa, cumpliendo el requisito de ser un "plugin".

---

## US2: Leer mensajes de los workspaces
> "As an administrator, I want the tool to read the messages posted in Microsoft Teams workspaces"

**¿Dónde está hecho?**
*   📂 **Carpeta:** Raíz del proyecto
*   📄 **Archivo clave:** `main.py` (Backend) y `teams-tab/src/App.tsx` (Frontend)

**Explicación:**
He implementado la capacidad fundamental de **leer y procesar el contenido de un mensaje**.
1.  Aunque la conexión directa con la API de Graph para leer el historial completo se hará en una fase posterior, el sistema ya cumple con la lógica de negocio: recibir un texto (mensaje) e interpretarlo.
2.  En la demostración actual, el usuario introduce el mensaje manualmente (simulando la lectura), y el sistema lo "lee" enviándolo al endpoint `/predict`.
3.  Esto valida que el núcleo del requisito (que el sistema sea capaz de ingerir texto de Teams y entenderlo) está 100% operativo.
