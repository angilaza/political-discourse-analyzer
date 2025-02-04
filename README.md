# Political Discourse Analyzer

Una herramienta de análisis de discursos políticos mediante IA que permite explorar y comprender programas electorales a través de una interfaz conversacional.

## 📌 Visión General

Political Discourse Analyzer es una herramienta innovadora diseñada para hacer más accesible y comprensible el análisis de programas electorales mediante el uso de inteligencia artificial. Esta aplicación permite a los usuarios interactuar con documentos políticos complejos de una manera intuitiva y conversacional.

## 🎯 Modos de Interacción

La aplicación ofrece dos modos distintos de análisis:

- **Modo Programas Electorales**
  - Análisis objetivo basado estrictamente en los documentos
  - Respuestas con citaciones directas de los programas
  - Ideal para investigación y consulta factual
  - Mantiene la neutralidad en las explicaciones

- **Modo Perspectiva Personal**
  - Enfoque contextualizado y conversacional
  - Explicaciones adaptadas al usuario
  - Relaciona diferentes aspectos de las propuestas
  - Facilita la comprensión de implicaciones prácticas

## 🏗️ Arquitectura Técnica

### Backend

- **FastAPI**: Framework web moderno para APIs
- **OpenAI Assistants API**: Procesamiento de lenguaje natural
- **PostgreSQL**: Base de datos para almacenamiento
- **SQLAlchemy**: ORM para gestión de base de datos

### Frontend

- **React + Vite**: Framework de desarrollo
- **TypeScript**: Tipado estático
- **Tailwind CSS**: Estilos y diseño
- **React Hooks**: Gestión de estado

## 🚀 Instalación y Configuración

### Prerrequisitos

- Python 3.11 o superior
- Poetry (gestor de dependencias)
- PostgreSQL 14
- Node.js y npm
- Cuenta en OpenAI (para API key)

### Configuración Inicial

1. **Clonar el Repositorio**

```bash
git clone https://github.com/angilaza/political-discourse-analyzer.git
cd political-discourse-analyzer
```

2. **Configurar PostgreSQL**

```bash
# Crear usuario postgres (solo primera vez)
createuser -s postgres

# Verificar instalación y crear base de datos
python -m political_discourse_analyzer.utils.db_management check
python -m political_discourse_analyzer.utils.db_management setup
```

3. **Configurar Variables de Entorno**

```bash
cp .env.example .env

# Editar .env con los siguientes valores:
OPENAI_API_KEY=tu_clave_api
MODEL_NAME=gpt-4
ENVIRONMENT=development
DB_USER=postgres
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432
DB_NAME=political_discourse
```

## 🔧 Gestión del Entorno de Desarrollo

### 1. Configuración del Entorno Virtual

```bash
# Instalar Poetry si no está instalado
curl -sSL https://install.python-poetry.org | python3 -

# Instalar dependencias del proyecto
poetry install

# Activar el entorno virtual
poetry shell
```

### 2. Secuencia de Inicialización

Después de activar el entorno virtual:

```bash
# 1. Verificar estado de la base de datos
python -m political_discourse_analyzer.utils.db_management check
python -m political_discourse_analyzer.utils.db_management tables

# 2. Inicializar el sistema (Vector Store y Asistentes)
python -m src.political_discourse_analyzer.core.initialize

# 3. Iniciar el servidor backend (en una terminal)
uvicorn src.political_discourse_analyzer.core.main:app --reload

# 4. En otra terminal (con el entorno activado):
cd frontend
npm install
npm run dev
```

### 3. Comandos de Desarrollo Diario

```bash
# Activar el entorno (al comenzar a trabajar)
cd political-discourse-analyzer
poetry shell

# Iniciar backend (en una terminal)
uvicorn src.political_discourse_analyzer.core.main:app --reload

# Iniciar frontend (en otra terminal)
cd frontend
npm run dev
```

### 4. Gestión de Base de Datos

