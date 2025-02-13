# Análisis de Interacciones - Political Discourse Analyzer
Fecha de generación: 2025-02-12 23:55:34

## 1. Estadísticas Básicas
- Total de conversaciones: 30
- Total de interacciones: 48
- Promedio de interacciones por conversación: 1.60

### Distribución por Modo
- neutral: 30 (100.0%)

## 2. Análisis de Temas
### Resumen del Período
- Total de interacciones analizadas: 48
- Período de análisis: 2025-01-13T23:50:02.380298 a 2025-02-12T23:50:02.380298

### Resultados por Método de Análisis

#### Análisis por Embeddings
| Tema | Puntuación |
|------|------------|
| economía | 0.298 |
| vivienda | 0.292 |
| derechos_sociales | 0.255 |
| medio_ambiente | 0.237 |
| seguridad | 0.226 |
| educación | 0.216 |
| sanidad | 0.210 |


#### Análisis por LLM
| Tema | Puntuación |
|------|------------|
| economía | 31.646 |
| vivienda | 19.354 |
| derechos_sociales | 11.562 |
| educación | 11.438 |
| seguridad | 8.333 |
| medio_ambiente | 6.125 |
| sanidad | 5.292 |


#### Análisis Lingüístico
| Tema | Puntuación |
|------|------------|
| derechos_sociales | 0.155 |
| economía | 0.143 |
| medio_ambiente | 0.139 |
| sanidad | 0.137 |
| seguridad | 0.136 |
| vivienda | 0.101 |
| educación | 0.099 |


#### Análisis Combinado
| Tema | Puntuación |
|------|------------|
| economía | 10.696 |
| vivienda | 6.583 |
| derechos_sociales | 3.991 |
| educación | 3.917 |
| seguridad | 2.898 |
| medio_ambiente | 2.167 |
| sanidad | 1.880 |

### Análisis Comparativo de Métodos
#### Correlación entre Métodos

| Método | Embeddings | LLM | Lingüístico | Combinado |
|--------|----------|----------|----------|----------|
| Embeddings | 1.00 | 0.87 | 0.01 | 0.87 |
| LLM | 0.87 | 1.00 | -0.06 | 1.00 |
| Lingüístico | 0.01 | -0.06 | 1.00 | -0.06 |
| Combinado | 0.87 | 1.00 | -0.06 | 1.00 |

## 3. Métricas de Engagement
- Promedio de interacciones por conversación: 1.60
- Duración promedio de conversación: 1.1 minutos
- Tasa de seguimiento: 30.0%
- Total de conversaciones de seguimiento: 9

## 4. Metodología
### Embeddings (OpenAI)
- Modelo: text-embedding-3-small
- Método: Similitud coseno entre consultas y categorías predefinidas
- Ventajas: Captura relaciones semánticas complejas
- Limitaciones: Dependiente de la calidad de las categorías predefinidas

### LLM (GPT-4)
- Modelo: GPT-4
- Método: Análisis contextual y categorización experta
- Ventajas: Comprensión profunda del contexto y matices
- Limitaciones: Mayor costo computacional y tiempo de respuesta

### Análisis Lingüístico (spaCy)
- Modelo: es_core_news_md
- Método: Análisis de entidades, dependencias y similitud léxica
- Ventajas: Rápido y eficiente, buen análisis estructural
- Limitaciones: Menor capacidad para captar contexto semántico

## 5. Visualizaciones
Se han generado las siguientes visualizaciones:
- `embedding_analysis.png`: Resultados del análisis por embeddings
- `llm_analysis.png`: Resultados del análisis por LLM
- `linguistic_analysis.png`: Resultados del análisis lingüístico
- `combined_analysis.png`: Resultados del análisis combinado
- `method_comparison.png`: Comparación entre métodos

## 6. Archivos de Datos
Los datos completos están disponibles en:
- `basic_stats.csv`: Estadísticas básicas
- `topic_analysis_*.csv`: Resultados detallados por método
- `engagement_metrics.csv`: Métricas de engagement
