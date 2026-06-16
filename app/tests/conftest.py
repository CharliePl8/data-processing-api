import os
import sys

# Asegurarse de que el directorio raíz del proyecto esté en sys.path para que los módulos puedan ser importados correctamente durante las pruebas.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

if PROJECT_ROOT not in sys.path:
	sys.path.insert(0, PROJECT_ROOT)
