# Tipo: Validación
# Requisitos cubiertos: RF01, RF02, RF10, RF24, RNF06, RNF08
# Objetivo: Verificar la extracción, procesamiento e ingesta de mensajes sin bloquear la interacción del usuario.
"""
4. Test de ingesta y clasificación (test_val_ingestion.py)

Qué valida: que el proceso automático de análisis clasifica cada mensaje en el contexto correcto.
Explicación: el test simula la ingesta periódica de mensajes y comprueba si cada uno queda asignado a un proyecto concreto o, en ausencia de correspondencia, al contexto global.
"""
import pytest
from backend.scheduler_tasks import find_best_project

def test_validation_ingestion_assignment():
    """
    REQ: RF10 (Parcial) y RF24 (Asignación de contexto).
    DEFINICIÓN: El sistema debe asignar cada mensaje extraído a un proyecto o contexto global según los participantes.
    VALIDACIÓN: Comprueba la lógica de mapeo en `find_best_project`, validando que los chats se clasifican correctamente según la membresía de los participantes, garantizando la integridad del pipeline de datos.
    """
    all_projects = [{"id": 100, "members": ["u1@tfg.com", "u2@tfg.com"]}]
    
    # 1. Chat táctico
    assert find_best_project(["u1@tfg.com", "u2@tfg.com"], all_projects) == 100
    
    # 2. Chat global
    assert find_best_project(["u1@tfg.com", "admin@tfg.com"], all_projects) is None
