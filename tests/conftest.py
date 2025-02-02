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

#  Cargar variables de entorno para tests
load_dotenv()

# Configuración de base de datos de prueba
TEST_DB_NAME = "political_discourse_test"
TEST_DATABASE_URL = f"postgresql://postgres@localhost:5432/{TEST_DB_NAME}"

def create_test_database():
    """Crear base de datos de prueba si no existe."""
    try:
        # Intentar crear la base de datos
        subprocess.run(
            ["createdb", TEST_DB_NAME],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Base de datos {TEST_DB_NAME} creada.")
    except subprocess.CalledProcessError as e:
        if "already exists" not in e.stderr:
            print(f"Error creando base de datos: {e.stderr}")
            raise

def drop_test_database():
    """Eliminar base de datos de prueba."""
    try:
        subprocess.run(
            ["dropdb", TEST_DB_NAME],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Base de datos {TEST_DB_NAME} eliminada.")
    except subprocess.CalledProcessError as e:
        print(f"Error eliminando base de datos: {e.stderr}")

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Configurar y limpiar base de datos de prueba."""
    create_test_database()
    yield
    drop_test_database()

@pytest.fixture(scope="session")
def test_db_engine():
    """Crear motor de base de datos de prueba."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_settings():
    """Configuración de prueba."""
    return ApplicationSettings.from_env(openai_api_key=os.getenv("OPENAI_API_KEY"))

@pytest.fixture
def test_client(test_settings):
    """Cliente de prueba para la API."""
    app = create_app(init_services=False)  # No inicializar servicios en tests
    with TestClient(app) as client:
        yield client

@pytest.fixture
def test_db_service():
    """Servicio de base de datos para pruebas."""
    os.environ["DB_NAME"] = TEST_DB_NAME
    return DatabaseService()
