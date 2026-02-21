import { useState } from 'react'
import './App.css'

// Mapa para traducir las etiquetas técnicas a texto amigable
const LABEL_DISPLAY_NAMES = {
  "TRISTEZA": "Tristeza / Desánimo",
  "ESTRES_ANSIEDAD": "Estrés / Ansiedad",
  "ENFADO_IRRITACION": "Enfado / Irritación",
  "SOBRECARGA_URGENCIA": "Sobrecarga / Urgencia",
  "CANSANCIO_FATIGA": "Cansancio / Fatiga",
  "POSITIVO_ALIVIO": "Positivo / Alivio",
  "NEUTRO": "Neutro / Informativo"
};

// Helper antibalas para parsear números
const parseScore = (val) => {
  if (typeof val === 'number') return val;
  if (typeof val === 'string') {
    // Reemplazar coma por punto y limpiar basura
    const clean = val.replace(',', '.').replace(/[^\d.-]/g, '');
    return parseFloat(clean) || 0;
  }
  return 0;
};

// ==========================================
// 1. SUB-COMPONENTE: SECCIÓN DE TEAMS
// Agrupa toda la lógica de cargar chats y analizarlos
// ==========================================
const TeamsSection = () => {
  // Estado local para esta sección
  const [chats, setChats] = useState([]);          // Lista de chats cargados
  const [selectedChat, setSelectedChat] = useState(''); // ID del chat elegido
  const [analysis, setAnalysis] = useState(null);  // Resultado del análisis (JSON)
  const [loading, setLoading] = useState(false);   // Para mostrar "Cargando..."

  // --- Función A: Cargar la lista de chats ---
  const loadChats = async () => {
    try {
      // Pedimos al backend (/me/chats)
      // 'credentials: include' es vital para que envíe la cookie de sesión
      const res = await fetch('http://localhost:8000/me/chats', { credentials: 'include' });

      // Si el backend dice que no estamos logueados, nos redirige
      if (res.redirected) {
        window.location.href = res.url;
        return;
      }

      const data = await res.json();
      if (data.chats) setChats(data.chats);
      else alert("No se pudieron cargar chats (¿Login?)");
    } catch (e) {
      alert("Error cargando chats: " + e.message);
    }
  };

  // --- Función B: Analizar el chat seleccionado ---
  const analyzeChat = async () => {
    if (!selectedChat) return;
    setLoading(true);
    setAnalysis(null); // Limpiamos resultado anterior
    try {
      // Llamamos al endpoint mágico del backend
      const res = await fetch(`http://localhost:8000/chats/${selectedChat}/analyze`, { credentials: 'include' });
      const data = await res.json();
      setAnalysis(data);
    } catch (e) {
      alert("Error analizando: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  // --- Función Auxiliar: Pintar un mensajito individual ---
  const renderMessageDetail = (msg, idx) => {
    // Filtramos etiquetas con confianza > 40%
    const highRisks = Object.entries(msg.analysis).filter(([, v]) => v > 0.4);
    const isNeutral = highRisks.length === 0;

    return (
      <div key={idx} className="message-item">
        <div className="message-meta">
          {msg.author || 'Desc'} - {new Date(msg.date).toLocaleTimeString()}
        </div>
        <div className="message-content">"{msg.message}"</div>
        <div className="tags-container">
          {highRisks.map(([k, v]) => (
            <span key={k} className={`tag-badge ${k.includes('POSITIVO') ? 'tag-positive' : 'tag-negative'}`}>
              {/* Mostramos nombre corto y porcentaje */}
              {k.split('_')[0]} ({(v * 100).toFixed(0)}%)
            </span>
          ))}
          {isNeutral && <span className="tag-badge tag-neutral">Neutro</span>}
        </div>
      </div>
    );
  };

  // --- Renderizado Visual de TeamsSection ---
  return (
    <div>
      {/* Controles: Botón Cargar y Select */}
      <div className="teams-controls">
        <button onClick={loadChats} className="btn-analyze">
          🔄 Cargar Mis Chats
        </button>

        {chats.length > 0 && (
          <select
            value={selectedChat}
            onChange={e => setSelectedChat(e.target.value)}
            className="chat-select"
          >
            <option value="">-- Selecciona un Chat --</option>
            {chats.map(c => (
              <option key={c.id} value={c.id}>
                {c.topic || c.display_name || c.id.substring(0, 20) + '...'}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Botón Analizar (Solo si hay chat seleccionado) */}
      {chats.length > 0 && (
        <button
          onClick={analyzeChat}
          disabled={!selectedChat || loading}
          className="btn-analyze btn-analyze-teams"
        >
          {loading ? 'Analizando...' : '📊 Analizar Chat Completo'}
        </button>
      )}

      {/* Resultados Visuales (Gráficos y Lista) */}
      {analysis && analysis.summary && (
        <div className="result-box">
          <h3>Resumen del Chat</h3>

          {/* Tarjetas de Riesgo */}
          <div className="stats-grid">
            <div className="stat-card stat-overload">
              🛡️ Riesgo Sobrecarga: <strong>{analysis.summary.risks_detected.SOBRECARGA_URGENCIA}</strong>
            </div>
            <div className="stat-card stat-stress">
              😰 Riesgo Estrés: <strong>{analysis.summary.risks_detected.ESTRES_ANSIEDAD}</strong>
            </div>
            <div className="stat-card stat-fatigue">
              😪 Riesgo Fatiga: <strong>{analysis.summary.risks_detected.CANSANCIO_FATIGA}</strong>
            </div>
          </div>

          <h4>Detalle de Mensajes ({analysis.summary.analyzed})</h4>
          <div className="messages-list">
            {analysis.details.map(renderMessageDetail)}
          </div>
        </div>
      )}
    </div>
  );
};

// ==========================================
// 2. COMPONENTE NUEVO: INDICADOR DE EQUIPO (US11)
// ==========================================
const TeamRiskDashboard = () => {
  const [teamRisk, setTeamRisk] = useState(null);
  const [loading, setLoading] = useState(false);
  const [teamIdInput, setTeamIdInput] = useState("1"); // Por defecto consultamos el equipo 1

  const fetchTeamRisk = async () => {
    if (!teamIdInput) return;
    setLoading(true);
    try {
      const parsedTeamId = Number(teamIdInput);
      const url = `http://localhost:8000/api/team/risk?team_id=${parsedTeamId}`;
      console.log(`[FRONTEND] 🚀 Llamando a Backend: ${url}`);

      const res = await fetch(url);
      const data = await res.json();

      console.log(`[FRONTEND] 📦 Respuesta recibida para team_id ${parsedTeamId}:`, data);
      setTeamRisk(data);
    } catch (e) {
      alert("Error cargando riesgo del equipo: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  // Función para determinar el color del semáforo/tarjeta
  const getRiskColor = (level) => {
    if (level === "Verde") return "#d4edda"; // Verde claro
    if (level === "Amarillo") return "#fff3cd"; // Amarillo claro
    if (level === "Rojo") return "#f8d7da"; // Rojo claro
    return "#f8f9fa"; // Gris por defecto
  };

  const getRiskTextColor = (level) => {
    if (level === "Verde") return "#155724";
    if (level === "Amarillo") return "#856404";
    if (level === "Rojo") return "#721c24";
    return "#333";
  };

  return (
    <div className="card" style={{ marginBottom: "20px" }} translate="no">
      <h2>📊 Panel del Mánager (Métricas de Equipo)</h2>

      <div className="teams-controls" style={{ marginBottom: "15px", display: "flex", gap: "10px", alignItems: "center" }}>
        <label>ID del Equipo:</label>
        <input
          type="number"
          value={teamIdInput}
          onChange={(e) => setTeamIdInput(e.target.value)}
          style={{ width: "60px", padding: "5px" }}
        />
        <button onClick={fetchTeamRisk} disabled={loading} className="btn-analyze">
          {loading ? "Calculando..." : "Analizar Equipo"}
        </button>
      </div>

      {teamRisk && teamRisk.status === "ok" && (
        <div
          style={{
            marginTop: "15px",
            padding: "20px",
            borderRadius: "10px",
            backgroundColor: getRiskColor(teamRisk.risk_level),
            color: getRiskTextColor(teamRisk.risk_level),
            textAlign: "center",
            border: `2px solid ${getRiskTextColor(teamRisk.risk_level)}`
          }}
        >
          {teamRisk.sample_size === 0 ? (
            <p>No hay datos o el equipo está vacío.</p>
          ) : (
            <>
              <h3 style={{ margin: "0 0 10px 0", fontSize: "1.5rem" }}>
                Riesgo General: {teamRisk.risk_level}
              </h3>
              <div style={{ fontSize: "3rem", fontWeight: "bold", margin: "10px 0" }}>
                {teamRisk.risk_score_percentage}%
              </div>
              <p style={{ margin: 0, fontSize: "0.9rem" }}>
                Basado en mensajes de {teamRisk.sample_size} usuarios en 7 días.
              </p>
              <div style={{ marginTop: "10px", fontSize: "0.8rem", opacity: 0.8 }}>
                (0% = Relajado | 100% = Burnout Grave)
              </div>
            </>
          )}
        </div>
      )}

      {teamRisk && teamRisk.error && (
        <div style={{ color: "red", marginTop: "10px" }}>
          Error: {teamRisk.error}
        </div>
      )}
    </div>
  );
};

// ==========================================
// 3. COMPONENTE PRINCIPAL (LA PÁGINA)
// ==========================================
function App() {
  // Estado para la prueba manual
  const [inputText, setInputText] = useState('')
  const [modelType, setModelType] = useState('final')
  const [manualResult, setManualResult] = useState(null)

  // Lógica de la prueba manual (simula lo que hace el backend de Teams pero con input de usuario)
  const handleManualPredict = async () => {
    if (!inputText) return;
    try {
      const response = await fetch('http://localhost:8000/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: inputText, model: modelType })
      });
      const data = await response.json();
      console.log("Manual Result:", data); // DEBUG
      setManualResult(data);
    } catch (error) {
      alert("Error al conectar con el backend:" + error);
    }
  };

  return (
    <div className="container">
      <h1 style={{ color: '#0078d4', fontSize: '2.5rem', marginBottom: '10px' }}>
        Observatorio de Salud Mental - TFG
      </h1>
      <p style={{ color: '#666', marginBottom: '30px' }}>
        Análisis de sentimientos y detección de riesgos en el entorno laboral.
      </p>

      {/* TARJETA 0: DASHBOARD DEL MANAGER (NUEVA US11) */}
      <TeamRiskDashboard />

      {/* TARJETA 1: INTEGRACIÓN TEAMS */}
      <div className="card teams-card">
        <h2>Integración Microsoft Teams</h2>

        {/* Botones de Login/Logout */}
        <div className="auth-buttons-container">
          <button
            onClick={() => window.location.href = 'http://localhost:8000/login'}
            className="btn-teams-connect"
          >
            Auth: Conectar con Teams
          </button>
          <button
            onClick={() => window.location.href = 'http://localhost:8000/logout'}
            className="btn-logout"
          >
            Logout
          </button>
        </div>

        {/* Aquí insertamos el componente que definimos arriba */}
        <TeamsSection />
      </div>

      {/* TARJETA 2: PRUEBA MANUAL (Lo antiguo) */}
      <div className="card">
        <h2>Prueba Manual</h2>
        <div className="manual-controls">
          <label style={{ marginRight: '10px' }}>Modelo:</label>
          <select
            value={modelType}
            onChange={(e) => setModelType(e.target.value)}
          >
            <option value="final">Final (Multilabel)</option>
            <option value="baseline">Baseline (Sentimiento)</option>
          </select>
        </div>

        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Escribe aquí... (ej: No llego a la entrega)"
          rows="3"
        />

        <button onClick={handleManualPredict} className="btn-analyze">
          Analizar Texto
        </button>

        {/* Pequeño renderizado para resultados manuales */}
        {manualResult && (
          <div className="result-box">
            {manualResult.model === 'baseline' ? (
              <div style={{ textAlign: 'center', padding: '10px' }}>
                <p style={{ fontSize: '1.1rem', marginBottom: '10px' }}>
                  Resultado: <strong>{manualResult.sentiment_label}</strong>
                </p>
                <div style={{ fontSize: '2rem', color: '#ffc107', marginBottom: '10px' }}>
                  {"★".repeat(manualResult.stars || 0)}{"☆".repeat(5 - (manualResult.stars || 0))}
                </div>
                <p style={{ color: '#666', fontSize: '0.9rem' }}>
                  Confianza: {(manualResult.confidence * 100).toFixed(1)}%
                </p>
              </div>
            ) : (
              <div>
                <h4>📊 Análisis de Sentimientos</h4>
                {Object.entries(manualResult.labels)
                  .sort(([, a], [, b]) => parseScore(b) - parseScore(a)) // Sort seguro usando antibalas
                  .map(([label, rawScore]) => {
                    // BLINDAJE ANTI-ERRORES
                    const score = parseScore(rawScore);
                    const threshold = manualResult.thresholds ? manualResult.thresholds[label] : 0.5;
                    const isDetected = score >= threshold;
                    const pct = (score * 100).toFixed(1);

                    // DEBUG: Log para ver qué está pasando
                    console.log(`[DEBUG UI] Label: ${label}, Raw: ${rawScore}, Safe: ${score}, Pct: ${pct}%`);

                    // Determine color class
                    // INCLUIMOS TODAS LAS EMOCIONES NEGATIVAS
                    let barClass = "bar-neutral";
                    if (['TRISTEZA', 'ESTRES_ANSIEDAD', 'ENFADO_IRRITACION', 'SOBRECARGA_URGENCIA', 'CANSANCIO_FATIGA'].includes(label)) {
                      if (score > 0.6) barClass = "bar-high";      // Rojo (Grave)
                      else if (score > 0.3) barClass = "bar-med"; // Amarillo (Medio)
                      else barClass = "bar-low";                  // Verde (Leve)
                    } else if (label === 'POSITIVO_ALIVIO') {
                      barClass = "bar-low"; // Verde siempre para positivo
                    }

                    return (
                      <div key={label} style={{ marginBottom: '8px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                          <span style={{ fontWeight: isDetected ? 'bold' : 'normal' }}>
                            {LABEL_DISPLAY_NAMES[label] || label}
                          </span>
                          <span>{pct}%</span>
                        </div>
                        <div className="progress-container">
                          <div
                            className={`progress-bar ${barClass}`}
                            style={{ width: `${pct}%` }}
                          >
                          </div>
                        </div>
                      </div>
                    );
                  })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default App
