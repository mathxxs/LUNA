from pathlib import Path
from agents import NotesState
from core.llm import get_llm, ModelTier
from core.progress import emit

def structurer(state: NotesState) -> NotesState:
    emit("Structurer", "INFO", "Starting…")
    
    prompt_path = Path(__file__).parent.parent / "prompts" / "structurer.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")
    
    llm = get_llm(ModelTier.MEDIUM)
    linted = state.get("linted", "")
    
    full_prompt = f"{system_prompt}\n\nAppunti corretti:\n{linted}"
    
    try:
        emit("Structurer", "INFO", "Invoking LLM for structuring")
        result = llm.invoke(full_prompt)
        result = result.strip()
        if not result:
            emit("Structurer", "WARNING", "Empty model output, falling back to un-structured linted notes")
            state["structured"] = linted
        else:
            state["structured"] = result
    except Exception as e:
        emit("Structurer", "ERROR", f"LLM call failed: {e}")
        state["structured"] = linted
        
    emit("Structurer", "INFO", "Done.")
    return state
