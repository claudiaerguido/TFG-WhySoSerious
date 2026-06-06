# Arquitectura del Sistema: Análisis de Riesgo Organizacional

Este documento detalla la estructura técnica, la organización del proyecto y la metodología analítica empleada en el sistema. Ha sido diseñado para servir de base técnica en la memoria del Trabajo de Fin de Grado (TFG).

## 1. Estructura de Directorios del Backend

El proyecto sigue una organización modular que separa el código productivo de los scripts de soporte y el historial de desarrollo.

```text
backend/
  ├── main.py                # Punto de entrada de la API FastAPI
  ├── scheduler_tasks.py     # Motor de ingesta y análisis programado
  ├── db_client.py           # Gestión de conexión Singleton a Supabase
  ├── db_repository.py       # Única fuente de verdad para acceso a datos
  ├── nlp_model.py           # Implementación del modelo de IA (HuggingFace)
  ├── message_analyzer.py    # Orquestador del análisis de texto
  ├── auth_graph_app.py      # Autenticación delegada (Permisos de Aplicación)
  ├── auth_graph_web.py      # Autenticación de usuario (OAuth/PKCE)
  │
  ├── logic/                 # Lógica matemática pura
  │   └── risk_model.py      # Motor de cálculo (Pearson) y constantes
  │
  ├── services/              # Capa de servicios (Lógica de negocio)
  │   ├── risk_service.py    # Cálculo de métricas, tendencias y desgloses
  │   └── permissions_service.py # Control de acceso y visibilidad por rol
  │
  ├── scripts/               # Herramientas auxiliares
  │   └── training/          # Entrenamiento y evaluación de modelos NLP
  │
  ├── logs/                  # Directorio reservado para trazas locales
  └── tests/                 # Pruebas unitarias e integración
```

## 2. Capa de Datos y Persistencia

El sistema utiliza **Supabase** como motor de base de datos relacional. El acceso a los datos ha sido estandarizado a través de un repositorio centralizado.

- **`db_repository.py`**: Implementa la técnica de **Join Manual Robusto** para garantizar la integridad de las listas de miembros en equipos y proyectos, superando las limitaciones de las relaciones automáticas en esquemas dinámicos.
- **Relaciones Clave**:
    - `teams`: Estructuras organizativas (Departamentos).
    - `projects`: Unidades de ejecución táctica.
    - `risk_metrics`: Almacén de indicadores calculados por mensaje.

## 3. Metodología de Cálculo de Riesgo

La evaluación del riesgo se basa en el **Coeficiente de Correlación de Pearson**, permitiendo una ponderación estadística en lugar de un conteo lineal de palabras clave.

### Niveles de Análisis
1.  **Riesgo Individual Global**: Bienestar consolidado del colaborador.
2.  **Riesgo Individual por Proyecto**: Nivel de estrés derivado de una iniciativa concreta.
3.  **Riesgo de Equipo (Global)**: Salud emocional del departamento.
4.  **Riesgo de Proyecto (Táctico)**: Indicador de salud colectiva en una unidad de trabajo.

### Clasificación Semafórica
- **Crítico (🔴 >= 35%)**: Intervención inmediata requerida.
- **En Observación (🟡 >= 20%)**: Monitorización preventiva.
- **Estable (🟢 < 20%)**: Clima laboral saludable.

## 4. Gestión de Visibilidad y Permisos

Se ha implementado un motor de permisos estricto en la capa de servicios (`permissions_service.py`):
- **Admin**: Acceso total a la analítica organizacional.
- **Manager**: Visibilidad restringida a sus Equipos o Proyectos asignados.
- **Employee**: Rol estándar sin acceso a dashboards analíticos.

---
*Este documento constituye la especificación técnica oficial del sistema para el TFG.*