```bash
# Ver tablas existentes
python -m political_discourse_analyzer.utils.db_management tables

# Resetear base de datos
python -m political_discourse_analyzer.utils.db_management reset

# Verificar estado de PostgreSQL
python -m political_discourse_analyzer.utils.db_management check
```

### 5. Solución de Problemas Comunes

1. **Problemas con el Entorno Virtual**

```bash
# Recrear el entorno
poetry env remove python
poetry install
```

2. **Errores de Dependencias**

```bash
# Actualizar dependencias
poetry update
```

3. **Reinicio Completo**

```bash
# Limpiar todo y reiniciar
poetry env remove python
rm -rf .venv
poetry install
poetry shell
```

## 📂 Estructura del Proyecto

```text
political-discourse-analyzer/
├── data/
│   ├── programs/     # Documentos políticos
│   └── db/          # Directorio para PostgreSQL
├── src/
│   └── political_discourse_analyzer/
│       ├── core/          # Núcleo de la aplicación
│       │   ├── main.py    # Servidor FastAPI
│       │   └── initialize.py # Inicialización del sistema
│       ├── models/        # Modelos de datos
│       ├── services/      # Servicios principales
│       │   ├── assistant_service.py  # Integración con OpenAI
│       │   └── database_service.py   # Gestión de BD
│       └── utils/         # Utilidades
│           ├── db_management.py      # Gestión de BD
│           └── document_checker.py   # Verificación de documentos
├── frontend/        # Aplicación React
└── tests/          # Tests del sistema
├── Dockerfile      # Configuración de contenedor
├── railway.toml    # Configuración de Railway
└── .dockerignore   # Exclusiones para Docker
```

## 🌐 API Endpoints

### Estado del Servicio

```bash
GET /
```

Retorna el estado actual del servicio.

### Consultas

```bash
POST /search
```

Realiza consultas sobre programas electorales.

Ejemplo de payload:

```json
{
  "query": "¿Qué propone el PSOE en materia de vivienda?",
  "mode": "neutral"
}
```

## ☁️ Despliegue en Railway

El proyecto está configurado para un despliegue en dos servicios separados:

### 1. Backend

- Despliegue automatizado desde GitHub
- Contenedorización con Docker
- Configuración mediante `railway.toml` y `Dockerfile`
- Healthcheck integrado
- Variables de entorno necesarias:
  - OPENAI_API_KEY
  - MODEL_NAME
  - ENVIRONMENT
  - PORT

### 2. Frontend

- Despliegue separado en `/frontend`
- Construcción y servido automático
- Variable de entorno para conexión con backend:
  - VITE_API_URL

### 3. Base de Datos

- PostgreSQL gestionado por Railway
- Configuración automática de conexión
- Variables proporcionadas por Railway:
  - DATABASE_URL

### 4. Verificación del Despliegue

- Monitorización via Railway Dashboard
- Logs disponibles para debugging
- Endpoints de health para verificación

## 🧪 Tests

```bash
# Ejecutar todos los tests
pytest

# Ejecutar tests específicos
pytest tests/test_api/
pytest tests/test_services/
pytest tests/test_utils/

# Ejecutar tests con coverage
pytest --cov=src
```

## 🔧 Comandos de Utilidad

```bash
# Verificar documentos
python -m political_discourse_analyzer.utils.document_checker

# Formatear código
black src/

# Lint
ruff check src/
```

## 🤝 Contribuir

1. Fork el repositorio
2. Crear rama para feature: `git checkout -b feature/NuevaCaracteristica`
3. Commit cambios: `git commit -m 'Añadir nueva característica'`
4. Push a la rama: `git push origin feature/NuevaCaracteristica`
5. Abrir Pull Request

## 📝 Licencia

[MIT](LICENSE)

## 👥 Autores

Angélica Laza - <angi.laza@hotmail.es>

## 🔗 Enlaces Útiles

- [Dashboard de Railway](https://railway.app/dashboard)
- [OpenAI Platform](https://platform.openai.com)
- [Documentación de FastAPI](https://fastapi.tiangolo.com)
- [React Documentation](https://reactjs.org)
- [Tailwind CSS](https://tailwindcss.com)
