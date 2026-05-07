from pathlib import Path
from agents import NotesState
from core.llm import get_llm, ModelTier
from core.progress import emit

# Soglia oltre la quale il writer LLM tende a comprimere/sintetizzare
# l'input invece di preservarlo verbatim, anche con prompt esplicito.
# Sopra questa soglia, andiamo deterministici anche quando ci sono
# web findings da integrare.
LONG_INPUT_THRESHOLD = 1000


def _build_deterministic_draft(structured: str, gaps: list, web_findings: list = None) -> str:
    """Compose the final draft without invoking the LLM.

    Output: structured verbatim + web findings as callouts + unresolved-gap
    callouts. Used when the LLM would have nothing meaningful to add (no
    findings, no critic feedback) OR when the input is too long for the
    LLM to handle reliably (it tends to compress/erase content under load).
    """
    if web_findings is None:
        web_findings = []

    parts = [structured.rstrip()]

    # Append web findings as canonical callouts.
    if web_findings:
        parts.append("")
        for finding in web_findings:
            summary = (finding.get("summary") or "").strip()
            source = (finding.get("source") or "").strip()
            line = f"> **Integrazione (web):** {summary}"
            if source:
                line += f" [Fonte: {source}]"
            parts.append(line)

    # Append unresolved-gap callouts (gaps NOT covered by any web finding).
    # If there are no web findings, all gaps count as unresolved (preserves
    # the original deterministic-path behaviour).
    covered = {f.get("gap_ref") for f in web_findings if "gap_ref" in f}
    unresolved = [g for i, g in enumerate(gaps) if i not in covered]
    if unresolved:
        if not web_findings:
            parts.append("")
        for gap in unresolved:
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

    structured_word_count = len(structured.split())
    no_critic_feedback = not critic_feedback.strip()

    # Fast path 1: nothing meaningful for the LLM to do (no web findings,
    # no critic feedback). qwen3.5:9b under such conditions tends to (a)
    # erase the user's body and replace it with chat-mode summaries,
    # (b) fabricate web callouts despite web_findings being empty.
    #
    # Fast path 2: input too long. Even with web findings the LLM
    # compresses the user's content (~50% loss observed at 2300 words).
    # Going deterministic preserves fidelity at the cost of LLM polish.
    trigger_deterministic = no_critic_feedback and (
        not web_findings or structured_word_count > LONG_INPUT_THRESHOLD
    )
    if trigger_deterministic:
        reason = (
            "no web findings, no critic feedback"
            if not web_findings
            else f"long input ({structured_word_count} words > {LONG_INPUT_THRESHOLD}), "
                 f"integrating {len(web_findings)} web findings"
        )
        emit("WriterNotes", "INFO", f"Deterministic build ({reason})")
        state["draft"] = _build_deterministic_draft(structured, gaps, web_findings)
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
            state["draft"] = _build_deterministic_draft(structured, gaps, web_findings)
        elif continuation.startswith("# "):
            state["draft"] = continuation
        else:
            state["draft"] = prefix + continuation
    except Exception as e:
        emit("WriterNotes", "ERROR", f"LLM call failed: {e}")
        state["draft"] = _build_deterministic_draft(structured, gaps, web_findings)

    emit("WriterNotes", "INFO", "Done.")
    return state
