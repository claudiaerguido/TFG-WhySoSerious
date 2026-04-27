# Tipo: Validación
# Requisitos cubiertos: RF04, RF19 (Parcial)
# Objetivo: Verificar la asignación contextual de mensajes durante la ingesta automática.
"""
4. Test de ingesta y clasificación (test_val_ingestion.py)

Qué valida: que el proceso automático de análisis clasifica cada mensaje en el contexto correcto.
Explicación: el test simula la ingesta periódica de mensajes y comprueba si cada uno queda asignado a un proyecto concreto o, en ausencia de correspondencia, al contexto global.
"""
import pytest
from backend.scheduler_tasks import find_best_project

def test_validation_ingestion_assignment():
    """
    REQ: RF04 y RF19 (Parcial).
    DEFINICIÓN: El sistema debe contextualizar cada mensaje en el ámbito organizativo correspondiente durante el procesamiento automático.
    VALIDACIÓN: Comprueba la lógica de mapeo en `find_best_project`, validando que los chats se clasifican correctamente según la membresía de los participantes y que el mensaje se asocia a un proyecto o al contexto global.
    """
    all_projects = [{"id": 100, "members": ["u1@tfg.com", "u2@tfg.com"]}]
    
    # 1. Chat táctico
    assert find_best_project(["u1@tfg.com", "u2@tfg.com"], all_projects) == 100
    
    # 2. Chat global
    assert find_best_project(["u1@tfg.com", "admin@tfg.com"], all_projects) is None
