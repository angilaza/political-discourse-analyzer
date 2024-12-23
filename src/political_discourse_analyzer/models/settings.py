from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path

class AISettings(BaseModel):
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    model: str = Field(default="gpt-4-turbo-preview", description="Modelo a utilizar")

class DatabaseSettings(BaseModel):
    path: Path = Field(
        default=Path("data/db/discourse.db"),
        description="Ruta de la base de datos SQLite"
    )

class ApplicationSettings(BaseModel):
    ai_settings: AISettings = Field(default_factory=AISettings)
    db_settings: DatabaseSettings = Field(default_factory=DatabaseSettings)
    documents_path: Path = Field(
        default=Path("data/programs"),
        description="Ruta de los documentos políticos"
    )

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_env(cls, openai_api_key: str):
        """
        Crea una instancia de ApplicationSettings desde variables de entorno
        """
        return cls(
            ai_settings=AISettings(
                openai_api_key=openai_api_key,
                model="gpt-4-turbo-preview"
            ),
            db_settings=DatabaseSettings(),
            documents_path=Path("data/programs")
        )