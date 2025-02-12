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
        assistant_configs = {
            "neutral": {
                "name": "Asistente de Programas Electorales",
                "instructions": (
                    "Eres un asistente especializado en analizar programas electorales. "
                    "Estructura tus respuestas siguiendo este formato:\n\n"
                    
                    "1. ESTRUCTURA:\n"
                    "- Introducción breve (1 línea)\n"
                    "- Lista numerada de propuestas\n"
                    "- Referencias al final\n\n"
                    
                    "2. FORMATO DE PROPUESTAS:\n"
                    "Estructura tus respuestas así:\n\n"
                    
                    "Las principales propuestas [del partido] para [tema] son:\n\n"
                    
                    "1. **[Título de la Propuesta]**:\n"
                    "   - [Descripción concisa] (Documento.pdf, Sección o página X)\n\n"
                    
                    "2. **[Siguiente Propuesta]**:\n"
                    "   - [Descripción] (Documento.pdf, Sección o página X)\n\n"
                    
                    "Referencias:\n"
                    "   - Documento: [Nombre_completo]\n\n"
                    
                    "3. REGLAS:\n"
                    "- Citas integradas en el texto entre paréntesis\n"
                    "- Referencias completas al final\n"
                    "- Usa numeración continua (1, 2, 3...)\n"
                    "- Máximo 4-5 propuestas relevantes\n"
                    "- Solo información respaldada por documentos\n"
                    "- Sin espacios dobles entre elementos\n"
                    "- Descripciones concisas y comprensivas para cualquier público\n"
                    "- No inventes páginas o información\n"
                    "- No atribuyas propuestas a partidos que no las mencionen\n"
                    "- No uses etiquetas de referencia como 【4:0†source】, 【4:1†source】, 【n:m†source】; omite cualquier marcador de referencia de este formato.\n"
                    "- Evita cualquier formato de referencia automático que no siga las reglas aquí establecidas.\n"

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
                                model=self.settings.ai_settings.model,
                                tools=[{"type": "file_search"}],
                                tool_resources={"file_search": {"vector_store_ids": [self.vector_store.id]}},
                                metadata={"mode": mode}
                            )
                        except Exception as update_error:
                            print(f"Error actualizando asistente {mode}, creando nuevo: {update_error}")
                            assistant = self.client.beta.assistants.create(
                                name=config["name"],
                                instructions=config["instructions"],
                                model=self.settings.ai_settings.model,
                                tools=[{"type": "file_search"}],
                                tool_resources={"file_search": {"vector_store_ids": [self.vector_store.id]}},
                                metadata={"mode": mode}
                            )
                    else:
                        print(f"Creando nuevo asistente para modo {mode}")
                        assistant = self.client.beta.assistants.create(
                            name=config["name"],
                            instructions=config["instructions"],
                            model=self.settings.ai_settings.model,
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
        Reformatea la respuesta para mejorar su legibilidad y el formato Markdown.
        """
        # Eliminar los identificadores de citation
        formatted = re.sub(r'\s*\【\d+:\d+†?source\】', '', raw_response)
        
        # Convertir los puntos en una lista numerada continua
        lines = formatted.split('\n')
        counter = 1
        new_lines = []
        
        for line in lines:
            # Si es una línea que comienza con número, actualizarla con el contador
            if re.match(r'^\d+\.\s*', line):
                line = re.sub(r'^\d+\.', f"{counter}.", line)
                counter += 1
            
            # Ajustar indentación de las fuentes
            if 'Fuente:' in line:
                line = f"    • {line.strip().replace('• Fuente:', 'Fuente:')}"
            
            new_lines.append(line)
        
        # Unir las líneas y eliminar espacios extra
        formatted = '\n'.join(line for line in new_lines if line.strip())
        
        return formatted

    async def process_query(self, query: str, mode: str = "neutral", thread_id: Optional[str] = None) -> dict:
        """
        Procesa una consulta usando el asistente configurado y obtiene la respuesta.
        """
        if mode not in self.assistants:
            raise ValueError(f"Modo no válido: {mode}")

        try:
            # Crear o recuperar thread
            thread = (self.client.beta.threads.retrieve(thread_id)
                    if thread_id else self.client.beta.threads.create())

            context_prompts = {
                "neutral": "Por favor, proporciona una respuesta estructurada con citas específicas de los documentos.",
                "personal": "Por favor, explica esto de forma conversacional pero incluyendo referencias específicas."
            }
            full_query = f"{context_prompts[mode]}\n\nConsulta del usuario: {query}"
            
            # Enviar mensaje de consulta
            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=full_query
            )

            # Procesar la respuesta con streaming
            event_handler = MyEventHandler()
            with self.client.beta.threads.runs.stream(
                thread_id=thread.id,
                assistant_id=self.assistants[mode],
                event_handler=event_handler,
            ) as stream:
                stream.until_done()

            # Recuperar el mensaje final
            messages = self.client.beta.threads.messages.list(thread_id=thread.id)
            last_message = messages.data[0]
            
            # Extraer la respuesta y citas
            response = {
                'response': last_message.content[0].text.value,
                'thread_id': thread.id,
                'citations': []
            }

            # Extraer citas si existen
            annotations = getattr(last_message.content[0], 'annotations', []) or []
            for annotation in annotations:
                if getattr(annotation, 'type', None) == "file_citation":
                    citation = {
                        'text': annotation.text,
                        'quote': annotation.file_citation.quote,
                        'file_path': annotation.file_citation.file_path
                    }
                    response['citations'].append(citation)

            return response

        except Exception as e:
            logger.error(f"Error en process_query: {str(e)}", exc_info=True)
            raise