# Why So Serious - Guía de Ejecución

Este documento explica cómo levantar los entornos de desarrollo para el backend y el frontend del proyecto de forma local.

Para que la aplicación funcione correctamente, es necesario ejecutar ambos servidores en terminales separadas.

## Requisitos Previos

- **Python** (recomendado 3.8 o superior) para el backend
- **Node.js y npm** para el frontend

---

## 1. Ejecutar el Backend (FastAPI)

El backend está desarrollado en Python usando FastAPI. Sigue estos pasos abriendo una terminal en la raíz del proyecto:

1. **Navega a la carpeta del backend:**

   ```bash
   cd backend
   ```
2. **Activa el entorno virtual:**

   ```bash
   # En macOS o Linux


   # En Windows (CMD)
   # venv\Scripts\activate
   ```
3. **Instala las dependencias (si es la primera vez):**

   ```bash
   pip install -r requirements.txt
   ```
4. **Inicia el servidor de desarrollo:**

   ```bash
   uporqu

   ```

   *El servidor se iniciará y estará disponible en `http://localhost:8000`.*

---

## 2. Ejecutar el Frontend (React + Vite)

El frontend está desarrollado en React utilizando Vite. Mantén la terminal del backend abierta y abre **una nueva ventana de terminal** en la raíz del proyecto:

1. **Navega a la carpeta del frontend:**

   ```bash
   cd frontend
   ```
2. **Instala las dependencias (solo necesario la primera vez o si se añaden paquetes nuevos):**

   ```bash
   npm install
   ```
3. **Inicia el servidor de desarrollo del frontend:**

   ```bash
   npm run dev
   ```

   *El frontend estará disponible en tu navegador web en `http://localhost:5173`.*

---

## Notas de uso

- El backend debe estar siempre corriendo para que el frontend pueda hacer llamadas a la API (ver configuración de CORS en `backend/main.py`).
- Culaquier cambio que hagas en el código del backend (debido a `--reload`) o del frontend (Vite HMR) se reflejará automáticamente sin necesidad de reiniciar ambos servidores.
