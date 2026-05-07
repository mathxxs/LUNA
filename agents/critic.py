import re
from pathlib import Path
from typing import Union
from agents import NotesState, ResearchState
from core.llm import get_llm, ModelTier
from core.progress import emit

# Soglia oltre la quale il thinking mode di qwen3.5 esplode in tempo:
# su draft brevi (test, fixture) il reasoning è severo e completa in
# ~30-90s; su draft lunghi (PDF reali post web augmentation) può
# bloccarsi per decine di minuti su hardware modesto. Soglia adattiva.
WORD_THRESHOLD_FOR_REASONING = 1500


def critic(state: Union[NotesState, ResearchState]) -> Union[NotesState, ResearchState]:
    emit("Critic", "INFO", "Starting…")

    prompt_path = Path(__file__).parent.parent / "prompts" / "critic.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")

    draft = state.get("draft", "")
    word_count = len(draft.split())
    use_reasoning = word_count < WORD_THRESHOLD_FOR_REASONING
    emit(
        "Critic", "INFO",
        f"Reasoning {'ON' if use_reasoning else 'OFF'} (draft: {word_count} words)."
    )
    llm = get_llm(ModelTier.MEDIUM, reasoning=use_reasoning)

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
