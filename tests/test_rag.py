import pytest
from core.rag import NotesRAG

@pytest.mark.slow
def test_rag_roundtrip(tmp_path, monkeypatch):
    """Ingest then query returns at least one chunk on identical text."""
    pytest.importorskip("chromadb")
    # Optional: skip if Ollama is not reachable for the embedding model
    rag = NotesRAG()
    title = "test_rag_smoke"
    text = (
        "Il machine learning è una branca dell'intelligenza artificiale. "
        "Permette ai modelli di imparare dai dati senza essere programmati esplicitamente."
    )
    rag.ingest(text, title)
    hits = rag.query(title, "machine learning", k=3)
    assert len(hits) > 0
    assert isinstance(hits[0], dict)
    assert "snippet" in hits[0]
    rag.delete(title)
