import pytest
from fastapi.testclient import TestClient

def test_read_root(test_client: TestClient):
    """Probar el endpoint raíz."""
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "active"
    assert "version" in response.json()

def test_search_neutral_mode(test_client: TestClient):
    """Probar búsqueda en modo neutral."""
    request_data = {
        "query": "¿Qué propone el PSOE en materia de vivienda?",
        "mode": "neutral"
    }
    response = test_client.post("/search", json=request_data)
    assert response.status_code == 200
    assert "response" in response.json()
    assert "thread_id" in response.json()
    
def test_search_personal_mode(test_client: TestClient):
    """Probar búsqueda en modo personal."""
    request_data = {
        "query": "¿Qué propone el PSOE en materia de vivienda?",
        "mode": "personal"
    }
    response = test_client.post("/search", json=request_data)
    assert response.status_code == 200
    assert "response" in response.json()
    assert "thread_id" in response.json()

def test_search_invalid_mode(test_client: TestClient):
    """Probar búsqueda con modo inválido."""
    request_data = {
        "query": "¿Qué propone el PSOE?",
        "mode": "invalid_mode"
    }
    response = test_client.post("/search", json=request_data)
    assert response.status_code == 400