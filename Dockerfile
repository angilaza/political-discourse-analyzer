FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && \
    apt-get install -y \
    curl \
    gcc \
    python3-dev \
    libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Instalar poetry
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VIRTUALENVS_CREATE=false
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar el proyecto
COPY . .

# Instalar dependencias
RUN poetry install --without dev

# Comando para ejecutar la aplicación
CMD ["poetry", "run", "uvicorn", "src.political_discourse_analyzer.core.main:app", "--host", "0.0.0.0", "--port", "$PORT"]