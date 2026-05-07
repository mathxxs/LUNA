from pathlib import Path
from agents import NotesState
from core.llm import get_llm, ModelTier
from core.progress import emit

# Soglia di parole oltre la quale qwen3.5:4b (MEDIUM tier) non riesce a
# riformattare fedelmente: tende a riassumere/parafrasare invece di
# preservare il testo. Sopra questa soglia, salta l'LLM e lascia passare
# il testo linted intatto (perde l'auto-heading ma garantisce fedeltà).
WORD_LIMIT_FOR_STRUCTURER = 800

# Se l'output del modello è drammaticamente più corto dell'input, è quasi
# sicuro che ha riassunto invece di formattare. Soglia di sicurezza.
SHRINKAGE_RATIO_THRESHOLD = 0.5


def structurer(state: NotesState) -> NotesState:
    emit("Structurer", "INFO", "Starting…")

    linted = state.get("linted", "")
    word_count = len(linted.split())

    # Length-based bypass.
    if word_count > WORD_LIMIT_FOR_STRUCTURER:
        emit(
            "Structurer", "INFO",
            f"Input too long ({word_count} words > {WORD_LIMIT_FOR_STRUCTURER}), "
            f"skipping LLM to preserve fidelity."
        )
        state["structured"] = linted
        emit("Structurer", "INFO", "Done.")
        return state

    prompt_path = Path(__file__).parent.parent / "prompts" / "structurer.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")

    llm = get_llm(ModelTier.MEDIUM)
    full_prompt = f"{system_prompt}\n\nAppunti corretti:\n{linted}"

    try:
        emit("Structurer", "INFO", "Invoking LLM for structuring")
        result = llm.invoke(full_prompt).strip()
        if not result:
            emit("Structurer", "WARNING", "Empty model output, falling back to un-structured linted notes")
            state["structured"] = linted
        elif word_count > 0 and len(result.split()) < SHRINKAGE_RATIO_THRESHOLD * word_count:
            # Length-sanity check: il modello ha riassunto invece di formattare.
            emit(
                "Structurer", "WARNING",
                f"Output too short ({len(result.split())} words vs {word_count} input), "
                f"suspected summary collapse — falling back to linted notes."
            )
            state["structured"] = linted
        else:
            state["structured"] = result
    except Exception as e:
        emit("Structurer", "ERROR", f"LLM call failed: {e}")
        state["structured"] = linted

    emit("Structurer", "INFO", "Done.")
    return state
