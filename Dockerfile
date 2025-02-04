FROM python:3.11-slim

# Instalar curl y otras dependencias necesarias
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Instalar poetry y añadirlo al PATH
ENV POETRY_HOME=/opt/poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos de configuración de poetry
COPY pyproject.toml poetry.lock ./

# Deshabilitar la creación de entornos virtuales e instalar dependencias
RUN /opt/poetry/bin/poetry config virtualenvs.create false && \
    /opt/poetry/bin/poetry install --no-interaction --no-ansi

# Copiar el código de la aplicación
COPY . .

# Comando para ejecutar la aplicación
CMD ["/opt/poetry/bin/poetry", "run", "uvicorn", "src.political_discourse_analyzer.core.main:app", "--host", "0.0.0.0", "--port", "$PORT"]