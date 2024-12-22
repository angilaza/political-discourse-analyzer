import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from political_discourse_analyzer.models.settings import ApplicationSettings
from political_discourse_analyzer.services.assistant_service import AssistantService
from political_discourse_analyzer.services.sqlite_service import SQLiteService

# Cargar variables de entorno
load_dotenv()

# Crear la aplicación FastAPI
app = FastAPI(title="Political Discourse Analyzer API")

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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

# Inicialización de servicios
settings = ApplicationSettings.from_env(openai_api_key=os.getenv("OPENAI_API_KEY"))
assistant_service = AssistantService(settings)
db_service = SQLiteService(str(settings.db_settings.path))

# Inicializar el servicio de asistente al arrancar
assistant_service.init_service()

@app.get("/")
async def read_root():
    return {
        "status": "active",
        "message": "Political Discourse Analyzer API",
        "available_modes": list(assistant_service.assistants.keys())
    }

@app.post("/search", response_model=SearchResponse)
async def search_documents(query: SearchQuery):
    try:
        print(f"Recibida consulta: {query.query}")
        print(f"Modo: {query.mode}")
        print(f"Asistentes disponibles: {assistant_service.assistants}")
        
        response = await assistant_service.process_query(
            query=query.query,
            thread_id=query.thread_id,
            mode=query.mode
        )
        
        return SearchResponse(**response)
    
    except ValueError as e:
        print(f"Error de validación: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error interno: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando la consulta: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)