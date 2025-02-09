# src/political_discourse_analyzer/services/analytics_service.py
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from openai import OpenAI
from sqlalchemy import func 
from .database_service import DatabaseService, Interaction, Conversation

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        try:
            self.nlp = spacy.load('es_core_news_md')
        except OSError:
            logger.warning("Descargando modelo de spaCy...")
            import os
            os.system('python -m spacy download es_core_news_md')
            self.nlp = spacy.load('es_core_news_md')
        
        self.client = OpenAI()
        
        # Categorías políticas con descriptores expandidos
        self.categories = {
            'economía': {
                'keywords': ['economía', 'impuestos', 'trabajo', 'empleo', 'paro', 'salario', 'pensiones'],
                'descriptors': ['mercado laboral', 'inflación', 'precio', 'coste de vida', 'autónomo', 
                              'empresa', 'inversión', 'subvención', 'ayuda económica']
            },
            'sanidad': {
                'keywords': ['sanidad', 'salud', 'hospital', 'médico', 'sanitario'],
                'descriptors': ['atención primaria', 'lista de espera', 'centro de salud', 
                              'ambulatorio', 'urgencias', 'especialista']
            },
            'educación': {
                'keywords': ['educación', 'universidad', 'escuela', 'estudios', 'becas'],
                'descriptors': ['formación', 'profesorado', 'enseñanza', 'colegio', 'instituto',
                              'máster', 'investigación', 'ciencia']
            },
            'vivienda': {
                'keywords': ['vivienda', 'alquiler', 'hipoteca', 'casa'],
                'descriptors': ['precio vivienda', 'acceso vivienda', 'compra', 'venta', 'inmobiliario',
                              'construcción', 'promotor', 'urbanismo']
            },
            'medio_ambiente': {
                'keywords': ['clima', 'ambiente', 'sostenible', 'energía', 'renovable'],
                'descriptors': ['cambio climático', 'contaminación', 'reciclaje', 'transición ecológica',
                              'biodiversidad', 'emisiones']
            },
            'derechos_sociales': {
                'keywords': ['igualdad', 'feminismo', 'derechos', 'social'],
                'descriptors': ['discriminación', 'violencia de género', 'conciliación', 'brecha salarial',
                              'inclusión', 'diversidad']
            },
            'seguridad': {
                'keywords': ['seguridad', 'policía', 'delincuencia', 'justicia'],
                'descriptors': ['criminalidad', 'orden público', 'terrorismo', 'ciberseguridad',
                              'judicial', 'legislación']
            }
        }

    async def analyze_topic_with_embeddings(self, query: str) -> List[Tuple[str, float]]:
        """Análisis mediante embeddings de OpenAI."""
        try:
            query_embedding = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=query
            ).data[0].embedding

            category_scores = []
            for category, descriptors in self.categories.items():
                category_text = f"{category}: {', '.join(descriptors['keywords'] + descriptors['descriptors'])}"
                category_embedding = self.client.embeddings.create(
                    model="text-embedding-3-small",
                    input=category_text
                ).data[0].embedding

                similarity = cosine_similarity(
                    [query_embedding],
                    [category_embedding]
                )[0][0]
                
                category_scores.append((category, float(similarity)))

            return sorted(category_scores, key=lambda x: x[1], reverse=True)
        except Exception as e:
            logger.error(f"Error en análisis de embeddings: {str(e)}")
            return [(category, 0.0) for category in self.categories]

    async def analyze_topic_with_llm(self, query: str) -> Dict[str, float]:
        """Análisis mediante GPT-4."""
        try:
            prompt = f"""Analiza la siguiente consulta sobre política y asigna porcentajes de relevancia
            para cada categoría (la suma debe ser 100%). Las categorías son: {list(self.categories.keys())}.
            
            Consulta: {query}
            
            Tu respuesta debe ser un objeto JSON con las categorías como claves y los porcentajes como valores.
            Por ejemplo: {{"economía": 60, "sanidad": 40}}"""

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un analista experto en política española. Responde siempre en formato JSON."},
                    {"role": "user", "content": prompt}
                ]
            )

            # Parsear la respuesta como JSON
            try:
                return json.loads(response.choices[0].message.content)
            except json.JSONDecodeError as e:
                logger.error(f"Error decodificando JSON de GPT-4: {str(e)}")
                logger.error(f"Contenido recibido: {response.choices[0].message.content}")
                return {category: 0.0 for category in self.categories}

        except Exception as e:
            logger.error(f"Error en análisis LLM: {str(e)}")
            return {category: 0.0 for category in self.categories}

    def analyze_topic_with_spacy(self, query: str) -> Dict[str, float]:
        """Análisis lingüístico con spaCy."""
        try:
            doc = self.nlp(query)
            entities = [ent.text.lower() for ent in doc.ents]
            main_tokens = [token.text.lower() for token in doc if token.dep_ in ['ROOT', 'nsubj', 'dobj']]
            
            scores = {}
            for category, info in self.categories.items():
                category_text = ' '.join(info['keywords'] + info['descriptors'])
                category_doc = self.nlp(category_text)
                
                semantic_score = doc.similarity(category_doc)
                entity_score = len(set(entities) & set(info['keywords'] + info['descriptors'])) / len(info['keywords'])
                token_score = len(set(main_tokens) & set(info['keywords'] + info['descriptors'])) / len(info['keywords'])
                
                scores[category] = (semantic_score + entity_score + token_score) / 3

            return scores
        except Exception as e:
            logger.error(f"Error en análisis spaCy: {str(e)}")
            return {category: 0.0 for category in self.categories}

    async def get_topic_distribution(self, 
                                   start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None) -> Dict:
        """Análisis combinado de distribución de temas."""
        with self.db_service.SessionLocal() as db:
            query = db.query(Interaction.query)
            if start_date:
                query = query.filter(Interaction.timestamp >= start_date)
            if end_date:
                query = query.filter(Interaction.timestamp <= end_date)
            
            interactions = query.all()
            
            if not interactions:
                return {
                    "status": "no_data",
                    "message": "No se encontraron interacciones en el período especificado"
                }
            
            results = {
                'embedding_analysis': {},
                'llm_analysis': {},
                'linguistic_analysis': {},
                'combined_analysis': {}
            }
            
            for interaction in interactions:
                embedding_scores = await self.analyze_topic_with_embeddings(interaction.query)
                llm_scores = await self.analyze_topic_with_llm(interaction.query)
                spacy_scores = self.analyze_topic_with_spacy(interaction.query)
                
                for category in self.categories:
                    results['embedding_analysis'][category] = results['embedding_analysis'].get(category, 0) + \
                        [score for cat, score in embedding_scores if cat == category][0]
                    results['llm_analysis'][category] = results['llm_analysis'].get(category, 0) + \
                        float(llm_scores.get(category, 0))
                    results['linguistic_analysis'][category] = results['linguistic_analysis'].get(category, 0) + \
                        spacy_scores.get(category, 0)

            # Normalizar resultados
            n_interactions = len(interactions)
            for analysis_type in results:
                for category in results[analysis_type]:
                    results[analysis_type][category] /= n_interactions

            # Análisis combinado
            for category in self.categories:
                results['combined_analysis'][category] = (
                    results['embedding_analysis'][category] +
                    results['llm_analysis'][category] +
                    results['linguistic_analysis'][category]
                ) / 3

            return {
                "status": "success",
                "total_interactions": n_interactions,
                "period": {
                    "start": start_date.isoformat() if start_date else "all",
                    "end": end_date.isoformat() if end_date else "all"
                },
                "results": results
            }

    async def get_engagement_metrics(self) -> Dict:
        """Métricas de engagement de usuarios."""
        with self.db_service.SessionLocal() as db:
            try:
                avg_interactions = db.query(
                    func.avg(Conversation.total_interactions)
                ).scalar() or 0

                duration_query = db.query(
                    func.avg(
                        func.extract('epoch', 
                            Conversation.last_interaction - Conversation.created_at
                        )
                    )
                ).scalar() or 0

                total_conversations = db.query(Conversation).count()
                followup_conversations = db.query(Conversation).filter(
                    Conversation.total_interactions > 1
                ).count()

                followup_rate = (followup_conversations / total_conversations * 100) if total_conversations > 0 else 0

                return {
                    "status": "success",
                    "metrics": {
                        "average_interactions_per_conversation": round(float(avg_interactions), 2),
                        "average_conversation_duration_minutes": round(duration_query / 60, 2),
                        "followup_rate_percentage": round(followup_rate, 2),
                        "total_conversations": total_conversations,
                        "total_followup_conversations": followup_conversations
                    }
                }
            except Exception as e:
                logger.error(f"Error getting engagement metrics: {str(e)}")
                return {
                    "status": "error",
                    "message": str(e)
                }

    async def generate_comprehensive_report(self, 
                                         start_date: Optional[datetime] = None,
                                         end_date: Optional[datetime] = None) -> Dict:
        """Genera un informe completo de análisis."""
        try:
            topics = await self.get_topic_distribution(start_date, end_date)
            engagement = await self.get_engagement_metrics()

            return {
                "status": "success",
                "timestamp": datetime.utcnow().isoformat(),
                "period": {
                    "start": start_date.isoformat() if start_date else "all",
                    "end": end_date.isoformat() if end_date else "all"
                },
                "topic_analysis": topics,
                "engagement_metrics": engagement
            }
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }