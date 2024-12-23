import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from political_discourse_analyzer.services.database_service import Base
from political_discourse_analyzer.core.main import create_app

# Base de datos de prueba
TEST_DATABASE_URL = "postgresql://postgres@localhost:5432/political_discourse_test"

@pytest.fixture(scope="session")
def test_db_engine():
    """Crear base de datos de prueba."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_db(test_db_engine):
    """Proporcionar sesión de base de datos para pruebas."""
    TestingSessionLocal = sessionmaker(bind=test_db_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

@pytest.fixture
def test_client():
    """Crear cliente de prueba."""
    app = create_app()
    with TestClient(app) as client:
        yield client