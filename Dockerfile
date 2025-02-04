FROM python:3.11-slim

# Instalar curl y otras dependencias necesarias
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Instalar poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos de configuración de poetry
COPY pyproject.toml poetry.lock ./

# Instalar dependencias
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

# Copiar el código de la aplicación
COPY . .

# Comando para ejecutar la aplicación
CMD poetry run uvicorn src.political_discourse_analyzer.core.main:app --host 0.0.0.0 --port $PORT