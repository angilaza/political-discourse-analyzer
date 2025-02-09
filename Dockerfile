# Usar una imagen base de Python
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Copiar archivos de configuración de Poetry
COPY pyproject.toml poetry.lock ./

# Configurar Poetry para no crear un entorno virtual
RUN poetry config virtualenvs.create false

# Instalar dependencias
RUN poetry install --no-dev --no-interaction --no-ansi

# Copiar el código de la aplicación
COPY . .

# Instalar spacy model
RUN python -m spacy download es_core_news_md

# Exponer el puerto
EXPOSE $PORT

# Comando para ejecutar la aplicación
CMD uvicorn src.political_discourse_analyzer.core.main:app --host 0.0.0.0 --port $PORT