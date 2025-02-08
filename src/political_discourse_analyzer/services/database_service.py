# src/political_discourse_analyzer/services/database_service.py
import os
import logging
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String, unique=True, index=True)
    mode = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_interaction = Column(DateTime, default=datetime.utcnow)
    total_interactions = Column(Integer, default=0)

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String, index=True)
    query = Column(Text)
    response = Column(Text)
    mode = Column(String)
    citations = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

class DatabaseService:
    def __init__(self):
        """Inicializa la conexión a PostgreSQL."""
        try:
            db_url = self._get_database_url()
            self.engine = create_engine(db_url, pool_size=5, max_overflow=10)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database connection established successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise

    def _get_database_url(self) -> str:
        """Obtiene la URL de conexión a la base de datos según el entorno."""
        try:
            if os.getenv("ENVIRONMENT") == "production":
                db_url = os.getenv("DATABASE_URL")
                if not db_url:
                    raise ValueError("DATABASE_URL no está configurada en producción")
                return db_url.replace("postgres://", "postgresql://", 1)
            
            # Local development connection
            db_params = {
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', ''),
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': os.getenv('DB_PORT', '5432'),
                'database': os.getenv('DB_NAME', 'political_discourse')
            }
            
            url = f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['database']}"
            logger.info(f"Database URL configured for environment: {os.getenv('ENVIRONMENT', 'development')}")
            return url
            
        except Exception as e:
            logger.error(f"Error building database URL: {str(e)}")
            raise

    async def save_conversation(self, thread_id: str, mode: str) -> Conversation:
        """Guarda una nueva conversación."""
        try:
            with self.SessionLocal() as db:
                conversation = Conversation(
                    thread_id=thread_id,
                    mode=mode,
                    created_at=datetime.utcnow(),
                    last_interaction=datetime.utcnow(),
                    total_interactions=0
                )
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
                logger.info(f"New conversation saved with thread_id: {thread_id}")
                return conversation
        except SQLAlchemyError as e:
            logger.error(f"Database error saving conversation: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error saving conversation: {str(e)}")
            raise

    async def save_interaction(self, 
                         thread_id: str, 
                         query: str, 
                         response: str, 
                         mode: str,
                         citations: List[str] = None):
        """Guarda una nueva interacción y actualiza la conversación."""
        logger.info(f"Attempting to save interaction for thread_id: {thread_id}")
        logger.info(f"Database URL: {self._get_database_url()}")
        
        try:
            with self.SessionLocal() as db:
                # Crear nueva interacción
                interaction = Interaction(
                    thread_id=thread_id,
                    query=query,
                    response=response,
                    mode=mode,
                    citations=','.join(citations) if citations else '',
                    timestamp=datetime.utcnow()
                )
                logger.info(f"Created interaction object: {interaction.thread_id}")
                
                db.add(interaction)
                logger.info("Added interaction to session")
                
                # Actualizar conversación existente
                conversation = db.query(Conversation).filter(
                    Conversation.thread_id == thread_id
                ).first()
                
                if conversation:
                    logger.info(f"Found existing conversation: {conversation.thread_id}")
                    conversation.last_interaction = datetime.utcnow()
                    conversation.total_interactions += 1
                else:
                    logger.info("No existing conversation found, creating new one")
                    conversation = Conversation(
                        thread_id=thread_id,
                        mode=mode,
                        created_at=datetime.utcnow(),
                        last_interaction=datetime.utcnow(),
                        total_interactions=1
                    )
                    db.add(conversation)
                
                logger.info("Committing changes to database")
                db.commit()
                logger.info("Successfully committed changes")
                
        except Exception as e:
            logger.error(f"Error saving interaction: {str(e)}", exc_info=True)
            raise
        
    async def get_conversation_history(self, thread_id: str) -> List[Dict]:
            """
            Recupera el historial de una conversación.
            """
            with self.SessionLocal() as db:
                interactions = db.query(Interaction).filter(
                    Interaction.thread_id == thread_id
                ).order_by(Interaction.timestamp).all()
                
                return [
                    {
                        "query": interaction.query,
                        "response": interaction.response,
                        "mode": interaction.mode,
                        "citations": interaction.citations.split(',') if interaction.citations else [],
                        "timestamp": interaction.timestamp
                    }
                    for interaction in interactions
                ]
                
    async def get_analytics(self) -> Dict:
        """
        Obtiene estadísticas de uso de la plataforma.
        """
        try:
            with self.SessionLocal() as db:
                # Contar total de conversaciones
                total_conversations = db.query(Conversation).count()
                logger.info(f"Total conversations: {total_conversations}")

                # Contar total de interacciones
                total_interactions = db.query(Interaction).count()
                logger.info(f"Total interactions: {total_interactions}")
                
                # Distribución por modo
                modes_count = db.query(
                    Conversation.mode, 
                    func.count(Conversation.id).label('count')
                ).group_by(Conversation.mode).all()
                
                modes_distribution = {mode: count for mode, count in modes_count}
                logger.info(f"Modes distribution: {modes_distribution}")
                
                # Obtener algunas estadísticas adicionales
                latest_conversation = db.query(Conversation).order_by(
                    Conversation.created_at.desc()
                ).first()

                latest_interaction = db.query(Interaction).order_by(
                    Interaction.timestamp.desc()
                ).first()

                return {
                    "total_conversations": total_conversations,
                    "total_interactions": total_interactions,
                    "modes_distribution": modes_distribution,
                    "latest_conversation_time": latest_conversation.created_at.isoformat() if latest_conversation else None,
                    "latest_interaction_time": latest_interaction.timestamp.isoformat() if latest_interaction else None,
                    "database_status": "connected"
                }
                
        except Exception as e:
            logger.error(f"Error getting analytics: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "database_status": "error"
            }