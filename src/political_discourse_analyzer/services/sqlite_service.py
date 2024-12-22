import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class Conversation:
    thread_id: str
    mode: str
    created_at: datetime
    last_interaction: datetime
    total_interactions: int

@dataclass
class Interaction:
    thread_id: str
    query: str
    response: str
    mode: str
    citations: List[str]
    timestamp: datetime

class SQLiteService:
    def __init__(self, db_path: str = "interactions.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """
        Inicializa la base de datos con las tablas necesarias.
        """
        with sqlite3.connect(self.db_path) as conn:
            # Tabla para mantener registro de conversaciones (threads)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    thread_id TEXT PRIMARY KEY,
                    mode TEXT NOT NULL,
                    created_at DATETIME NOT NULL,
                    last_interaction DATETIME NOT NULL,
                    total_interactions INTEGER DEFAULT 0
                )
            """)

            # Tabla para almacenar cada interacción individual
            conn.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id TEXT NOT NULL,
                    query TEXT NOT NULL,
                    response TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    citations TEXT,
                    timestamp DATETIME NOT NULL,
                    FOREIGN KEY (thread_id) REFERENCES conversations (thread_id)
                )
            """)

    async def create_conversation(self, thread_id: str, mode: str) -> Conversation:
        """
        Registra una nueva conversación cuando se crea un thread.
        """
        current_time = datetime.now()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO conversations 
                (thread_id, mode, created_at, last_interaction, total_interactions)
                VALUES (?, ?, ?, ?, 0)
                """,
                (thread_id, mode, current_time, current_time)
            )
        
        return Conversation(
            thread_id=thread_id,
            mode=mode,
            created_at=current_time,
            last_interaction=current_time,
            total_interactions=0
        )

    async def save_interaction(self, interaction: Interaction):
        """
        Guarda una nueva interacción y actualiza la conversación.
        """
        with sqlite3.connect(self.db_path) as conn:
            # Guardar la interacción
            conn.execute(
                """
                INSERT INTO interactions 
                (thread_id, query, response, mode, citations, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    interaction.thread_id,
                    interaction.query,
                    interaction.response,
                    interaction.mode,
                    ','.join(interaction.citations) if interaction.citations else '',
                    interaction.timestamp
                )
            )
            
            # Actualizar la conversación
            conn.execute(
                """
                UPDATE conversations 
                SET last_interaction = ?,
                    total_interactions = total_interactions + 1
                WHERE thread_id = ?
                """,
                (interaction.timestamp, interaction.thread_id)
            )

    async def get_conversation(self, thread_id: str) -> Optional[Conversation]:
        """
        Recupera una conversación por su thread_id.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM conversations WHERE thread_id = ?",
                (thread_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return Conversation(
                    thread_id=row['thread_id'],
                    mode=row['mode'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    last_interaction=datetime.fromisoformat(row['last_interaction']),
                    total_interactions=row['total_interactions']
                )
            return None

    async def get_conversation_history(self, thread_id: str) -> List[Interaction]:
        """
        Recupera todas las interacciones de una conversación.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM interactions WHERE thread_id = ? ORDER BY timestamp",
                (thread_id,)
            )
            
            return [
                Interaction(
                    thread_id=row['thread_id'],
                    query=row['query'],
                    response=row['response'],
                    mode=row['mode'],
                    citations=row['citations'].split(',') if row['citations'] else [],
                    timestamp=datetime.fromisoformat(row['timestamp'])
                )
                for row in cursor.fetchall()
            ]

    async def get_analytics(self) -> Dict:
        """
        Obtiene estadísticas básicas de uso.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(DISTINCT thread_id) as total_conversations,
                    COUNT(*) as total_interactions,
                    AVG(total_interactions) as avg_interactions_per_conversation,
                    MODE as most_common_mode
                FROM conversations
                GROUP BY mode
                ORDER BY COUNT(*) DESC
                LIMIT 1
            """)
            
            stats = cursor.fetchone()
            
            return {
                "total_conversations": stats[0],
                "total_interactions": stats[1],
                "avg_interactions_per_conversation": stats[2],
                "most_common_mode": stats[3]
            }