# src/political_discourse_analyzer/core/initialize.py
import os
from dotenv import load_dotenv
from political_discourse_analyzer.models.settings import ApplicationSettings
from political_discourse_analyzer.services.assistant_service import AssistantService
from political_discourse_analyzer.services.database_service import DatabaseService

def initialize_app():
    """
    Inicializa los servicios y la base de datos de la aplicación.
    """
    load_dotenv()
    
    print("Configurando aplicación...")
    settings = ApplicationSettings.from_env(openai_api_key=os.getenv("OPENAI_API_KEY"))
    
    print("Inicializando servicios...")
    db_service = DatabaseService()
    assistant_service = AssistantService(settings)
    
    print("Inicializando asistente...")
    assistant_service.init_service()
    
    return settings, db_service, assistant_service

if __name__ == "__main__":
    initialize_app()
    print("Aplicación inicializada correctamente")