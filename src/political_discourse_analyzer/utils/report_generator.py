# src/political_discourse_analyzer/utils/report_generator.py

import os
import markdown
import jinja2
from datetime import datetime
from typing import Dict
import shutil

class ReportGenerator:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.ensure_template_directory()

    def ensure_template_directory(self):
        """Asegura que exista el directorio de templates y crea los necesarios."""
        os.makedirs(self.template_dir, exist_ok=True)
        
        # HTML template
        html_template = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <style>
        .chart-container {
            margin: 2rem 0;
            text-align: center;
        }
        .chart-container img {
            max-width: 100%;
            height: auto;
            margin: 0 auto;
        }
    </style>
</head>
<body class="bg-gray-100">
    <div class="container mx-auto px-4 py-8 max-w-4xl">
        <div class="bg-white shadow-lg rounded-lg p-8">
            {{ content | safe }}
            
            <div class="mt-8">
                <h2 class="text-2xl font-bold mb-4">Visualizaciones</h2>
                {% for image in images %}
                <div class="chart-container">
                    <img src="{{ image.path }}" alt="{{ image.description }}">
                    <p class="text-gray-600 mt-2">{{ image.description }}</p>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</body>
</html>
"""
        with open(os.path.join(self.template_dir, 'report_template.html'), 'w') as f:
            f.write(html_template)

        # LaTeX template
        latex_template = r"""
\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[spanish]{babel}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{float}
\usepackage{booktabs}
\usepackage{amsmath}
\usepackage{geometry}

\geometry{margin=2.5cm}

\title{{{ title }}}
\author{Análisis de Resultados - Political Discourse Analyzer}
\date{{\today}}

\begin{document}

\maketitle

{{ content }}

\section{Visualizaciones}
{% for image in images %}
\begin{figure}[H]
    \centering
    \includegraphics[width=0.8\textwidth]{ {{image.path}} }
    \caption{ {{image.description}} }
    \label{fig:{{image.label}}}
\end{figure}
{% endfor %}

\end{document}
"""
        with open(os.path.join(self.template_dir, 'report_template.tex'), 'w') as f:
            f.write(latex_template)

    def generate_html_report(self, markdown_content: str, images: list):
        """Genera un reporte HTML con las visualizaciones integradas."""
        # Convertir markdown a HTML
        html_content = markdown.markdown(markdown_content)
        
        # Preparar imágenes
        image_data = []
        for img in images:
            image_data.append({
                'path': os.path.relpath(img['path'], self.output_dir),
                'description': img['description']
            })
        
        # Cargar y renderizar template
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dir)
        )
        template = env.get_template('report_template.html')
        
        rendered_html = template.render(
            title="Análisis de Interacciones Ciudadanas",
            content=html_content,
            images=image_data
        )
        
        # Guardar HTML
        with open(os.path.join(self.output_dir, 'analysis_report.html'), 'w', encoding='utf-8') as f:
            f.write(rendered_html)

    def generate_latex_report(self, markdown_content: str, images: list):
        """Genera un reporte LaTeX con las visualizaciones integradas."""
        # Convertir markdown a LaTeX
        latex_content = self._markdown_to_latex(markdown_content)
        
        # Preparar imágenes
        image_data = []
        for img in images:
            image_data.append({
                'path': os.path.relpath(img['path'], self.output_dir),
                'description': img['description'],
                'label': os.path.splitext(os.path.basename(img['path']))[0]
            })
        
        # Cargar y renderizar template
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dir)
        )
        template = env.get_template('report_template.tex')
        
        rendered_latex = template.render(
            title="Análisis de Interacciones Ciudadanas",
            content=latex_content,
            images=image_data
        )
        
        # Guardar LaTeX
        with open(os.path.join(self.output_dir, 'analysis_report.tex'), 'w', encoding='utf-8') as f:
            f.write(rendered_latex)

    def _markdown_to_latex(self, markdown_text: str) -> str:
        """Convierte markdown a LaTeX (versión simplificada)."""
        # Esta es una versión básica, podrías usar panflute o pandoc para una conversión más robusta
        conversions = [
            (r'# (.*)', r'\\section{\1}'),
            (r'## (.*)', r'\\subsection{\1}'),
            (r'### (.*)', r'\\subsubsection{\1}'),
            (r'\*\*(.*?)\*\*', r'\\textbf{\1}'),
            (r'\*(.*?)\*', r'\\textit{\1}'),
        ]
        
        text = markdown_text
        for pattern, replacement in conversions:
            text = re.sub(pattern, replacement, text)
        
        return text

    def create_report_package(self):
        """Crea un paquete ZIP con todos los archivos del reporte."""
        report_dir = os.path.join(self.output_dir, 'report_package')
        os.makedirs(report_dir, exist_ok=True)
        
        # Copiar archivos al paquete
        for ext in ['html', 'tex', 'md']:
            src = os.path.join(self.output_dir, f'analysis_report.{ext}')
            if os.path.exists(src):
                shutil.copy2(src, report_dir)
        
        # Copiar imágenes
        images_dir = os.path.join(report_dir, 'images')
        os.makedirs(images_dir, exist_ok=True)
        for img in os.listdir(self.output_dir):
            if img.endswith(('.png', '.jpg', '.svg')):
                shutil.copy2(
                    os.path.join(self.output_dir, img),
                    images_dir
                )
        
        # Crear ZIP
        shutil.make_archive(
            os.path.join(self.output_dir, 'analysis_report'),
            'zip',
            report_dir
        )