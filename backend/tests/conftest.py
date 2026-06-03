"""Configuración común de pytest para estabilizar imports del backend.

Permite ejecutar la suite tanto desde `ceu-whysoserious/` como desde
`ceu-whysoserious/backend/`, conviviendo con imports de paquete (`backend.*`)
y algunos imports absolutos heredados (`db_client`, `scheduler_tasks`, etc.).
"""

from pathlib import Path
import sys


TESTS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = TESTS_DIR.parent
PROJECT_DIR = BACKEND_DIR.parent

for path in (str(PROJECT_DIR), str(BACKEND_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)
