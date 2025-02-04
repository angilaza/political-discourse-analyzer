import time
from typing import Optional, Dict, List
import openai
from pathlib import Path
from political_discourse_analyzer.models.settings import ApplicationSettings
import os
import asyncio

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
            # Listar Vector Stores existentes
            vector_stores = self.client.beta.vector_stores.list()
            
            # Buscar un Vector Store existente llamado "Programas Políticos"
            for vs in vector_stores.data:
                if vs.name == "Programas Políticos":
                    try:
                        # Verificar si el Vector Store está activo
                        self.client.beta.vector_stores.files.list(vs.id)
                        return vs
                    except Exception as e:
                        print(f"Vector Store existente expirado o inválido: {e}")
                        try:
                            print(f"Eliminando Vector Store expirado: {vs.id}")
                            self.client.beta.vector_stores.delete(vs.id)
                        except Exception as del_e:
                            print(f"Error eliminando Vector Store: {del_e}")
                            pass

            print("Creando nuevo Vector Store...")
            # Crear nuevo Vector Store
            return self.client.beta.vector_stores.create(
                name="Programas Políticos",
                expires_after={
                    "anchor": "last_active_at",
                    "days": 90
                }
            )
        except Exception as e:
            print(f"Error en operación de Vector Store: {e}")
            raise

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
        
        # Intentar obtener o crear Vector Store hasta que tengamos uno válido
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Crear Vector Store
                self.vector_store = self._create_or_get_vector_store()
                print(f"Vector Store creado/recuperado: {self.vector_store.id}")
                
                # Verificar que el Vector Store está activo
                self.client.beta.vector_stores.files.list(self.vector_store.id)
                
                # Si llegamos aquí, el Vector Store es válido
                # Cargar documentos al Vector Store
                self._load_documents()
                print("Documentos cargados")
                
                # Inicializar asistentes
                self.init_assistants()
                print(f"Asistentes inicializados: {self.assistants}")
                
                # Si todo fue exitoso, salir del bucle
                break
                
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
                time.sleep(1)  # Esperar un segundo antes de reintentar

    def init_assistants(self):
        """
        Inicializa o recupera los asistentes.
        """
        print("Inicializando asistentes...")
        
        # Configuración de los asistentes
        assistant_configs = {
            "neutral": {
                "name": "Asistente de Programas Electorales",
                "instructions": ("Eres un asistente especializado en analizar y explicar programas electorales, basándote "
                    "estrictamente en la información contenida en los documentos oficiales. Responde únicamente "
                    "con datos objetivos extraídos de dichos documentos y evita emitir opiniones personales.\n\n"
                    
                    "1. OBJETIVO DE LA RESPUESTA:\n"
                    "   - Tu respuesta se fundamentará en el análisis de los programas electorales disponibles.\n"
                    "   - Deja claro que la información que presentas responde a la consulta realizada, por ejemplo, "
                    "     si se pregunta sobre propuestas en materia de energía, indica que respondes sobre ese tema.\n\n"
                    
                    "2. PRESENTACIÓN:\n"
                    "   - Comienza con una breve introducción que informe al usuario sobre el enfoque de la respuesta. "
                    "     Ejemplo: 'Esta respuesta se basa en el análisis de los programas electorales disponibles, en los que se extraen propuestas sobre [tema de la consulta].'\n"
                    "   - Presenta cada propuesta en párrafos separados utilizando viñetas o numeración para facilitar la lectura.\n"
                    "   - Utiliza párrafos cortos y separaciones claras para que el contenido sea fácilmente legible.\n\n"
                    
                    "3. CONTENIDO DE CADA PROPUESTA:\n"
                    "   - Resume cada propuesta de forma concisa (limitada a 2-3 líneas) sin perder claridad.\n"
                    "   - Incluye en la descripción la ubicación precisa de la información, especificando el documento "
                    "     y la sección o página de donde se extrae, utilizando el siguiente formato: \n"
                    "       > Fuente: [Nombre_del_documento]\n"
                    "       > Sección: [Nombre_de_la_sección o página X]\n\n"
                    
                    "4. SECCIÓN DE REFERENCIAS:\n"
                    "   - Al final de la respuesta, añade una sección titulada 'Fuentes:' o 'Referencias:'\n"
                    "   - En esta sección, lista de forma ordenada todas las fuentes utilizadas, en el orden en que "
                    "     aparecen en el cuerpo de la respuesta.\n\n"
                    
                    "5. EJEMPLO DE ESTRUCTURA DE RESPUESTA:\n"
                    "   - Introducción breve:\n"
                    "       'Esta respuesta se basa en el análisis de los programas electorales disponibles, "
                    "        focalizándose en las propuestas sobre [tema].'\n\n"
                    "   - Propuestas (presentadas en párrafos separados o en lista):\n"
                    "       1. **[Partido] - [Título de la propuesta]**: Breve descripción de la propuesta. \n"
                    "          > Fuente: [Documento]\n"
                    "          > Sección: [Sección o página]\n\n"
                    "       2. **[Otro Partido] - [Título de la propuesta]**: Breve descripción de la propuesta. \n"
                    "          > Fuente: [Documento]\n"
                    "          > Sección: [Sección o página]\n\n"
                    "   - Sección final de referencias:\n"
                    "       Fuentes:\n"
                    "       - [Documento] - Sección: [Sección o página]\n"
                    "       - [Otro Documento] - Sección: [Sección o página]\n\n"
                    
                    "6. DIRECTRICES ADICIONALES:\n"
                    "   - Responde de forma objetiva y sin añadir juicios personales.\n"
                    "   - Limita la respuesta a las 4-5 propuestas más relevantes según la consulta.\n"
                    "   - No agregues información que no esté respaldada por los documentos.\n"
                )
            }
        }

        # Obtener lista de asistentes existentes
        try:
            existing_assistants = {
                asst.name: asst.id 
                for asst in self.client.beta.assistants.list().data
            }
            print(f"Asistentes existentes: {existing_assistants}")

            # Crear o actualizar cada asistente
            for mode, config in assistant_configs.items():
                try:
                    if config["name"] in existing_assistants:
                        assistant_id = existing_assistants[config["name"]]
                        print(f"Actualizando asistente para modo {mode}: {assistant_id}")
                        
                        # Intentar actualizar el asistente
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
                            # Si falla la actualización, crear nuevo asistente
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
        Asegura que la respuesta sigue el formato establecido.
        """
        # Dividir en secciones principales
        sections = raw_response.split('\n\n')
        
        # Asegurar que los títulos están en mayúsculas
        formatted_sections = []
        for section in sections:
            # Si es una línea que parece un título (sin ">" y sin "-")
            if section.strip() and '>' not in section and '-' not in section:
                words = section.split()
                if len(words) <= 5:  # Probable título
                    section = section.upper()
            formatted_sections.append(section)
        
        # Reconstruir con espaciado correcto
        formatted_response = '\n\n'.join(formatted_sections)
        
        return formatted_response

    async def process_query(self, query: str, mode: str = "neutral", thread_id: Optional[str] = None) -> dict:
        """
        Procesa una consulta usando el asistente apropiado con mejor manejo de citas.
        """
        if mode not in self.assistants:
            raise ValueError(f"Modo no válido: {mode}")

        try:
            # Crear o recuperar thread
            thread = (self.client.beta.threads.retrieve(thread_id) if thread_id 
                     else self.client.beta.threads.create())

            # Añadir mensaje con contexto específico según el modo
            context_prompts = {
                "neutral": "Por favor, proporciona una respuesta estructurada con citas específicas de los documentos.",
                "personal": "Por favor, explica esto de forma conversacional pero incluyendo referencias específicas."
            }
            
            full_query = f"{context_prompts[mode]}\n\nConsulta del usuario: {query}"
            
            message = self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=full_query
            )

            # Ejecutar el asistente
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistants[mode]
            )

            # Esperar respuesta con mejor manejo de errores
            start_time = time.time()
            while True:
                if time.time() - start_time > 300:  # 5 minutos timeout
                    raise TimeoutError("La respuesta tardó demasiado")

                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )

                if run.status == "completed":
                    break
                elif run.status in ["failed", "cancelled", "expired"]:
                    raise Exception(f"Error en la ejecución: {run.status}")
                
                await asyncio.sleep(1)

            # Procesar la respuesta y las citas
            messages = self.client.beta.threads.messages.list(thread_id=thread.id)
            last_message = messages.data[0]

            # Extraer y formatear las citas
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

            # Formatear y estructurar la respuesta
            raw_response = last_message.content[0].text.value
            formatted_response = self._format_response(raw_response)
            
            # Formatear la respuesta final
            response = {
                'response': formatted_response,
                'thread_id': thread.id,
                'citations': citations
            }

            return response

        except Exception as e:
            logger.error(f"Error en process_query: {str(e)}", exc_info=True)
            raise