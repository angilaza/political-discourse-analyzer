import time
import re
import asyncio
import os
import logging
from typing import Optional, Dict, List
from pathlib import Path
import openai
from political_discourse_analyzer.models.settings import ApplicationSettings
from openai import AssistantEventHandler

logger = logging.getLogger(__name__)

# --- EventHandler para streaming ---
class MyEventHandler(AssistantEventHandler):
    def on_text_created(self, text) -> None:
        print(f"\nassistant > ", end="", flush=True)
      
    def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=True)
      
    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call.type}\n", flush=True)
  
    def on_tool_call_delta(self, delta, snapshot):
        if delta.type == 'code_interpreter':
            if delta.code_interpreter.input:
                print(delta.code_interpreter.input, end="", flush=True)
            if delta.code_interpreter.outputs:
                print(f"\n\noutput >", flush=True)
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        print(f"\n{output.logs}", flush=True)

# --- Clase principal ---
class AssistantService:
    def __init__(self, settings: ApplicationSettings):
        self.settings = settings
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = openai.Client(api_key=api_key)
        self.assistants: Dict[str, str] = {}
        self.vector_store = None

    def _create_or_get_vector_store(self):
        """
        Crea o recupera el Vector Store para los documentos políticos.
        """
        try:
            vector_stores = self.client.beta.vector_stores.list()
            # Buscar un vector store existente llamado "Programas Políticos"
            for vs in vector_stores.data:
                if vs.name == "Programas Políticos":
                    try:
                        # Intentar listar los archivos para verificar que el vector store está activo
                        self.client.beta.vector_stores.files.list(vs.id)
                        return vs
                    except Exception as e:
                        print(f"Vector Store existente expirado o inválido: {e}")
                        try:
                            print(f"Eliminando Vector Store expirado: {vs.id}")
                            self.client.beta.vector_stores.delete(vs.id)
                        except Exception as del_e:
                            print(f"Error eliminando Vector Store: {del_e}")
            print("Creando nuevo Vector Store...")
            return self.client.beta.vector_stores.create(
                name="Programas Políticos",
                expires_after={"anchor": "last_active_at", "days": 90}
            )
        except Exception as e:
            print(f"Error en operación de Vector Store: {e}")
            raise

    def _load_documents(self):
        """
        Carga los documentos políticos en el Vector Store evitando duplicados.
        
        Para cada archivo PDF en 'data/programs', se consulta el vector store para ver si ya existe
        un archivo con ese nombre (utilizando client.beta.vector_stores.files.list y client.files.retrieve).
        Si no existe, se sube y se añade a un batch.
        """
        docs_dir = Path("data/programs")
        # Obtener la lista de archivos ya asociados al vector store
        vs_files = self.client.beta.vector_stores.files.list(self.vector_store.id)
        existing_file_names = set()
        for vs_file in vs_files.data:
            try:
                # Recuperar detalles del archivo (se asume que 'client.files.retrieve' devuelve el filename)
                file_detail = self.client.files.retrieve(vs_file.id)
                if hasattr(file_detail, "filename"):
                    existing_file_names.add(file_detail.filename)
            except Exception as e:
                print(f"Error recuperando detalles del archivo {vs_file.id}: {e}")

        new_file_ids = []
        for file_path in docs_dir.glob("*.pdf"):
            if file_path.name in existing_file_names:
                print(f"El archivo {file_path.name} ya existe en el vector store. Saltando.")
            else:
                print(f"Subiendo nuevo archivo: {file_path.name}")
                with open(file_path, "rb") as f:
                    uploaded_file = self.client.files.create(
                        file=f,
                        purpose="assistants"
                    )
                new_file_ids.append(uploaded_file.id)

        if new_file_ids:
            self.client.beta.vector_stores.file_batches.create(
                vector_store_id=self.vector_store.id,
                file_ids=new_file_ids
            )
            print(f"Añadidos {len(new_file_ids)} nuevos archivos al Vector Store")
        else:
            print("No hay nuevos archivos para cargar en el Vector Store.")

    def init_service(self):
        """
        Inicializa el servicio creando el Vector Store, cargando documentos y configurando los asistentes.
        """
        print("Iniciando servicio...")
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                self.vector_store = self._create_or_get_vector_store()
                print(f"Vector Store creado/recuperado: {self.vector_store.id}")
                # Verificar listando los archivos
                self.client.beta.vector_stores.files.list(self.vector_store.id)
                self._load_documents()
                print("Documentos cargados")
                self.init_assistants()
                print(f"Asistentes inicializados: {self.assistants}")
                break  # Todo fue exitoso, salimos
            except Exception as e:
                print(f"Intento {attempt + 1} falló: {str(e)}")
                if self.vector_store:
                    try:
                        print(f"Eliminando Vector Store inválido: {self.vector_store.id}")
                        self.client.beta.vector_stores.delete(self.vector_store.id)
                    except Exception as del_e:
                        print(f"Error eliminando Vector Store: {del_e}")
                    self.vector_store = None
                if attempt == max_attempts - 1:
                    print("Todos los intentos fallaron")
                    raise
                print("Reintentando...")
                time.sleep(1)

    def init_assistants(self):
        """
        Inicializa o recupera los asistentes.
        """
        print("Inicializando asistentes...")
        assistant_configs = {
            "neutral": {
                "name": "Asistente de Programas Electorales",
                "instructions": (
                    "Eres un asistente especializado en analizar y explicar programas electorales, basándote "
                    "estrictamente en la información contenida en los documentos oficiales. Responde únicamente "
                    "con datos objetivos extraídos de dichos documentos y evita emitir opiniones personales.\n\n"
                    
                    "1. OBJETIVO DE LA RESPUESTA:\n"
                    "   - Tu respuesta se fundamentará en el análisis de los programas electorales disponibles.\n"
                    "   - Deja claro que la información que presentas responde a la consulta realizada, por ejemplo, "
                    "     si se pregunta sobre propuestas en materia de energía, indica que respondes sobre ese tema.\n\n"
                    
                    "2. PRESENTACIÓN:\n"
                    "   - Comienza con una breve introducción que informe al usuario sobre el enfoque de la respuesta. "
                    "     Ejemplo: 'Esta respuesta se basa en el análisis de los programas electorales disponibles, de los que se extraen propuestas sobre [tema de la consulta].'\n"
                    "   - Presenta cada propuesta en párrafos separados utilizando viñetas o numeración para facilitar la lectura.\n"
                    "   - Utiliza párrafos cortos y separaciones claras para que el contenido sea fácilmente legible.\n\n"
                    
                    "3. CONTENIDO DE CADA PROPUESTA:\n"
                    "   - Resume cada propuesta de forma concisa (limitada a 2-3 líneas) sin perder claridad.\n"
                    "   - Incluye en la descripción la ubicación precisa de la información, especificando el documento "
                    "     y la sección o página de donde se extrae, utilizando el siguiente formato:\n"
                    "         > Fuente: [Nombre_del_documento]\n"
                    "         > Sección: [Nombre_de_la_sección o página X]\n\n"
                    
                    "4. SECCIÓN DE REFERENCIAS:\n"
                    "   - Al final de la respuesta, añade una sección titulada 'Fuentes:' o 'Referencias:'\n"
                    "   - En esta sección, lista de forma ordenada todas las fuentes utilizadas, en el orden en que "
                    "     aparecen en el cuerpo de la respuesta.\n\n"
                    
                    "5. EJEMPLO DE ESTRUCTURA DE RESPUESTA:\n"
                    "   - Introducción breve:\n"
                    "         'Esta respuesta se basa en el análisis de los programas electorales disponibles, "
                    "          focalizándose en las propuestas sobre [tema].'\n\n"
                    "   - Propuestas (presentadas en párrafos separados o en lista):\n"
                    "         1. **[Partido] - [Título de la propuesta]**: Breve descripción de la propuesta.\n"
                    "            > Fuente: [Documento]\n"
                    "            > Sección: [Sección o página]\n\n"
                    "         2. **[Otro Partido] - [Título de la propuesta]**: Breve descripción de la propuesta.\n"
                    "            > Fuente: [Documento]\n"
                    "            > Sección: [Sección o página]\n\n"
                    "   - Sección final de referencias:\n"
                    "         Fuentes:\n"
                    "         - [Documento] - Sección: [Sección o página]\n"
                    "         - [Otro Documento] - Sección: [Sección o página]\n\n"
                    
                    "6. DIRECTRICES ADICIONALES:\n"
                    "   - Responde de forma objetiva y sin añadir juicios personales.\n"
                    "   - Limita la respuesta a las 4-5 propuestas más relevantes según la consulta.\n"
                    "   - No agregues información que no esté respaldada por los documentos.\n"
                )
            }
        }
        try:
            existing_assistants = {
                asst.name: asst.id 
                for asst in self.client.beta.assistants.list().data
            }
            print(f"Asistentes existentes: {existing_assistants}")
            for mode, config in assistant_configs.items():
                try:
                    if config["name"] in existing_assistants:
                        assistant_id = existing_assistants[config["name"]]
                        print(f"Actualizando asistente para modo {mode}: {assistant_id}")
                        try:
                            assistant = self.client.beta.assistants.update(
                                assistant_id=assistant_id,
                                name=config["name"],
                                instructions=config["instructions"],
                                model="gpt-4-turbo-preview",
                                tools=[{"type": "file_search"}],
                                tool_resources={"file_search": {"vector_store_ids": [self.vector_store.id]}},
                                metadata={"mode": mode}
                            )
                        except Exception as update_error:
                            print(f"Error actualizando asistente {mode}, creando nuevo: {update_error}")
                            assistant = self.client.beta.assistants.create(
                                name=config["name"],
                                instructions=config["instructions"],
                                model="gpt-4-turbo-preview",
                                tools=[{"type": "file_search"}],
                                tool_resources={"file_search": {"vector_store_ids": [self.vector_store.id]}},
                                metadata={"mode": mode}
                            )
                    else:
                        print(f"Creando nuevo asistente para modo {mode}")
                        assistant = self.client.beta.assistants.create(
                            name=config["name"],
                            instructions=config["instructions"],
                            model="gpt-4-turbo-preview",
                            tools=[{"type": "file_search"}],
                            tool_resources={"file_search": {"vector_store_ids": [self.vector_store.id]}},
                            metadata={"mode": mode}
                        )
                    self.assistants[mode] = assistant.id
                    print(f"Asistente {mode} configurado con ID: {assistant.id}")
                except Exception as e:
                    print(f"Error configurando asistente {mode}: {e}")
                    raise
        except Exception as e:
            print(f"Error listando asistentes: {e}")
            raise

    def _format_response(self, raw_response: str) -> str:
        """
        Reformatea la respuesta para mejorar su legibilidad.
        
        Se insertan saltos de línea antes de cada propuesta numerada y se fuerza que las citas
        ("> Fuente:" y "> Sección:") aparezcan en líneas separadas.
        """
        # Insertar salto de línea antes de propuestas numeradas (si no hay ya uno)
        formatted = re.sub(r'(?<!\n)(\d+\.\s*\*\*)', r'\n\n\1', raw_response)
        # Forzar que "> Fuente:" y "> Sección:" estén en líneas separadas
        formatted = re.sub(r'\s*(>\s*Fuente:)', r'\n\1', formatted)
        formatted = re.sub(r'\s*(>\s*Sección:)', r'\n\1', formatted)
        # Añadir línea en blanco antes de la sección de fuentes si no existe
        formatted = re.sub(r'(\nFuentes:)', r'\n\n\1', formatted)
        # Limpiar líneas en blanco y espacios extra
        lines = [line.strip() for line in formatted.splitlines() if line.strip()]
        formatted = "\n\n".join(lines)
        return formatted

    async def process_query(self, query: str, mode: str = "neutral", thread_id: Optional[str] = None) -> dict:
        """
        Procesa una consulta usando el asistente configurado, obtiene la respuesta por streaming,
        la formatea y extrae las citas.
        """
        if mode not in self.assistants:
            raise ValueError(f"Modo no válido: {mode}")

        try:
            # Crear o recuperar thread
            thread = (self.client.beta.threads.retrieve(thread_id)
                      if thread_id else self.client.beta.threads.create())

            context_prompts = {
                "neutral": "Por favor, proporciona una respuesta estructurada y formateada, incluyendo citas específicas de los documentos.",
                "personal": "Por favor, explica esto de forma conversacional pero incluyendo referencias específicas."
            }
            full_query = f"{context_prompts[mode]}\n\nConsulta del usuario: {query}"
            
            # Enviar mensaje de consulta
            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=full_query
            )

            # Usar streaming para crear el run y procesar la respuesta en tiempo real
            event_handler = MyEventHandler()
            with self.client.beta.threads.runs.stream(
                thread_id=thread.id,
                assistant_id=self.assistants[mode],
                event_handler=event_handler,
            ) as stream:
                stream.until_done()

            # Recuperar el mensaje final del thread
            messages = self.client.beta.threads.messages.list(thread_id=thread.id)
            last_message = messages.data[0]

            # Extraer citas de las anotaciones (si las hay)
            citations = []
            annotations = getattr(last_message.content[0], 'annotations', []) or []
            for annotation in annotations:
                if getattr(annotation, 'type', None) == "file_citation":
                    citation = {
                        'text': annotation.text,
                        'file_citation': annotation.file_citation.quote,
                        'file_path': annotation.file_citation.file_path
                    }
                    citations.append(citation)

            raw_response = last_message.content[0].text.value
            formatted_response = self._format_response(raw_response)
            
            response = {
                'response': formatted_response,
                'thread_id': thread.id,
                'citations': citations
            }
            return response

        except Exception as e:
            logger.error(f"Error en process_query: {str(e)}", exc_info=True)
            raise
