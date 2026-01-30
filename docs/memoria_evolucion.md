
# Memoria del Proyecto: El Viaje del Modelo de Emociones

Este documento resume la **historia técnica** del proyecto, explicando qué hemos hecho, por qué lo hemos hecho y qué hemos conseguido. Es ideal para redactar la sección de "Desarrollo" y "Resultados" de tu TFG.

---

## 📅 Hito 0: El Punto de Partida ("Baseline")
- **Objetivo:** Tener algo que funcione rápido para comparar.
- **Solución:** Usamos un modelo estándar de Hugging Face (`bert-base-multilingual-uncased-sentiment`).
- **Resultado:** Nos da "Estrellas" (1 a 5).
- **Problema:** Es muy básico. Decir "Este proyecto me agobia" para él es simplemente "1 estrella (malo)", pero para RRHH es vital saber si es **Estrés** o **Enfado**.

---

## 🚀 Fase A: Selección del Modelo ("Casting")
- **Objetivo:** Encontrar un modelo de lenguaje que entienda español y emociones complejas.
- **Acción:** Probamos varios candidatos con el dataset `GoEmotions` y `XED`.
- **Ganador:** Elegimos una base **Mistral/PlanTL** (dependiendo de la decisión final de arquitectura) porque demostró mejor capacidad de comprensión del contexto laboral que los modelos más pequeños.

---

## 🛠️ Fase B: Adaptación al Contexto Teams ("Entrenamiento")
- **El Problema:** El modelo sabía español, pero no "idioma corporativo".
    - *Ejemplo:* "Queda pendiente" en español estándar es neutro. En un modelo genérico podría parecer preocupación.
- **La Solución (`train_teams.py`):**
    - Creamos un **Dataset Propio** (`teams_train_manual.csv`) con frases reales de entornos de trabajo (Jira, Teams, Dailies).
    - Definimos **7 Emociones Clave**: `TRISTEZA, ESTRES, ENFADO, SOBRECARGA, CANSANCIO, POSITIVO, NEUTRO`.
    - Entrenamos el modelo para detectar estas etiquetas específicamente.

---

## 🧪 Fase C: Refinamiento y "El Problema del Neutro"
Una vez teníamos el modelo Fase B, encontramos dos problemas graves en las pruebas reales:

### 1. "El Síndrome de la Alarma Falsa"
- **Problema:** El modelo marcaba "SOBRECARGA" cada vez que leía la palabra "pendiente" o "revisar", aunque la frase fuera tranquila (*"Queda pendiente revisar esto mañana"*).
- **Solución (`train_polish.py`):**
    - Creamos un **Dataset Anti-Trigger**.
    - Enseñamos al modelo ejemplos explícitos de que "pendiente" puede ser NEUTRO.
    - Implementamos lógica de **Fallback**: Si la confianza de las emociones es baja (<0.35), forzamos la salida a **NEUTRO**.

### 2. "La Ceguera ante la Urgencia"
- **Problema:** Al arreglar lo anterior, el modelo se volvió miedoso y dejó de detectar urgencias reales (*"Voy tarde con el informe"*). El Recall de Sobrecarga bajó al 73%.
- **Solución Final:**
    - Añadimos ~20 ejemplos manuales de **Sobrecarga Real** ("No llego", "Deadline", "Fuego").
    - Re-entrenamos con un "Polish" (pulido fino).
    - **Resultado:** El Recall subió al **80%** sin romper la detección de neutros.

---

## 🏆 Validación Final: El "Gold Set"
Para no hacernos trampas al solitario, creamos un archivo sagrado: `evaluate_goldset.py`.
- Usamos 120 frases que el modelo **nunca había visto**.
- **Resultados Finales:**
    - ✅ **Neutros Seguros:** Cero falsos positivos en frases de gestión ("pendiente", "agendar").
    - ✅ **Sensibilidad:** Detectamos el 80% de las situaciones de Sobrecarga/Urgencia.
    - ✅ **Estrellas vs Emociones:** El sistema permite ver la visión simple (Baseline) y la compleja (Final) con un clic.

---

## 🧩 Arquitectura Final (Resumen Técnico)
1.  **Frontend (React):** Interfaz limpia que pide predicción.
2.  **Backend (FastAPI - `main.py`):** Recibe la petición.
3.  **Cerebro (`nlp_model.py`):**
    - Carga modelo `.pt` optimizado.
    - Aplica Umbrales (`thresholds_phaseB.json`).
    - Filtra con lógica de negocio (Neural Gating).
4.  **Salida:** JSON con probabilidades exactas y alertas visuales.

Hemos pasado de un modelo que "adivinaba estrellas" a un sistema capaz de distinguir entre "estar cansado" y "estar quemado (burnout)".
