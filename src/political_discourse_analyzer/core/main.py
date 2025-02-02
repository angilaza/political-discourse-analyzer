# src/political_discourse_analyzer/core/main.py
import os
import uvicorn 
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from political_discourse_analyzer.models.settings import ApplicationSettings
from political_discourse_analyzer.services.assistant_service import AssistantService
from political_discourse_analyzer.services.database_service import DatabaseService

def create_app(init_services: bool = True):
    """
    Crea y configura la aplicación FastAPI.
    
    Args:
        init_services (bool): Si se deben inicializar los servicios automáticamente
    """
    load_dotenv()
    
    app = FastAPI(title="Political Discourse Analyzer API")
    
    # Configuración de CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Modelos de datos
    class SearchQuery(BaseModel):
        query: str
        mode: str = "neutral"
        thread_id: Optional[str] = None

    class SearchResponse(BaseModel):
        response: str
        thread_id: str
        citations: Optional[List[str]] = None

    # Initialize services
    settings = ApplicationSettings.from_env(openai_api_key=os.getenv("OPENAI_API_KEY"))
    assistant_service = AssistantService(settings)
    db_service = DatabaseService()

    if init_services:
        assistant_service.init_service()

    @app.get("/")
    async def read_root():
        try:
            return {
                "status": "active",
                "message": "Political Discourse Analyzer API",
                "version": "0.1.0"
            }
        except Exception as e:
            print(f"Error en endpoint raíz: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    @app.post("/search", response_model=SearchResponse)
    async def search_documents(query: SearchQuery):
        try:
            response = await assistant_service.process_query(
                query=query.query,
                thread_id=query.thread_id,
                mode=query.mode
            )
            return SearchResponse(**response)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app

# Crear la aplicación principal
app = create_app()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)