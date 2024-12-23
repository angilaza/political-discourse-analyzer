# src/political_discourse_analyzer/services/database_service.py
import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import List, Dict, Optional

Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String, unique=True, index=True)
    mode = Column(String)
    created_at = Column(DateTime)
    last_interaction = Column(DateTime)
    total_interactions = Column(Integer, default=0)

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String, index=True)
    query = Column(Text)
    response = Column(Text)
    mode = Column(String)
    citations = Column(Text)
    timestamp = Column(DateTime)

class DatabaseService:
    def __init__(self):
        """Inicializa la conexión a PostgreSQL."""
        db_url = self._get_database_url()
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    def _get_database_url(self) -> str:
        """
        Obtiene la URL de conexión a la base de datos según el entorno.
        """
        if os.getenv("ENVIRONMENT") == "production":
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                raise ValueError("DATABASE_URL no está configurada en producción")
            # Railway usa postgres://, SQLAlchemy necesita postgresql://
            return db_url.replace("postgres://", "postgresql://", 1)
        
        # Configuración local
        return (
            f"postgresql://"
            f"{os.getenv('DB_USER', 'postgres')}:"
            f"{os.getenv('DB_PASSWORD', '')}@"
            f"{os.getenv('DB_HOST', 'localhost')}:"
            f"{os.getenv('DB_PORT', '5432')}/"
            f"{os.getenv('DB_NAME', 'political_discourse')}"
        )

    async def save_conversation(self, thread_id: str, mode: str) -> Conversation:
        """
        Guarda una nueva conversación.
        """
        with self.SessionLocal() as db:
            conversation = Conversation(
                thread_id=thread_id,
                mode=mode,
                created_at=datetime.now(),
                last_interaction=datetime.now(),
                total_interactions=0
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            return conversation

    async def save_interaction(self, 
                             thread_id: str, 
                             query: str, 
                             response: str, 
                             mode: str,
                             citations: List[str] = None):
        """
        Guarda una nueva interacción y actualiza la conversación.
        """
        with self.SessionLocal() as db:
            interaction = Interaction(
                thread_id=thread_id,
                query=query,
                response=response,
                mode=mode,
                citations=','.join(citations) if citations else '',
                timestamp=datetime.now()
            )
            db.add(interaction)
            
            conversation = db.query(Conversation).filter(
                Conversation.thread_id == thread_id
            ).first()
            
            if conversation:
                conversation.last_interaction = datetime.now()
                conversation.total_interactions += 1
            
            db.commit()

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
        Obtiene estadísticas de uso.
        """
        with self.SessionLocal() as db:
            total_conversations = db.query(Conversation).count()
            total_interactions = db.query(Interaction).count()
            
            modes_count = db.query(
                Conversation.mode, 
                func.count(Conversation.id)
            ).group_by(Conversation.mode).all()
            
            return {
                "total_conversations": total_conversations,
                "total_interactions": total_interactions,
                "modes_distribution": dict(modes_count)
            }