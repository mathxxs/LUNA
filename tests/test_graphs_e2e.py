import pytest
import re
from pathlib import Path
from graphs.notes_graph import notes_graph
from graphs.research_graph import research_graph

pytestmark = pytest.mark.slow

def test_notes_graph_e2e():
    fixture_notes = "Gli appunti di oggi trattano in maniera molto dettagliata e complessa del concetto di overfitting sul training set. Il professore ha inoltre spiegato ampiamente tutti i passi necessari su come fare il deploy dei modelli in produzione, assicurandosi di mantenere sempre una solida architettura del framework."
    state = {
        "raw_notes": fixture_notes,
        "title": "test_appunti",
        "web_augment": False
    }
    
    out = notes_graph.invoke(state)
    
    assert len(out["final_notes"]) >= len(out["raw_notes"])
    assert "training set" in out["final_notes"] or "deploy" in out["final_notes"]
    
    out_path = Path(out["output_path"])
    assert out_path.exists()
    assert out_path.suffix == ".md"

def test_research_graph_e2e():
    state = {
        "topic": "machine learning"
    }
    
    out = research_graph.invoke(state)
    
    final_report = out.get("final_report", "")
    assert "## Fonti" in final_report
    assert re.search(r"## Fonti.*?https?://\S+", final_report, re.DOTALL)
    
    out_path = Path(out["output_path"])
    assert out_path.exists()
    assert out_path.suffix == ".md"
