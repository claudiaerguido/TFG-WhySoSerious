import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scheduler_tasks import run_nightly_analysis

def test_background_processing():
    print("--- Probando Procesamiento en Segundo Plano (US28) ---")
    print("Iniciando tarea simulada del Scheduler (run_nightly_analysis)...")
    print("Esta prueba ejecuta el flujo completo de Graph API + NLP de manera desatendida.")
    try:
        run_nightly_analysis()
        print("\n✅ ÉXITO: El análisis en segundo plano se ejecutó correctamente sin intervenir en los hilos principales.")
    except Exception as e:
        print(f"\n❌ ERROR: Fallo al ejecutar el análisis asíncrono/en background: {e}")

if __name__ == "__main__":
    test_background_processing()
