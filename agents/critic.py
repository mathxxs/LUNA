import re
from pathlib import Path
from typing import Union
from agents import NotesState, ResearchState
from core.llm import get_llm, ModelTier
from core.progress import emit

def critic(state: Union[NotesState, ResearchState]) -> Union[NotesState, ResearchState]:
    emit("Critic", "INFO", "Starting…")
    
    prompt_path = Path(__file__).parent.parent / "prompts" / "critic.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")
    
    llm = get_llm(ModelTier.MEDIUM, reasoning=True)
    draft = state.get("draft", "")
    
    full_prompt = f"{system_prompt}\n\nDocumento da revisionare:\n{draft}"
    
    try:
        emit("Critic", "INFO", "Invoking LLM for critique")
        result = llm.invoke(full_prompt).strip()
        
        state["critic_feedback"] = result
        
        # Parse verdict
        match = re.search(r'(APPROVE|REVISE)', result, re.IGNORECASE)
        if match:
            state["critic_verdict"] = match.group(1).upper()
        else:
            emit("Critic", "WARNING", "No explicit APPROVE or REVISE found in output, defaulting to APPROVE")
            state["critic_verdict"] = "APPROVE"
            
    except Exception as e:
        emit("Critic", "WARNING", f"LLM call failed: {e}. Defaulting to APPROVE.")
        state["critic_feedback"] = f"Errore critico: {e}"
        state["critic_verdict"] = "APPROVE"
        
    emit("Critic", "INFO", "Done.")
    return state
