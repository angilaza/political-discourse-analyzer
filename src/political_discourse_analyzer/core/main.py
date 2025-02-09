# src/political_discourse_analyzer/core/main.py
import os
import uvicorn 
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import logging
import sys
from datetime import datetime, timedelta

# Importaciones locales
from political_discourse_analyzer.models.settings import ApplicationSettings
from political_discourse_analyzer.services.assistant_service import AssistantService
from political_discourse_analyzer.services.database_service import DatabaseService
from political_discourse_analyzer.services.analytics_service import AnalyticsService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

# Modelos de datos
class SearchQuery(BaseModel):
    query: str
    mode: str = "neutral"
    thread_id: Optional[str] = None

class SearchResponse(BaseModel):
    response: str
    thread_id: str
    citations: Optional[List[str]] = None

# Initialize FastAPI app
app = FastAPI(title="Political Discourse Analyzer API")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar variables de entorno
load_dotenv()

# Initialize services
try:
    settings = ApplicationSettings.from_env(openai_api_key=os.getenv("OPENAI_API_KEY"))
    assistant_service = AssistantService(settings)
    db_service = DatabaseService()
    analytics_service = AnalyticsService(db_service)
    
    # Initialize assistant service
    assistant_service.init_service()
    logger.info("Services initialized successfully")
except Exception as e:
    logger.error(f"Error initializing services: {str(e)}")
    raise

@app.get("/")
async def read_root():
    try:
        logger.info("Processing root endpoint request")
        return {
            "status": "active",
            "message": "Political Discourse Analyzer API",
            "version": "0.1.0"
        }
    except Exception as e:
        logger.error(f"Error in root endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=SearchResponse)
async def search_documents(query: SearchQuery):
    try:
        logger.info(f"Processing search request with thread_id: {query.thread_id}")
        
        # Procesar la consulta a través del asistente
        response = await assistant_service.process_query(
            query=query.query,
            thread_id=query.thread_id,
            mode=query.mode
        )
        
        # Si no hay thread_id (nueva conversación), crear una en la base de datos
        if not query.thread_id:
            await db_service.save_conversation(
                thread_id=response['thread_id'],
                mode=query.mode
            )
        
        # Guardar la interacción
        await db_service.save_interaction(
            thread_id=response['thread_id'],
            query=query.query,
            response=response['response'],
            mode=query.mode,
            citations=[c['quote'] for c in response.get('citations', [])]
        )
        
        return SearchResponse(**response)
        
    except Exception as e:
        logger.error(f"Error in search endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/diagnostic/db")
async def database_diagnostic():
    """Endpoint de diagnóstico para verificar la conexión a la base de datos."""
    try:
        # Intentar realizar operaciones básicas
        stats = await db_service.get_analytics()
        
        return {
            "status": "healthy",
            "database_connection": "ok",
            "statistics": stats,
            "environment": os.getenv("ENVIRONMENT", "development"),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Database diagnostic failed: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "environment": os.getenv("ENVIRONMENT", "development"),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/analytics/report")
async def get_analytics_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Genera un informe completo de análisis de las consultas.
    Fechas en formato ISO: YYYY-MM-DD
    """
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        report = await analytics_service.generate_comprehensive_report(start, end)
        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")
    except Exception as e:
        logger.error(f"Error generating analytics report: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/topics")
async def get_topic_analysis(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Análisis de distribución de temas en las consultas."""
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        return await analytics_service.get_topic_distribution(start, end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/engagement")
async def get_engagement_metrics():
    """Métricas de engagement de usuarios."""
    try:
        return await analytics_service.get_engagement_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)