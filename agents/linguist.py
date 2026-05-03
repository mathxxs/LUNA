from pathlib import Path
from agents import NotesState
from core.llm import get_llm, ModelTier
from core.progress import emit

def linguist(state: NotesState) -> NotesState:
    emit("Linguist", "INFO", "Starting…")
    
    prompt_path = Path(__file__).parent.parent / "prompts" / "linguist.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")
    
    llm = get_llm(ModelTier.LIGHT)
    raw_notes = state.get("raw_notes", "")
    
    full_prompt = f"{system_prompt}\n\nAppunti originali:\n{raw_notes}"
    
    try:
        emit("Linguist", "INFO", "Invoking LLM for grammar correction")
        result = llm.invoke(full_prompt)
        result = result.strip()
        if not result:
            emit("Linguist", "ERROR", "Empty model output, passing through raw_notes")
            state["linted"] = raw_notes
        else:
            state["linted"] = result
    except Exception as e:
        emit("Linguist", "ERROR", f"LLM call failed: {e}")
        state["linted"] = raw_notes
        
    emit("Linguist", "INFO", "Done.")
    return state
