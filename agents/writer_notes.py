from pathlib import Path
from agents import NotesState
from core.llm import get_llm, ModelTier
from core.progress import emit


def _build_deterministic_draft(structured: str, gaps: list) -> str:
    """Compose the final draft without invoking the LLM.

    The structurer's output is already a headed Markdown document; we
    just append non-resolved-gap callouts at the end so the user sees
    what looked thin. Used when there is no web finding to integrate
    and no critic feedback to address — i.e. when the LLM would have
    nothing meaningful to add but tends to hallucinate or erase
    content under those conditions.
    """
    parts = [structured.rstrip()]
    if gaps:
        parts.append("")  # blank line before callouts
        for gap in gaps:
            location = (gap.get("location") or "").strip()
            missing = (gap.get("missing") or "").strip()
            hint = (gap.get("hint") or "").strip()
            line = f"> **Lacuna non risolta:** {missing}"
            if location:
                line += f" (sezione: {location})"
            if hint:
                line += f" Suggerimento: {hint}"
            if not line.endswith("."):
                line += "."
            parts.append(line)
    return "\n".join(parts)


def writer_notes(state: NotesState) -> NotesState:
    emit("WriterNotes", "INFO", "Starting…")

    structured = state.get("structured", "")
    gaps = state.get("gaps", [])
    web_findings = state.get("web_findings", [])
    critic_feedback = state.get("critic_feedback", "")
    title = state.get("title", "appunti")

    # Fast path: no web integration to do, no critic feedback to
    # address. The LLM has no meaningful task here — qwen3.5:9b under
    # such conditions tends to (a) erase the user's body and replace
    # it with chat-mode summaries, (b) fabricate web callouts despite
    # web_findings being empty. Bypass it entirely.
    if not web_findings and not critic_feedback.strip():
        emit("WriterNotes", "INFO", "Deterministic build (no web findings, no critic feedback)")
        state["draft"] = _build_deterministic_draft(structured, gaps)
        emit("WriterNotes", "INFO", "Done.")
        return state

    # LLM path: web integration to perform OR critic revise loop.
    prompt_path = Path(__file__).parent.parent / "prompts" / "writer_notes.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")
    llm = get_llm(ModelTier.HEAVY)

    blocks = [f"Appunti strutturati:\n{structured}"]

    if gaps:
        gaps_context = "Lacune identificate:\n"
        for i, gap in enumerate(gaps):
            gaps_context += (
                f"Lacuna [{i}] (sezione: {gap.get('location', '')}): "
                f"{gap.get('missing', '')} — suggerimento: {gap.get('hint', '')}\n"
            )
        blocks.append(gaps_context.rstrip())

    if web_findings:
        findings_context = "Trovati web da integrare:\n"
        for finding in web_findings:
            findings_context += (
                f"> **Integrazione (web):** {finding['summary']} "
                f"[Fonte: {finding['source']}]\n"
            )
        blocks.append(findings_context.rstrip())

    if critic_feedback.strip():
        blocks.append(f"Feedback del revisore:\n{critic_feedback}")

    context_body = "\n\n".join(blocks)

    prefix = f"# Appunti: {title}\n\n"

    full_prompt = (
        f"{system_prompt}\n\n"
        f"{context_body}\n\n"
        f"ISTRUZIONE FINALE: Continua ESATTAMENTE dal punto in cui "
        f"il documento si interrompe qui sotto. NON ripetere le righe "
        f"già fornite. NON aggiungere preamboli, domande all'utente, "
        f"offerte di aiuto o saluti finali. Produci SOLO il contenuto "
        f"Markdown degli appunti ripuliti, rispettando le regole sopra "
        f"(no fence ```markdown, no callout web inventati, fedeltà "
        f"all'input).\n\n"
        f"{prefix}"
    )

    try:
        emit("WriterNotes", "INFO", "Invoking LLM for final notes draft")
        continuation = llm.invoke(full_prompt).strip()

        if not continuation:
            emit("WriterNotes", "WARNING", "Empty model output, falling back to deterministic draft")
            state["draft"] = _build_deterministic_draft(structured, gaps)
        elif continuation.startswith("# "):
            state["draft"] = continuation
        else:
            state["draft"] = prefix + continuation
    except Exception as e:
        emit("WriterNotes", "ERROR", f"LLM call failed: {e}")
        state["draft"] = _build_deterministic_draft(structured, gaps)

    emit("WriterNotes", "INFO", "Done.")
    return state
