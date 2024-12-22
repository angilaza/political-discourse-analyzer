from pathlib import Path
import os
from dotenv import load_dotenv
import openai
from political_discourse_analyzer.models.settings import ApplicationSettings
from political_discourse_analyzer.services.assistant_service import AssistantService
from political_discourse_analyzer.services.sqlite_service import SQLiteService

class SystemDiagnostic:
    def __init__(self):
        load_dotenv()
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.settings = ApplicationSettings.from_env(openai_api_key=self.openai_key)
        self.client = openai.Client(api_key=self.openai_key)
        
    def run_diagnostics(self):
        """
        Ejecuta una serie de comprobaciones del sistema.
        """
        print("\n=== Diagnóstico del Sistema ===\n")
        
        # Comprobar directorios
        self._check_directories()
        
        # Comprobar base de datos
        self._check_database()
        
        # Comprobar Vector Store
        self._check_vector_store()
        
        # Comprobar Asistentes
        self._check_assistants()
        
        print("\n=== Fin del Diagnóstico ===")

    def _check_directories(self):
        print("Comprobando directorios...")
        paths = {
            "DB": Path("data/db"),
            "Programas": Path("data/programs")
        }
        
        for name, path in paths.items():
            status = "✓ Existe" if path.exists() else "✗ No existe"
            print(f"Directorio {name}: {status}")
            if path.exists() and name == "Programas":
                files = list(path.glob("*.pdf"))
                print(f"  - Documentos PDF encontrados: {len(files)}")
                for file in files:
                    print(f"    * {file.name}")

    def _check_database(self):
        print("\nComprobando base de datos SQLite...")
        db_path = Path("data/db/discourse.db")
        if db_path.exists():
            print("✓ Base de datos encontrada")
            size_mb = db_path.stat().st_size / (1024 * 1024)
            print(f"  - Tamaño: {size_mb:.2f} MB")
        else:
            print("✗ Base de datos no encontrada")

    def _check_vector_store(self):
        print("\nComprobando Vector Store en OpenAI...")
        try:
            vector_stores = self.client.beta.vector_stores.list()
            political_store = next(
                (vs for vs in vector_stores.data if vs.name == "Programas Políticos"),
                None
            )
            
            if political_store:
                print("✓ Vector Store 'Programas Políticos' encontrado")
                print(f"  - ID: {political_store.id}")
                print(f"  - Estado: {political_store.status}")
                
                # Listar archivos en el Vector Store
                files = self.client.beta.vector_stores.files.list(political_store.id)
                print(f"  - Archivos indexados: {len(files.data)}")
                for file in files.data:
                    # Obtener detalles del archivo original
                    try:
                        file_details = self.client.files.retrieve(file.id)
                        print(f"    * {file_details.filename} (ID: {file.id})")
                    except Exception:
                        print(f"    * ID del archivo: {file.id}")
            else:
                print("✗ Vector Store 'Programas Políticos' no encontrado")
        except Exception as e:
            print(f"✗ Error al comprobar Vector Store: {str(e)}")

    def _check_assistants(self):
        print("\nComprobando Asistentes...")
        try:
            assistants = self.client.beta.assistants.list()
            expected_names = [
                "Asistente de Programas Electorales",
                "Asistente de Perspectiva Personal"
            ]
            
            found_assistants = {
                asst.name: asst 
                for asst in assistants.data 
                if asst.name in expected_names
            }
            
            for name in expected_names:
                if name in found_assistants:
                    asst = found_assistants[name]
                    print(f"✓ {name}")
                    print(f"  - ID: {asst.id}")
                    print(f"  - Modelo: {asst.model}")
                    print(f"  - Herramientas: {[tool['type'] if isinstance(tool, dict) else tool.type for tool in asst.tools]}")
                else:
                    print(f"✗ {name} no encontrado")
        
        except Exception as e:
            print(f"✗ Error al comprobar asistentes: {str(e)}")

if __name__ == "__main__":
    diagnostic = SystemDiagnostic()
    diagnostic.run_diagnostics()