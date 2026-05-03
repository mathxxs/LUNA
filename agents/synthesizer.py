import json
import re
from pathlib import Path
from agents import ResearchState
from core.llm import get_llm, ModelTier
from core.progress import emit

def synthesizer(state: ResearchState) -> ResearchState:
    emit("Synthesizer", "INFO", "Starting…")
    
    prompt_path = Path(__file__).parent.parent / "prompts" / "synthesizer.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")
    
    llm = get_llm(ModelTier.HEAVY)
    hits = state.get("hits", [])
    
    hits_context = ""
    for i, hit in enumerate(hits):
        hits_context += f"Hit [{i}]: {hit['title']} - {hit['snippet']}\n"
        
    full_prompt = f"{system_prompt}\n\nRisultati:\n{hits_context}"
    
    try:
        emit("Synthesizer", "INFO", "Invoking LLM for synthesis")
        result = llm.invoke(full_prompt).strip()
        
        match = re.search(r'\{.*\}', result, re.DOTALL)
        if match:
            json_str = match.group(0)
        else:
            json_str = result
            
        parsed = json.loads(json_str)
        if not isinstance(parsed, dict) or "groups" not in parsed:
            raise ValueError("Parsed JSON missing 'groups' key")
            
        state["synthesis"] = parsed
        
    except Exception as e:
        emit("Synthesizer", "WARNING", f"JSON parsing failed: {e}")
        state["synthesis"] = {
            "groups": [{"theme": "Risultati", "items": list(range(len(hits)))}]
        }
        
    emit("Synthesizer", "INFO", "Done.")
    return state
