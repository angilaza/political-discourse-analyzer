# Political Discourse Analyzer

Una herramienta de análisis de discursos políticos mediante IA que permite explorar y comprender programas electorales a través de una interfaz conversacional.

## 🎯 Objetivo

Esta aplicación permite a los usuarios explorar y comprender programas electorales y discursos políticos a través de una interfaz web sencilla. Ofrece dos modos de interacción:

- **Modo Neutral**: Proporciona respuestas objetivas y directas sobre los contenidos políticos indexados (programas electorales).
- **Modo Personal**: Utiliza un enfoque más contextualizado y conversacional para explicar las propuestas políticas.

## 🏗️ Arquitectura

### Backend (FastAPI + OpenAI)

- **FastAPI**: Framework web moderno para crear APIs con Python
- **OpenAI Assistants API**: Para procesamiento de lenguaje natural y búsqueda semántica
- **PostgreSQL**: Base de datos principal para almacenamiento de interacciones
- **SQLAlchemy**: ORM para gestión de base de datos

### Frontend (React)

- Interfaz de usuario moderna y responsiva
- Diseño minimalista y funcional
- Soporte para ambos modos de interacción

## 🚀 Instalación

### Prerrequisitos

- Python 3.11 o superior
- Poetry (gestor de dependencias)
- Node.js y npm (para el frontend)

## 🚀 Instalación

### Prerrequisitos
- Python 3.11 o superior
- Poetry (gestor de dependencias)
- PostgreSQL 14
- Node.js y npm (para el frontend)

### Configuración del Entorno

1. Clonar el repositorio:

```bash
git clone https://github.com/tu-usuario/political-discourse-analyzer.git
cd political-discourse-analyzer
```

2. Configurar PostgreSQL:

```bash
# Crear usuario postgres (solo primera vez)
createuser -s postgres

# Verificar instalación
python -m political_discourse_analyzer.utils.db_management check

# Crear y configurar base de datos
python -m political_discourse_analyzer.utils.db_management setup
```

3. Configurar el entorno Python:

```bash
# Instalar Poetry si no está instalado
curl -sSL https://install.python-poetry.org | python3 -

# Instalar dependencias
poetry install

# Activar el entorno virtual
poetry shell
```

4. Configurar variables de entorno:

```bash
cp .env.example .env

# Editar .env y añadir:
OPENAI_API_KEY=tu_clave_api
MODEL_NAME=gpt-4
ENVIRONMENT=development
DB_USER=postgres
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432
DB_NAME=political_discourse
```

### Comandos de Base de Datos

```bash
# Ver tablas existentes
python -m political_discourse_analyzer.utils.db_management tables

# Resetear base de datos
python -m political_discourse_analyzer.utils.db_management reset

# Verificar estado de PostgreSQL
python -m political_discourse_analyzer.utils.db_management check
```

### Inicialización

1. Inicializar el sistema:

```bash
python -m src.political_discourse_analyzer.core.initialize
```

2. Ejecutar el servidor de desarrollo:

```bash
python -m src.political_discourse_analyzer.core.main
```

## 📚 Uso

1. El servidor estará disponible en `http://localhost:8000`
2. La API incluye los siguientes endpoints:
   - `POST /search`: Para realizar consultas sobre programas electorales
   - `GET /`: Información sobre el estado del servicio

## 🔧 Desarrollo

### Estructura del Proyecto

```text
political-discourse-analyzer/
├── data/
│   ├── programs/     # Documentos políticos
│   └── db/           # Base de datos SQLite (desarrollo)
├── src/
│   └── political_discourse_analyzer/
│       ├── core/     # Núcleo de la aplicación
│       ├── models/   # Modelos de datos
│       ├── services/ # Servicios (DB, OpenAI, etc.)
│       └── utils/    # Utilidades
├── tests/
│   ├── conftest.py    # Configuración de pytest
│   ├── test_api/      # Tests de endpoints
│   ├── test_services/ # Tests de servicios
│   └── test_utils/    # Tests de utilidades
└── frontend/          # Interfaz de usuario React
```

### Comandos Útiles

```bash
# Verificar documentos
python -m src.political_discourse_analyzer.utils.document_checker

# Ejecutar tests
pytest

# Formatear código
black src/
```

## 🤝 Contribuir

1. Fork el repositorio
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## 📝 Licencia

[MIT](LICENSE)

## 🙏 Agradecimientos

- OpenAI por proporcionar la API de Asistentes
- A los contribuidores de las bibliotecas utilizadas

## 📬 Contacto

Angélica Laza - <angi.laza@hotmail.es>

Link del Proyecto: [https://github.com/angilaza/political-discourse-analyzer](https://github.com/angilaza/political-discourse-analyzer)
