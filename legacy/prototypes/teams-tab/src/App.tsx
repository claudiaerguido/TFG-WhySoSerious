import { useState, useEffect } from 'react'
import { app } from '@microsoft/teams-js'
import './App.css'

// Definimos tipos para nuestros datos
interface AnalysisResult {
  label: string;
  score: number;
}

function App() {
  // 1. ESTADO DE TEAMS (Contexto)
  const [inTeams, setInTeams] = useState(false);
  const [contextString, setContextString] = useState<string>("");

  // 2. LA DESPENSA (Estado de la App)
  const [inputText, setInputText] = useState('')
  const [manualResult, setManualResult] = useState<AnalysisResult | null>(null)

  // ... (useEffect initTeams) ...

  // 3. LAS INSTRUCCIONES (Funciones)
  const handleManualPredict = async () => {
    if (!inputText) return;

    try {
      const response = await fetch('http://127.0.0.1:8000/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: inputText })
      });
      const data = await response.json();
      setManualResult(data);
    } catch (error) {
      console.error("Error al analizar:", error);
      alert("Error al conectar con el backend");
    }
  };


  // Inicializar Teams SDK al arrancar
  useEffect(() => {
    const initTeams = async () => {
      try {
        await app.initialize();
        const context = await app.getContext();
        setInTeams(true);
        setContextString(context.user?.userPrincipalName || "Usuario desconocido");
      } catch (e) {
        console.log("No estamos en Teams o falló la inicialización:", e);
        setInTeams(false);
      }
    };
    initTeams();
  }, []);

  // 3. LAS INSTRUCCIONES (Funciones)


  // 4. EL EMPLATADO (HTML/JSX)
  return (
    <div className="container">
      <h1>Detector de Estrés (Teams Tab)</h1>

      {/* Badge de conexión a Teams */}
      {inTeams ? (
        <div className="teams-badge">Conectado como: {contextString}</div>
      ) : (
        <div className="teams-badge warning">Modo Web (Fuera de Teams)</div>
      )}

      <div className="card">
        <h2>Prueba Manual</h2>

        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Escribe aquí un mensaje (ej: Estoy muy agobiado)..."
          rows={3}
          className="input-text"
        />

        <br />

        <button onClick={handleManualPredict} className="btn-analyze">
          Analizar Texto
        </button>

        {manualResult && (
          <div className="result-box">
            <p><strong>Resultado:</strong> {manualResult.label}</p>

            {/* Explicación amigable */}
            <p className="result-explanation">
              {manualResult.label === '1 star' && "😡 Muy Negativo (Riesgo Alto de Burnout)"}
              {manualResult.label === '2 stars' && "😟 Negativo (Estrés Alto)"}
              {manualResult.label === '3 stars' && "😐 Neutral (Estrés Moderado)"}
              {manualResult.label === '4 stars' && "🙂 Positivo (Buen ambiente)"}
              {manualResult.label === '5 stars' && "😁 Muy Positivo (Excelente)"}
            </p>

            <p><strong>Confianza:</strong> {(manualResult.score * 100).toFixed(2)}%</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default App

