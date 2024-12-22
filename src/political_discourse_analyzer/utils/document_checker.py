import os
from pathlib import Path
import PyPDF2
from typing import Dict, List

class DocumentChecker:
    def __init__(self, documents_path: Path):
        self.documents_path = documents_path

    def check_documents(self) -> Dict:
        """
        Verifica los documentos en el directorio y devuelve información sobre ellos.
        """
        results = {
            "total_documents": 0,
            "total_pages": 0,
            "documents": [],
            "errors": []
        }

        # Asegurarse de que el directorio existe
        if not self.documents_path.exists():
            print(f"El directorio {self.documents_path} no existe")
            return results

        print(f"Buscando documentos en: {self.documents_path}")
        
        for file_path in self.documents_path.glob("*.pdf"):
            try:
                with open(file_path, 'rb') as file:
                    pdf = PyPDF2.PdfReader(file)
                    num_pages = len(pdf.pages)
                    
                    results["documents"].append({
                        "name": file_path.name,
                        "pages": num_pages,
                        "size_mb": round(os.path.getsize(file_path) / (1024 * 1024), 2)
                    })
                    
                    results["total_documents"] += 1
                    results["total_pages"] += num_pages
                    
            except Exception as e:
                results["errors"].append({
                    "file": file_path.name,
                    "error": str(e)
                })

        return results

async def print_documents_info():
    """
    Imprime información sobre los documentos en un formato legible.
    """
    # Obtener la ruta absoluta del proyecto (political-discourse-analyzer)
    project_root = Path(__file__).parent.parent.parent.parent
    documents_path = project_root / "data" / "programs"
    
    print(f"Directorio del proyecto: {project_root}")
    print(f"Buscando documentos en: {documents_path}")
    
    checker = DocumentChecker(documents_path)
    results = checker.check_documents()
    
    print("\n=== Resumen de Documentos ===")
    print(f"Total de documentos: {results['total_documents']}")
    print(f"Total de páginas: {results['total_pages']}")
    print("\n=== Documentos Individuales ===")
    
    for doc in results["documents"]:
        print(f"\nNombre: {doc['name']}")
        print(f"Páginas: {doc['pages']}")
        print(f"Tamaño: {doc['size_mb']} MB")
    
    if results["errors"]:
        print("\n=== Errores Encontrados ===")
        for error in results["errors"]:
            print(f"\nArchivo: {error['file']}")
            print(f"Error: {error['error']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(print_documents_info())