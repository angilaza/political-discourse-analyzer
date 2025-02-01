from political_discourse_analyzer.utils.document_checker import DocumentChecker
from pathlib import Path

def test_document_checker():
    """Probar el verificador de documentos."""
    checker = DocumentChecker(Path("data/programs"))
    results = checker.check_documents()
    
    assert isinstance(results, dict)
    assert "total_documents" in results
    assert "total_pages" in results
    assert "documents" in results
    assert len(results["documents"]) == results["total_documents"]
    
    for doc in results["documents"]:
        assert "name" in doc
        assert "pages" in doc
        assert "size_mb" in doc
        assert doc["name"].endswith(".pdf")