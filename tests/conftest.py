import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from political_discourse_analyzer.services.database_service import Base
from political_discourse_analyzer.core.main import create_app
from political_discourse_analyzer.models.settings import ApplicationSettings
from political_discourse_analyzer.services.assistant_service import AssistantService
from political_discourse_analyzer.services.database_service import DatabaseService

# Cargar variables de entorno para tests
load_dotenv()

# Configuración de base de datos de prueba
TEST_DB_NAME = "political_discourse_test"
TEST_DATABASE_URL = f"postgresql://postgres@localhost:5432/{TEST_DB_NAME}"

@pytest.fixture(scope="session")
def test_db_engine():
    """Crear base de datos de prueba."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_settings():
    """Configuración de prueba."""
    return ApplicationSettings.from_env(openai_api_key=os.getenv("OPENAI_API_KEY"))

@pytest.fixture
def test_assistant_service(test_settings):
    """Servicio de asistente para pruebas."""
    return AssistantService(test_settings)

@pytest.fixture
def test_db_service():
    """Servicio de base de datos para pruebas."""
    os.environ["DB_NAME"] = TEST_DB_NAME
    return DatabaseService()

@pytest.fixture
def test_client(test_settings, test_db_service, test_assistant_service):
    """Cliente de prueba para la API."""
    app = create_app()
    with TestClient(app) as client:
        yield client