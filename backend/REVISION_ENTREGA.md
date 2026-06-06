# Plan de revisión backend — entrega tribunal

En cada archivo revisar:
- Comentarios innecesarios, obvios o desactualizados → eliminar
- Código muerto (funciones sin usar, imports sin usar, variables sin usar)
- TODO / FIXME / prints de debug que no deberían estar
- Docstrings excesivos o que solo repiten el nombre de la función
- Coherencia de nombres con el resto del sistema
- Nada que rompa, solo limpieza

**Tono de los comentarios:**
- Que suenen escritos por una persona, no por una IA
- Eliminar frases típicas de IA: "Este método se encarga de...", "La función realiza...", "Se procede a...", "A continuación se...", "Cabe destacar que...", estructuras de lista exhaustiva donde sobra una línea
- Los comentarios que queden deben ser cortos, directos, en primera o tercera persona informal — como anotaría cualquier desarrollador en su propio código
- Si un comentario no aportaría nada a alguien leyendo el código por primera vez, fuera

---

## Orden de revisión

### 1. `db_client.py` (15 líneas)
Arrancar por el más pequeño. Solo inicializa el cliente Supabase.
- ¿Hay algún print o comentario de debug?
- ¿Las variables tienen nombres claros?

### 2. `message_analyzer.py` (17 líneas)
Muy pequeño. Revisar si sigue en uso o es código residual.
- ¿Se importa desde algún otro archivo?
- Si no se usa, valorar eliminarlo.

### 3. `db_client.py` + `db_repository.py` (222 líneas)
Todas las queries a Supabase.
- Eliminar comentarios de sección obvios (`# 1. CARGA DE DATOS`, etc.)
- Funciones sin usar
- Prints de debug

### 4. `logic/risk_model.py` (127 líneas)
Núcleo del cálculo de riesgo (Pearson, semáforo).
- Comentarios que explican el QUÉ en vez del POR QUÉ → eliminar
- Asegurarse de que las constantes de umbral (35%, 20%) están bien documentadas con una línea que explique la decisión

### 5. `nlp_model.py` (150 líneas)
Inferencia del transformer.
- Revisar que MODEL_PATH apunta a `final_teams` ✅ (ya verificado)
- Eliminar comentarios de sección redundantes
- Comprobar que las etiquetas en el código coinciden con las 5 operativas

### 6. `services/permissions_service.py` (72 líneas)
RBAC. Pequeño, revisar que los roles están bien definidos y sin código muerto.

### 7. `services/risk_service.py` (417 líneas)
Agregación de riesgo para las respuestas API. El más complejo de los services.
- Funciones sin usar
- Comentarios de bloque excesivos
- Prints de debug

### 8. `scheduler_tasks.py` (150 líneas)
Pipeline nocturno (APScheduler + NLP + Supabase).
- Prints de debug vs logs reales
- Código comentado que no se usa

### 9. `auth/auth_graph_app.py` (363 líneas)
Auth app-only (token de aplicación para el scheduler).
- Código muerto o comentado
- Prints de debug

### 10. `auth/auth_graph_web.py` (231 líneas)
Auth web (OAuth flow para el usuario).
- Idem que app.py

### 11. `main.py` (552 líneas)
El más grande. Todas las rutas FastAPI.
- Imports sin usar
- Rutas comentadas o de prueba que no deberían estar
- Prints de debug
- Comentarios de sección excesivos

### 12. `scripts/training/train_teams.py`
- Comentarios del docstring del WeightedTrainer que explican lo obvio
- Verificar que TARGET_LABELS son las 5 correctas ✅ (ya verificado)

### 13. `scripts/training/evaluate_goldset.py`
- Verificar que TARGET_LABELS incluye TRISTEZA/POSITIVO_ALIVIO solo para el gold set (que sí las tiene como columnas con soporte 0) o limpiarlas si confunden

### 14. Tests (`tests/`)
- Revisar que los tests pasan
- Eliminar tests marcados como legacy si ya no aplican
- Asegurarse de que los nombres de test son descriptivos

---

---

## Frontend — Orden de revisión

Mismos criterios que el backend: comentarios que suenen escritos por ti, imports sin usar, código muerto, console.log de debug.

### 1. `utils/risk.js` (25 líneas)
### 2. `context/authState.js` (8 líneas)
### 3. `context/AuthContext.jsx` (30 líneas)
### 4. `components/RequireAuth.jsx` (21 líneas)
### 5. `hooks/useRiskFilters.js` (56 líneas)
### 6. `theme.js` (66 líneas)
### 7. `main.jsx` (52 líneas)
### 8. `api/api.js` (147 líneas)
### 9. `components/RiskCard.jsx` (128 líneas)
### 10. `pages/Login/LoginPage.jsx` (113 líneas)
### 11. `pages/index.js`
### 12. `components/RiskTrendChart.jsx` (254 líneas)
### 13. `components/AppShell.jsx` (245 líneas)
### 14. `pages/Teams/TeamsPage.jsx` (165 líneas)
### 15. `pages/EmployeeProfile/EmployeeProfilePage.jsx` (213 líneas)
### 16. `pages/Profile/ProfilePage.jsx` (268 líneas)
### 17. `pages/Dashboard/DashboardPage.jsx` (293 líneas)
### 18. `pages/ProjectDetail/ProjectDetailPage.jsx` (516 líneas)

---

## Lo que NO tocar
- Lógica de negocio que funciona
- Nombres de funciones que se importan desde otros módulos
- El `.env` ni credenciales
- `train_polish.py` (experimento archivado, no es código de producción)
