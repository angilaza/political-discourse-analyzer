# src/political_discourse_analyzer/utils/db_management.py
import os
import sys
import subprocess
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

def load_config():
    """Carga la configuración de la base de datos desde variables de entorno."""
    load_dotenv()
    return {
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'political_discourse')
    }

def check_postgresql():
    """Verifica si PostgreSQL está instalado y en ejecución."""
    try:
        # Verificar si PostgreSQL está instalado
        result = subprocess.run(['which', 'postgres'], capture_output=True, text=True)
        if result.returncode != 0:
            print("PostgreSQL no está instalado. Instalando...")
            subprocess.run(['brew', 'install', 'postgresql@14'])
            print("PostgreSQL instalado correctamente.")
        
        # Verificar si el servicio está en ejecución
        result = subprocess.run(['brew', 'services', 'list'], capture_output=True, text=True)
        if 'postgresql@14' not in result.stdout:
            print("Iniciando servicio PostgreSQL...")
            subprocess.run(['brew', 'services', 'start', 'postgresql@14'])
            print("Servicio PostgreSQL iniciado.")
        
        return True
    except Exception as e:
        print(f"Error al verificar PostgreSQL: {str(e)}")
        return False

def create_database():
    """Crea la base de datos si no existe."""
    config = load_config()
    
    try:
        # Conectar a postgres para crear la base de datos
        conn = psycopg2.connect(
            user=config['user'],
            password=config['password'],
            host=config['host'],
            port=config['port'],
            database='postgres'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Verificar si la base de datos existe
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{config['database']}'")
        exists = cursor.fetchone()
        
        if not exists:
            print(f"Creando base de datos {config['database']}...")
            cursor.execute(f"CREATE DATABASE {config['database']}")
            print("Base de datos creada correctamente.")
        else:
            print(f"La base de datos {config['database']} ya existe.")
            
    except Exception as e:
        print(f"Error al crear la base de datos: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

def reset_database():
    """Elimina y recrea la base de datos."""
    config = load_config()
    
    try:
        # Conectar a postgres para poder eliminar la base de datos
        conn = psycopg2.connect(
            user=config['user'],
            password=config['password'],
            host=config['host'],
            port=config['port'],
            database='postgres'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Cerrar conexiones existentes
        cursor.execute(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{config['database']}'
            AND pid <> pg_backend_pid();
        """)
        
        # Eliminar y recrear la base de datos
        print(f"Eliminando base de datos {config['database']}...")
        cursor.execute(f"DROP DATABASE IF EXISTS {config['database']}")
        print(f"Creando nueva base de datos {config['database']}...")
        cursor.execute(f"CREATE DATABASE {config['database']}")
        print("Base de datos reiniciada correctamente.")
        
    except Exception as e:
        print(f"Error al reiniciar la base de datos: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

def show_tables():
    """Muestra las tablas en la base de datos."""
    config = load_config()
    
    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        tables = cursor.fetchall()
        if tables:
            print("\nTablas en la base de datos:")
            for table in tables:
                print(f"- {table[0]}")
        else:
            print("No hay tablas en la base de datos.")
            
    except Exception as e:
        print(f"Error al mostrar tablas: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Función principal para gestionar la base de datos."""
    if len(sys.argv) < 2:
        print("""
Uso: python -m political_discourse_analyzer.utils.db_management <comando>
Comandos disponibles:
  check    - Verifica la instalación y estado de PostgreSQL
  create   - Crea la base de datos si no existe
  reset    - Elimina y recrea la base de datos
  tables   - Muestra las tablas existentes
  setup    - Ejecuta la verificación completa (check, create, tables)
        """)
        return

    command = sys.argv[1]
    
    if command == 'check':
        check_postgresql()
    elif command == 'create':
        create_database()
    elif command == 'reset':
        reset_database()
    elif command == 'tables':
        show_tables()
    elif command == 'setup':
        if check_postgresql():
            create_database()
            show_tables()
    else:
        print(f"Comando desconocido: {command}")

if __name__ == "__main__":
    main()