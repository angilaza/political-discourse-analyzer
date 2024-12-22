import time
from typing import Optional, Dict, List
import openai
from pathlib import Path
from political_discourse_analyzer.models.settings import ApplicationSettings

class AssistantService:
    def __init__(self, settings: ApplicationSettings):
        self.settings = settings
        self.client = openai.Client(api_key=settings.ai_settings.openai_api_key)
        self.assistants: Dict[str, str] = {}
        self.vector_store = None

    def _create_or_get_vector_store(self):
        """
        Crea o recupera el Vector Store para los documentos políticos.
        """
        # Listar Vector Stores existentes
        vector_stores = self.client.beta.vector_stores.list()
        
        # Buscar un Vector Store existente llamado "Programas Políticos"
        for vs in vector_stores.data:
            if vs.name == "Programas Políticos":
                return vs
        
        # Si no existe, crear nuevo Vector Store
        return self.client.beta.vector_stores.create(
            name="Programas Políticos",
            expires_after={
                "anchor": "last_active_at",
                "days": 30
            }
        )

    def _load_documents(self):
        """
        Carga los documentos políticos en el Vector Store.
        """
        docs_dir = Path("data/programs")
        
        # Obtener archivos ya procesados
        files = self.client.beta.vector_stores.files.list(self.vector_store.id)
        processed_files = {
            file.id: True
            for file in files.data
        }
        
        # Procesar nuevos archivos
        new_files = []
        for file_path in docs_dir.glob("*.pdf"):
            # Subir archivo a OpenAI
            file = self.client.files.create(
                file=open(file_path, "rb"),
                purpose="assistants"
            )
            
            if file.id not in processed_files:
                new_files.append(file.id)

        if new_files:
            # Crear batch de archivos en el Vector Store
            self.client.beta.vector_stores.file_batches.create(
                vector_store_id=self.vector_store.id,
                file_ids=new_files
            )
            print(f"Añadidos {len(new_files)} nuevos archivos al Vector Store")

    def init_service(self):
        """
        Inicializa el servicio creando el Vector Store y los asistentes.
        """
        print("Iniciando servicio...")
        # Crear Vector Store
        self.vector_store = self._create_or_get_vector_store()
        print(f"Vector Store creado/recuperado: {self.vector_store.id}")
        
        # Cargar documentos al Vector Store
        self._load_documents()
        print("Documentos cargados")
        
        # Inicializar asistentes
        self.init_assistants()
        print(f"Asistentes inicializados: {self.assistants}")

    def init_assistants(self):
        """
        Inicializa o recupera los asistentes.
        """
        print("Inicializando asistentes...")
        
        # Configuración de los asistentes
        assistant_configs = {
            "neutral": {
                "name": "Asistente de Programas Electorales",
                "instructions": """Eres un asistente especializado en analizar y explicar programas electorales.
                Al responder a preguntas sobre propuestas políticas, sigue estas pautas:

                1. FORMATO DE RESPUESTA:
                   - Comienza con una breve introducción de una línea
                   - Enumera cada propuesta en un párrafo separado
                   - Usa viñetas o números para las diferentes propuestas
                   - Limita la respuesta a 4-5 propuestas principales
                   - Deja espacio entre párrafos para mejor legibilidad

                2. CONTENIDO PRINCIPAL:
                   - Presenta las propuestas de forma clara y concisa
                   - Evita jerga técnica innecesaria
                   - Estructura la información de forma lógica
                   - Mantén un tono neutral y objetivo
                   - Limita cada propuesta a 2-3 líneas

                3. SECCIÓN DE REFERENCIAS:
                   Añade siempre al final una sección de "Fuentes:" con este formato:

                   Fuentes:
                   - Programa Electoral [Partido] 2023, página X: [Título de la sección]
                     Enlace: https://[url_del_documento]#page=X

                   - Repite para cada fuente utilizada
                   - Ordena las referencias por orden de aparición
                   - Incluye el número de página específico para cada cita
                   - Si una propuesta aparece en múltiples páginas, cita todas

                4. LONGITUD Y ESTILO:
                   - Mantén el cuerpo principal conciso y directo
                   - La sección de referencias debe ir separada por una línea en blanco
                   - Usa formato consistente para todas las referencias
                """
            },
            "personal": {
                "name": "Asistente de Perspectiva Personal",
                "instructions": """Eres un asistente que analiza y explica las posiciones políticas desde una 
                perspectiva más personal y contextualizada. Al responder:

                1. FORMATO DE RESPUESTA:
                   - Comienza con un contexto breve y accesible
                   - Presenta las ideas principales de forma conversacional
                   - Usa ejemplos prácticos cuando sea posible
                   - Mantén párrafos cortos y bien espaciados

                2. EXPLICACIONES:
                   - Relaciona las propuestas con situaciones cotidianas
                   - Explica las implicaciones prácticas
                   - Usa analogías cuando sea apropiado
                   - Mantén un tono cercano pero profesional

                3. SECCIÓN DE REFERENCIAS:
                   Al final de cada respuesta, incluye:

                   Fuentes consultadas:
                   - Programa Electoral [Partido] 2023, páginas X-Y
                     Puedes consultar los detalles en: [URL del documento]

                   - Mantén las referencias en un tono más conversacional
                   - Incluye siempre los números de página
                   - Proporciona contexto sobre dónde encontrar más información

                4. ESTRUCTURA GENERAL:
                   - Contenido principal: explicación clara y accesible
                   - Línea en blanco
                   - Sección de referencias: formato consistente y fácil de seguir
                """
            }
        }

        # Obtener lista de asistentes existentes
        existing_assistants = {
            asst.name: asst.id 
            for asst in self.client.beta.assistants.list().data
        }
        print(f"Asistentes existentes: {existing_assistants}")

        # Crear o actualizar cada asistente
        for mode, config in assistant_configs.items():
            if config["name"] in existing_assistants:
                assistant_id = existing_assistants[config["name"]]
                print(f"Actualizando asistente para modo {mode}: {assistant_id}")
                
                # Configurar el asistente con el Vector Store
                assistant = self.client.beta.assistants.update(
                    assistant_id=assistant_id,
                    name=config["name"],
                    instructions=config["instructions"],
                    model="gpt-4",
                    tools=[{"type": "file_search"}],
                    tool_resources={"file_search": {"vector_store_ids": [self.vector_store.id]}},
                    metadata={"mode": mode}
                )
            else:
                print(f"Creando nuevo asistente para modo {mode}")
                assistant = self.client.beta.assistants.create(
                    name=config["name"],
                    instructions=config["instructions"],
                    model="gpt-4",
                    tools=[{"type": "file_search"}],
                    tool_resources={"file_search": {"vector_store_ids": [self.vector_store.id]}},
                    metadata={"mode": mode}
                )
                assistant_id = assistant.id
                print(f"Nuevo asistente creado: {assistant_id}")

            self.assistants[mode] = assistant_id
            print(f"Asistente {mode} configurado con ID: {assistant_id}")

    async def process_query(self, query: str, mode: str = "neutral", thread_id: Optional[str] = None) -> dict:
        """
        Procesa una consulta usando el asistente apropiado.
        """
        print(f"Procesando consulta en modo {mode}")
        print(f"Asistentes disponibles: {self.assistants}")
        
        if mode not in self.assistants:
            raise ValueError(f"Asistente no configurado para el modo: {mode}")

        assistant_id = self.assistants[mode]
        print(f"Usando asistente: {assistant_id}")

        # Crear thread o usar existente
        try:
            if thread_id:
                thread = self.client.beta.threads.retrieve(thread_id)
                print(f"Usando thread existente: {thread_id}")
            else:
                thread = self.client.beta.threads.create()
                print(f"Nuevo thread creado: {thread.id}")

            # Añadir mensaje del usuario
            message = self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=query
            )
            print(f"Mensaje añadido al thread: {message.id}")

            # Ejecutar el asistente
            print("Iniciando ejecución del asistente...")
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant_id
            )
            print(f"Run creado: {run.id}")

            # Esperar la respuesta con timeout
            start_time = time.time()
            max_wait_time = 300  # 5 minutos máximo
            
            while True:
                if time.time() - start_time > max_wait_time:
                    raise Exception("Timeout esperando respuesta del asistente")

                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
                print(f"Estado del run: {run.status}")

                if run.status == "completed":
                    break
                elif run.status == "failed":
                    if hasattr(run, 'last_error'):
                        raise Exception(f"Run failed with error: {run.last_error}")
                    else:
                        # Obtener más detalles del error
                        run_steps = self.client.beta.threads.runs.steps.list(
                            thread_id=thread.id,
                            run_id=run.id
                        )
                        error_details = [step for step in run_steps.data if step.status == "failed"]
                        raise Exception(f"Run failed. Steps with errors: {error_details}")
                elif run.status in ["cancelled", "expired"]:
                    raise Exception(f"Run ended with status: {run.status}")
                
                time.sleep(1)  # Esperar 1 segundo antes de verificar nuevamente

            # Obtener mensajes
            print("Obteniendo mensajes...")
            messages = self.client.beta.threads.messages.list(
                thread_id=thread.id
            )

            # Obtener el último mensaje y sus anotaciones
            last_message = messages.data[0]
            print(f"Mensaje recibido: {last_message.id}")
            
            response = {
                "response": last_message.content[0].text.value,
                "thread_id": thread.id,
                "citations": [
                    annotation.text
                    for annotation in (getattr(last_message.content[0], 'annotations', []) or [])
                    if getattr(annotation, 'type', None) == "file_citation"
                ]
            }
            print("Respuesta preparada con éxito")
            return response

        except Exception as e:
            print(f"Error durante el procesamiento: {str(e)}")
            raise