import json
import re
from pathlib import Path
from agents import NotesState
from core.llm import get_llm, ModelTier
from core.progress import emit

def gap_detector(state: NotesState) -> NotesState:
    emit("GapDetector", "INFO", "Starting…")
    
    prompt_path = Path(__file__).parent.parent / "prompts" / "gap_detector.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")
    
    llm = get_llm(ModelTier.MEDIUM)
    structured = state.get("structured", "")
    
    full_prompt = f"{system_prompt}\n\nAppunti strutturati:\n{structured}"
    
    try:
        emit("GapDetector", "INFO", "Invoking LLM for gap detection")
        result = llm.invoke(full_prompt)
        result = result.strip()
        
        # Try to find JSON array in output
        match = re.search(r'\[.*\]', result, re.DOTALL)
        if match:
            json_str = match.group(0)
        else:
            json_str = result
            
        parsed = json.loads(json_str)
        if not isinstance(parsed, list):
            raise ValueError("Parsed JSON is not a list")
            
        valid_gaps = []
        for item in parsed:
            if isinstance(item, dict) and "location" in item and "missing" in item and "hint" in item:
                valid_gaps.append({
                    "location": str(item["location"]),
                    "missing": str(item["missing"]),
                    "hint": str(item["hint"])
                })
                
        state["gaps"] = valid_gaps
        
    except Exception as e:
        emit("GapDetector", "WARNING", f"gap_detector: malformed JSON, treating as no gaps: {e}")
        state["gaps"] = []
        
    emit("GapDetector", "INFO", "Done.")
    return state
