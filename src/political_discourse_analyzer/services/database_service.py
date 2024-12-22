# src/political_discourse_analyzer/services/database_service.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Dict, Optional

load_dotenv()

class DatabaseConfig:
    """Configuración de la base de datos según el entorno"""
    @staticmethod
    def get_database_url():
        environment = os.getenv("ENVIRONMENT", "development")
        
        if environment == "production":
            # En producción, usar PostgreSQL de Railway
            db_url = os.getenv("DATABASE_URL")
            if db_url:
                # Railway usa postgres://, SQLAlchemy necesita postgresql://
                return db_url.replace("postgres://", "postgresql://")
            raise ValueError("DATABASE_URL no está configurada en producción")
        else:
            # En desarrollo, usar SQLite
            return "sqlite:///./data/db/discourse.db"

# Crear el motor de base de datos
engine = create_engine(DatabaseConfig.get_database_url())

# Crear sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarativa para modelos
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
    def __init__(self, db_path: Optional[str] = None):
        self.db_url = self._get_database_url(db_path)
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    def _get_database_url(self, db_path: Optional[str] = None) -> str:
        """
        Determina la URL de la base de datos según el entorno
        """
        environment = os.getenv("ENVIRONMENT", "development")
        
        if environment == "production":
            # En producción, usar PostgreSQL de Railway
            db_url = os.getenv("DATABASE_URL")
            if db_url:
                return db_url.replace("postgres://", "postgresql://")
            raise ValueError("DATABASE_URL no está configurada en producción")
        else:
            # En desarrollo, usar SQLite
            if db_path:
                return f"sqlite:///{db_path}"
            return "sqlite:///./data/db/discourse.db"

    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    async def save_conversation(self, thread_id: str, mode: str) -> Conversation:
        """
        Guarda una nueva conversación.
        """
        db = next(self.get_db())
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
        db = next(self.get_db())
        
        # Guardar la interacción
        interaction = Interaction(
            thread_id=thread_id,
            query=query,
            response=response,
            mode=mode,
            citations=','.join(citations) if citations else '',
            timestamp=datetime.now()
        )
        db.add(interaction)
        
        # Actualizar la conversación
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
        db = next(self.get_db())
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
        db = next(self.get_db())
        
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