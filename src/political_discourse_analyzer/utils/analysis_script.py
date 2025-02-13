# src/political_discourse_analyzer/utils/analysis_script.py

import os
import asyncio
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from dotenv import load_dotenv
from pathlib import Path
import logging
from sklearn.metrics import confusion_matrix
from scipy import stats
import networkx as nx
from wordcloud import WordCloud
import re
import jinja2
import markdown

# Importar los modelos y servicios
from political_discourse_analyzer.services.database_service import DatabaseService, Interaction, Conversation
from political_discourse_analyzer.services.analytics_service import AnalyticsService

# Importar el generador de reportes
from political_discourse_analyzer.utils.report_generator import ReportGenerator


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_environment():
    """Carga las variables de entorno necesarias."""
    # Buscar el archivo .env en la jerarquía de directorios
    current_dir = Path(__file__).resolve().parent
    while current_dir != current_dir.parent:
        env_file = current_dir / '.env'
        if env_file.exists():
            load_dotenv(env_file)
            logger.info(f"Variables de entorno cargadas desde {env_file}")
            break
        current_dir = current_dir.parent

    # Configurar el entorno como producción
    os.environ['ENVIRONMENT'] = 'production'
    
    # Verificar la URL de la base de datos de Railway
    if not os.getenv('DATABASE_URL'):
        raise EnvironmentError(
            "DATABASE_URL no encontrada. Asegúrate de tener configurada la URL de Railway"
        )

    # Verificar otras variables requeridas
    required_vars = [
        'OPENAI_API_KEY',
        'DATABASE_URL'
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(
            f"Faltan las siguientes variables de entorno: {', '.join(missing_vars)}"
        )

# Configuración de estilo para visualizaciones académicas
plt.style.use('seaborn-v0_8-paper')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12

class CitizenInterestAnalyzer:
    def __init__(self):
        try:
            self.db_service = DatabaseService()
            self.analytics_service = AnalyticsService(self.db_service)
            self._setup_analysis_parameters() 
            logger.info("Servicios inicializados correctamente")
        except Exception as e:
            logger.error(f"Error inicializando servicios: {str(e)}")
            raise
    
    def get_basic_statistics(self) -> Dict:
        """Obtiene estadísticas básicas de las interacciones."""
        try:
            with self.db_service.SessionLocal() as db:
                stats = self.db_service.get_analytics()
                total_convs = stats["total_conversations"]
                total_ints = stats["total_interactions"]
                
                # Obtener queries de las interacciones
                interactions = db.query(Interaction).all()
                queries = [interaction.query for interaction in interactions]
                
                return {
                    "total_conversations": total_convs,
                    "total_interactions": total_ints,
                    "modes_distribution": stats["modes_distribution"],
                    "average_interactions": total_ints / total_convs if total_convs > 0 else 0,
                    "interactions": interactions,  # Necesario para análisis posteriores
                    "unique_users": len(set(interaction.thread_id for interaction in interactions)),
                    "queries": queries  # Para análisis de texto
                }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas básicas: {str(e)}")
            raise
    
    def _setup_analysis_parameters(self):
        """Configura parámetros para el análisis."""
        self.correlation_threshold = 0.7
        self.topic_similarity_threshold = 0.6


    def analyze_topic_relationships(self, topic_analysis: Dict) -> Dict:
        """Analiza las relaciones entre temas y sus interconexiones."""
        try:
            # Crear DataFrame con la estructura correcta
            combined_analysis = topic_analysis['results']['combined_analysis']
            if not combined_analysis:
                return {
                    'correlation_matrix': {},
                    'centrality_measures': {'degree': {}, 'betweenness': {}, 'eigenvector': {}},
                    'graph': nx.Graph()
                }
                
            topics_df = pd.DataFrame({
                'value': combined_analysis.values()
            }, index=combined_analysis.keys())
            
            # Verifica que hay datos válidos
            if topics_df['value'].isna().any() or len(topics_df) < 2:
                return {
                    'correlation_matrix': {},
                    'centrality_measures': {'degree': {}, 'betweenness': {}, 'eigenvector': {}},
                    'graph': nx.Graph()
                }
            
            # Verifica que hay suficientes datos
            if len(topics_df) <= 1:
                return {
                    'correlation_matrix': {},
                    'centrality_measures': {
                        'degree': {},
                        'betweenness': {},
                        'eigenvector': {}
                    },
                    'graph': nx.Graph()
                }
            
            # Calcular matriz de correlación
            correlation_matrix = pd.DataFrame(
                index=topics_df.index,
                columns=topics_df.index,
                data=np.eye(len(topics_df))  # Inicializar con matriz identidad
            )
            
            # Calcular correlaciones
            for i in topics_df.index:
                for j in topics_df.index:
                    if i < j:  # Solo necesitamos calcular la mitad superior
                        corr = np.corrcoef(
                            [topics_df.loc[i, 'value']],
                            [topics_df.loc[j, 'value']]
                        )[0, 1]
                        correlation_matrix.loc[i, j] = corr
                        correlation_matrix.loc[j, i] = corr
            
            # Crear grafo de relaciones
            G = nx.Graph()
            for i in correlation_matrix.index:
                for j in correlation_matrix.columns:
                    if i < j:
                        correlation = abs(correlation_matrix.loc[i, j])
                        if correlation > self.correlation_threshold:
                            G.add_edge(i, j, weight=correlation)
            
            # Calcular métricas de centralidad
            if len(G.nodes()) > 0:
                centrality = {
                    'degree': nx.degree_centrality(G),
                    'betweenness': nx.betweenness_centrality(G),
                    'eigenvector': nx.eigenvector_centrality(G, max_iter=1000)
                }
            else:
                centrality = {
                    'degree': {},
                    'betweenness': {},
                    'eigenvector': {}
                }
            
            return {
                'correlation_matrix': correlation_matrix.to_dict(),
                'centrality_measures': centrality,
                'graph': G
            }
        except Exception as e:
            logger.error(f"Error en análisis de relaciones entre temas: {str(e)}")
            raise

    def calculate_citizen_interest_metrics(self, data: Dict) -> Dict:
        """Calcula métricas sobre los intereses ciudadanos."""
        metrics = {}
        
        # Índice de diversidad de intereses
        topic_distributions = pd.Series(data['results']['combined_analysis'])
        metrics['interest_diversity'] = -(topic_distributions * np.log(topic_distributions)).sum()
        
        # Temas dominantes
        metrics['dominant_topics'] = topic_distributions.nlargest(3)
        
        # Comparación de métodos
        method_correlations = {}
        methods = ['embedding_analysis', 'llm_analysis', 'linguistic_analysis']
        for m1 in methods:
            for m2 in methods:
                if m1 < m2:
                    data1 = pd.Series(data['results'].get(m1, {}))
                    data2 = pd.Series(data['results'].get(m2, {}))
                    
                    # Evita errores si hay datos vacíos
                    if len(data1) > 1 and len(data2) > 1:
                        corr = data1.corr(data2)
                        method_correlations[f"{m1}_vs_{m2}"] = corr
                    else:
                        method_correlations[f"{m1}_vs_{m2}"] = np.nan  # O algún otro valor de control
        
        metrics['method_correlations'] = method_correlations
        
        return metrics

    def generate_analysis_visualizations(self, topic_analysis: Dict, topic_relationships: Dict, output_dir: str):
        """Genera visualizaciones del análisis."""
        try:
            # 1. Comparación de métodos de análisis
            methods_data = {
                'Embeddings': topic_analysis['results']['embedding_analysis'],
                'LLM': topic_analysis['results']['llm_analysis'],
                'Lingüístico': topic_analysis['results']['linguistic_analysis'],
                'Combinado': topic_analysis['results']['combined_analysis']
            }
            
            methods_df = pd.DataFrame(methods_data)
            
            plt.figure(figsize=(15, 10))
            sns.heatmap(methods_df.corr(), 
                    annot=True, 
                    cmap='RdYlBu_r',
                    center=0,
                    square=True)
            plt.title('Correlación entre Métodos de Análisis')
            plt.tight_layout()
            plt.savefig(f"{output_dir}/method_comparison.png", dpi=300)
            plt.close()

            # 2. Distribución de temas por método
            fig, axes = plt.subplots(2, 2, figsize=(20, 15))
            methods = {
                (0,0): ('embedding_analysis', 'Análisis por Embeddings'),
                (0,1): ('llm_analysis', 'Análisis por LLM'),
                (1,0): ('linguistic_analysis', 'Análisis Lingüístico'),
                (1,1): ('combined_analysis', 'Análisis Combinado')
            }
            
            for pos, (method, title) in methods.items():
                # Convertir datos a DataFrame en el formato correcto
                data = pd.DataFrame.from_dict(
                    topic_analysis['results'][method], 
                    orient='index',
                    columns=['score']
                ).reset_index()
                data.columns = ['category', 'score']  # Renombrar columnas
                
                # Crear el gráfico de barras
                sns.barplot(
                    data=data,
                    x='score',
                    y='category',
                    ax=axes[pos[0]][pos[1]],
                    hue='category',
                    legend=False, 
                    palette='viridis'
                )
                axes[pos[0]][pos[1]].set_title(title)
                axes[pos[0]][pos[1]].set_xlabel('Puntuación')
                
            plt.tight_layout()
            plt.savefig(f"{output_dir}/topic_distribution_by_method.png", dpi=300)
            plt.close()

            # 3. Red de relaciones entre temas
            plt.figure(figsize=(15, 15))
            G = topic_relationships['graph']
            if len(G.nodes()) > 0:
                pos = nx.spring_layout(G, k=1, iterations=50)
                
                nx.draw_networkx_nodes(G, pos, 
                                    node_color='lightblue',
                                    node_size=2000)
                
                nx.draw_networkx_labels(G, pos, font_size=10)
                
                nx.draw_networkx_edges(G, pos,
                                    width=[G[u][v]['weight'] * 2 for (u, v) in G.edges()],
                                    alpha=0.5)
            else:
                plt.text(0.5, 0.5, 'No hay relaciones significativas entre temas',
                        horizontalalignment='center',
                        verticalalignment='center')
            
            plt.title('Red de Relaciones entre Temas de Interés Ciudadano')
            plt.axis('off')
            plt.savefig(f"{output_dir}/topic_network.png", dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info("Visualizaciones generadas correctamente")
            
        except Exception as e:
            logger.error(f"Error generando visualizaciones: {str(e)}")
            raise

    def generate_research_report(self,
                               basic_stats: Dict,
                               topic_analysis: Dict,
                               topic_relationships: Dict,
                               citizen_metrics: Dict,
                               output_dir: str):
        """Genera un reporte académico en formato markdown."""
        report = f"""# Análisis de Intereses Ciudadanos en Diálogos Políticos Asistidos por IA

            ## Resumen
            Este estudio analiza {basic_stats['total_interactions']} interacciones ciudadanas con un sistema de diálogo 
            político asistido por IA, enfocándose en la identificación y comprensión de los principales temas de 
            interés ciudadano y la evaluación de diferentes métodos de análisis.

            ## 1. Metodología

            ### 1.1 Métodos de Análisis Implementados
            1. **Análisis por Embeddings**
            - Modelo: text-embedding-3-small (OpenAI)
            - Ventajas: Captura relaciones semánticas profundas
            - Limitaciones: Dependencia del contexto del entrenamiento

            2. **Análisis por LLM**
            - Modelo: GPT-4
            - Ventajas: Comprensión contextual rica
            - Limitaciones: Costo computacional, variabilidad en respuestas

            3. **Análisis Lingüístico**
            - Framework: spaCy (es_core_news_md)
            - Ventajas: Rapidez, consistencia
            - Limitaciones: Menor capacidad de abstracción

            ### 1.2 Métricas de Evaluación
            - Índice de diversidad de intereses: {citizen_metrics['interest_diversity']:.3f}
            - Correlación entre métodos:
            {self._format_method_correlations(citizen_metrics['method_correlations'])}

            ## 2. Resultados

            ### 2.1 Temas Principales de Interés Ciudadano
            {self._format_dominant_topics(citizen_metrics['dominant_topics'])}

            ### 2.2 Análisis Comparativo de Métodos
            - Correlación media entre métodos: {np.mean(list(citizen_metrics['method_correlations'].values())):.3f}
            - Los métodos muestran {self._evaluate_method_agreement(citizen_metrics['method_correlations'])}

            ### 2.3 Interrelación de Temas
            {self._format_topic_relationships(topic_relationships)}

            ## 3. Discusión

            ### 3.1 Hallazgos Principales
            - **Patrones de Interés**: Los temas dominantes reflejan las preocupaciones actuales de la ciudadanía
            - **Eficacia de Métodos**: Cada método aporta perspectivas complementarias
            - **Interconexiones**: Se observan clusters temáticos significativos

            ### 3.2 Implicaciones
            - Para el diseño de políticas públicas
            - Para la comunicación política
            - Para el desarrollo de sistemas de diálogo

            ### 3.3 Limitaciones
            - Sesgos potenciales en la muestra
            - Limitaciones técnicas de los métodos
            - Consideraciones éticas

            ## 4. Conclusiones
            Este análisis proporciona una comprensión profunda de los intereses ciudadanos en el diálogo político,
            revelando patrones significativos en las preocupaciones de la ciudadanía y demostrando la
            complementariedad de diferentes enfoques analíticos.

            ## 5. Referencias Metodológicas
            1. OpenAI. (2024). text-embedding-3-small: Sistema de embeddings de nueva generación
            2. spaCy. (2024). Industrial-Strength Natural Language Processing
            3. Newman, M. E. J. (2010). Networks: An Introduction
        """
        with open(f"{output_dir}/research_report.md", "w", encoding='utf-8') as f:
            f.write(report)
        
        return report

    def _format_method_correlations(self, correlations: Dict) -> str:
        """Formatea las correlaciones entre métodos."""
        return "\n".join([
            f"  - {k.replace('_', ' ').title()}: {v:.3f}"
            for k, v in correlations.items()
        ])

    def _format_dominant_topics(self, topics: pd.Series) -> str:
        """Formatea los temas dominantes."""
        return "\n".join([
            f"1. **{topic}**: {score:.3f}"
            for topic, score in topics.items()
        ])

    def _evaluate_method_agreement(self, correlations: Dict) -> str:
        """Evalúa el nivel de acuerdo entre métodos."""
        mean_corr = np.mean(list(correlations.values()))
        if mean_corr > 0.8:
            return "un alto nivel de concordancia"
        elif mean_corr > 0.6:
            return "un nivel moderado de concordancia"
        else:
            return "diferencias significativas en sus evaluaciones"

    def _format_topic_relationships(self, relationships: Dict) -> str:
        """Formatea las relaciones entre temas."""
        centrality = relationships['centrality_measures']['eigenvector']
        top_topics = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return "\n".join([
            f"- **{topic}**: Centralidad {score:.3f}"
            for topic, score in top_topics
        ])

    async def generate_complete_report(self, start_date: Optional[datetime] = None,
                                    end_date: Optional[datetime] = None,
                                    output_dir: str = "analysis_results"):
        try:
            # Asegúrate de que el directorio existe
            os.makedirs(output_dir, exist_ok=True)
            
            # Realizar análisis
            basic_stats = self.get_basic_statistics()
            topic_analysis = await self.analytics_service.get_topic_distribution(start_date, end_date)
            topic_relationships = self.analyze_topic_relationships(topic_analysis)
            citizen_metrics = self.calculate_citizen_interest_metrics(topic_analysis)
            
            # Generar visualizaciones
            self.generate_analysis_visualizations(
                topic_analysis,
                topic_relationships,
                output_dir
            )
            
            # Prepara la información de imágenes
            images = [
                {
                    'path': os.path.join(output_dir, 'method_comparison.png'),
                    'description': 'Comparación de Métodos de Análisis'
                },
                {
                    'path': os.path.join(output_dir, 'topic_distribution_by_method.png'),
                    'description': 'Distribución de Temas por Método'
                },
                {
                    'path': os.path.join(output_dir, 'topic_network.png'),
                    'description': 'Red de Relaciones entre Temas'
                }
            ]
            
            # Generar contenido markdown y asegurarte de que no es None
            markdown_content = self.generate_research_report(
                basic_stats,
                topic_analysis,
                topic_relationships,
                citizen_metrics,
                output_dir
            )
            
            if markdown_content is None:
                raise ValueError("El contenido markdown no puede ser None")
            
            # Generar reportes en diferentes formatos
            report_generator = ReportGenerator(output_dir)
            report_generator.generate_html_report(markdown_content, images)
            report_generator.generate_latex_report(markdown_content, images)
            
            # Crear paquete de reporte
            report_generator.create_report_package()
            
            logger.info("Reportes generados exitosamente")
            
        except Exception as e:
            logger.error(f"Error generando reportes: {str(e)}")
            raise

async def main():
    try:
        # Cargar variables de entorno
        load_environment()
        
        # Crear analizador
        analyzer = CitizenInterestAnalyzer()
        
        # Definir período de análisis
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Generar reporte completo
        logger.info(f"Iniciando análisis desde {start_date} hasta {end_date}")
        await analyzer.generate_complete_report(
            start_date=start_date,
            end_date=end_date,
            output_dir="analysis_results"
        )
        logger.info("Análisis completado. Los resultados están disponibles en el directorio 'analysis_results'")
        
    except Exception as e:
        logger.error(f"Error en la ejecución principal: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())