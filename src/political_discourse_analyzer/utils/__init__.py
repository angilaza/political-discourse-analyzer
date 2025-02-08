# src/political_discourse_analyzer/utils/init_db.py
from political_discourse_analyzer.services.database_service import Base, DatabaseService

def init_database():
    db_service = DatabaseService()
    Base.metadata.drop_all(bind=db_service.engine)  # Borra tablas existentes
    Base.metadata.create_all(bind=db_service.engine)  # Crea tablas nuevas
    print("Database tables initialized successfully")

if __name__ == "__main__":
    init_database()