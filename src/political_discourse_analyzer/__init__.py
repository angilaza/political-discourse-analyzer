"""
Political Discourse Analyzer

Una herramienta para analizar y comprender programas electorales y discursos políticos
utilizando inteligencia artificial y procesamiento de lenguaje natural.

Este paquete proporciona:
- Análisis de programas electorales
- Búsqueda semántica en documentos políticos
- Interfaz conversacional para consultas
- Almacenamiento y análisis de interacciones
"""

__version__ = "0.1.0"
__author__ = "Tu Nombre"
__email__ = "tu.email@ejemplo.com"

from pathlib import Path

# Rutas importantes del proyecto
PACKAGE_ROOT = Path(__file__).parent
PROJECT_ROOT = PACKAGE_ROOT.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROGRAMS_DIR = DATA_DIR / "programs"
DB_DIR = DATA_DIR / "db"

# Asegurar que los directorios necesarios existen
DATA_DIR.mkdir(exist_ok=True)
PROGRAMS_DIR.mkdir(exist_ok=True)
DB_DIR.mkdir(exist_ok=True)

# Exportar versión
__all__ = ["__version__"]