from fastapi.testclient import TestClient

def test_read_root(test_client: TestClient):
    """Probar el endpoint raíz."""
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "active"

def test_search_endpoint(test_client: TestClient):
    """Probar el endpoint de búsqueda."""
    request_data = {
        "query": "¿Qué propone el PSOE en materia de vivienda?",
        "mode": "neutral"
    }
    response = test_client.post("/search", json=request_data)
    assert response.status_code == 200
    assert "response" in response.json()
    assert "thread_id" in response.json()