import os
from dotenv import load_dotenv
from pathlib import Path
from political_discourse_analyzer.models.settings import ApplicationSettings
from political_discourse_analyzer.services.assistant_service import AssistantService
from src.political_discourse_analyzer.services.database_service import DatabaseService

def initialize_app():
    """
    Inicializa la aplicación, configurando la base de datos y los servicios.
    """
    # Cargar variables de entorno
    load_dotenv()
    
    # Verificar API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("La API key de OpenAI no está configurada en el archivo .env")

    # Crear directorios necesarios
    for dir_path in ["data/db", "data/programs"]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    # Configurar settings usando el método from_env
    print("Configurando ajustes de la aplicación...")
    settings = ApplicationSettings.from_env(openai_api_key=openai_api_key)

    # Inicializar servicios
    print("Inicializando servicios...")
    db_service = DatabaseService() 
    assistant_service = AssistantService(settings)
    
    # Inicializar el servicio de asistente
    print("Iniciando servicio de asistente...")
    assistant_service.init_service()
    print("Servicio de asistente inicializado correctamente")

    return settings, db_service, assistant_service

if __name__ == "__main__":
    # Ejecutar la inicialización
    print("Iniciando la aplicación...")
    initialize_app()
    print("Aplicación inicializada correctamente")