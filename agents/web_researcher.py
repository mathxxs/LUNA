from pathlib import Path
from agents import NotesState
from core.llm import get_llm, ModelTier
from core.websearch import search_and_fetch
from core.progress import emit

def web_researcher(state: NotesState) -> NotesState:
    emit("WebResearcher", "INFO", "Starting…")
    
    if not state.get("web_augment", False):
        emit("WebResearcher", "INFO", "skipped: web_augment off")
        state["web_findings"] = []
        emit("WebResearcher", "INFO", "Done.")
        return state
        
    gaps = state.get("gaps", [])
    if not gaps:
        emit("WebResearcher", "INFO", "skipped: no gaps")
        state["web_findings"] = []
        emit("WebResearcher", "INFO", "Done.")
        return state
        
    prompt_path = Path(__file__).parent.parent / "prompts" / "web_researcher.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")
    llm = get_llm(ModelTier.HEAVY)
    
    findings = []
    
    for i, gap in enumerate(gaps):
        emit("WebResearcher", "INFO", f"Researching gap {i+1}/{len(gaps)}: {gap.get('missing', '')}")
        
        # Ask LLM for a query
        query_prompt = f"Lacuna:\n{gap}\n\nFornisci SOLO la stringa di ricerca più appropriata (max 6 parole)."
        try:
            query = llm.invoke(query_prompt).strip()
            
            # Fetch from web
            hits = search_and_fetch(query, k=3)
            if not hits:
                continue
                
            # Ask LLM to pick and summarize
            hits_context = ""
            for idx, hit in enumerate(hits):
                hits_context += f"Fonte [{idx}]: {hit['url']}\nContenuto: {hit['snippet'][:500]}\n\n"
                
            summary_prompt = f"{system_prompt}\n\nLacuna da colmare:\n{gap}\n\nRisultati trovati:\n{hits_context}\nScegli la fonte migliore e produci il riassunto specificando l'URL scelto alla fine."
            
            summary_result = llm.invoke(summary_prompt).strip()
            
            # Extract URL if possible, otherwise use the first one
            chosen_url = hits[0]["url"]
            for hit in hits:
                if hit["url"] in summary_result:
                    chosen_url = hit["url"]
                    break
                    
            findings.append({
                "gap_ref": i,
                "summary": summary_result,
                "source": chosen_url
            })
            
        except Exception as e:
            emit("WebResearcher", "WARNING", f"Failed to process gap {i}: {e}")
            
    state["web_findings"] = findings
    emit("WebResearcher", "INFO", "Done.")
    return state
