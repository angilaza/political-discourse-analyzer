import uvicorn
from political_discourse_analyzer.core.main import create_app

def run_server():
    """
    Inicia el servidor FastAPI
    """
    uvicorn.run(
        "political_discourse_analyzer.core.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    run_server()