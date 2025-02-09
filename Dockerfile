# Usar una imagen base de Python
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Establecer variables de entorno
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VERSION=1.7.1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="/opt/poetry/bin:$PATH"

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

# Copiar archivos de configuración de Poetry
COPY pyproject.toml poetry.lock ./

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