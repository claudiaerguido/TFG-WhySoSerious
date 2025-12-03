import { useState } from 'react'
import './App.css'

function App() {
  // 1. LA DESPENSA (Estado)
  // Aquí guardamos los datos que pueden cambiar
  const [inputText, setInputText] = useState('')       // Lo que escribes
  const [manualResult, setManualResult] = useState(null) // La respuesta de la IA

  // 2. LAS INSTRUCCIONES (Funciones)
  // Esta función se ejecuta al pulsar el botón "Analizar"
  const handleManualPredict = async () => {
    if (!inputText) return; // Si está vacío, no hacemos nada

    try {
      // A. Llamamos al Backend
      const response = await fetch('http://127.0.0.1:8000/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: inputText })
      });

      // B. Leemos la respuesta
      const data = await response.json();

      // C. Guardamos el resultado en la despensa
      setManualResult(data);

    } catch (error) {
      alert("Error al conectar con el backend");
    }
  };

  // 3. EL EMPLATADO (HTML/JSX)
  // Esto es lo que se ve en la pantalla
  return (
    <div className="container">
      <h1>Detector de Estrés</h1>

      <div className="card">
        <h2>Prueba Manual</h2>

        {/* Caja de texto */}
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Escribe aquí... (ej: Estoy muy agobiado)"
          rows="3"
          className="input-text"
        />

        <br />

        {/* Botón */}
        <button onClick={handleManualPredict} className="btn-analyze">
          Analizar Texto
        </button>

        {/* Resultado (Solo se ve si ya tenemos respuesta) */}
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
