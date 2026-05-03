from pathlib import Path
from agents import ResearchState
from core.llm import get_llm, ModelTier
from core.progress import emit


def _build_fallback_report(topic: str, ts: str, hits: list) -> str:
    """Minimal template-conformant report when the LLM produces empty output.

    Uses real hit data so ## Fonti is non-empty and the E2E URL assertion holds.
    """
    if hits:
        sources_lines = []
        for i, hit in enumerate(hits, start=1):
            title = hit.get("title", "Senza titolo")
            url = hit.get("url", "")
            sources_lines.append(f"{i}. [{title}]({url})")
        sources_block = "\n".join(sources_lines)
    else:
        sources_block = "(Nessuna fonte disponibile)"

    return (
        f"# Report: {topic}\n"
        f"_Generato:_ {ts}\n\n"
        f"## Sintesi\n"
        f"Generazione del report fallita: il modello non ha prodotto output. "
        f"Di seguito l'elenco delle fonti recuperate dalla ricerca.\n\n"
        f"## Notizie / Findings\n"
        f"### Risultati grezzi\n"
        f"Vedere la sezione ## Fonti per i risultati raccolti dalla ricerca web.\n\n"
        f"## Discrepanze tra fonti\n"
        f"Nessuna discrepanza rilevante.\n\n"
        f"## Fonti\n"
        f"{sources_block}\n"
    )


def writer_report(state: ResearchState) -> ResearchState:
    emit("WriterReport", "INFO", "Starting…")
    
    prompt_path = Path(__file__).parent.parent / "prompts" / "writer_report.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")
    
    llm = get_llm(ModelTier.HEAVY)
    topic = state.get("topic", "")
    synthesis = state.get("synthesis", {})
    hits = state.get("hits", [])
    critic_feedback = state.get("critic_feedback", "")
    
    import datetime
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    synthesis_context = f"Sintesi:\n{synthesis}\n\n"
    hits_context = "Risultati completi:\n"
    for i, hit in enumerate(hits):
        hits_context += f"[{i+1}] {hit['title']} (URL: {hit['url']}): {hit['fulltext'][:500]}\n"
        
    prefix = (
        f"# Report: {topic}\n"
        f"_Generato:_ {ts}\n\n"
        f"## Sintesi\n"
    )
    
    full_prompt = (
        f"{system_prompt}\n\n"
        f"Topic: {topic}\n\n"
        f"{synthesis_context}{hits_context}\n"
        f"Feedback: {critic_feedback}\n\n"
        f"ISTRUZIONE FINALE: Continua ESATTAMENTE dal punto in cui "
        f"il documento si interrompe qui sotto. NON ripetere le righe "
        f"già fornite. NON aggiungere preamboli. Produci il resto del "
        f"documento Markdown rispettando il template (## Sintesi, "
        f"## Notizie / Findings con sotto-heading ### per ogni tema, "
        f"## Discrepanze tra fonti, ## Fonti).\n\n"
        f"{prefix}"
    )
    
    try:
        emit("WriterReport", "INFO", "Invoking LLM for final report")
        continuation = llm.invoke(full_prompt).strip()

        if not continuation:
            emit("WriterReport", "WARNING", "Empty model output, building minimal fallback report from hits")
            state["draft"] = _build_fallback_report(topic, ts, hits)
        elif continuation.startswith("# Report:"):
            # Model echoed the prefix; accept as-is
            state["draft"] = continuation
        else:
            state["draft"] = prefix + continuation
            
        import re
        draft = state["draft"]
        sanitized = re.sub(
            r"^(##\s+(Sintesi|Notizie / Findings|Discrepanze tra fonti|Fonti))\s*\n\s*(?:\2)\s*(?:\n|$)",
            r"\1\n",
            draft,
            flags=re.MULTILINE
        )
        if sanitized != draft:
            emit("WriterReport", "WARNING", "Sanitized duplicated heading/content words.")
            state["draft"] = sanitized

    except Exception as e:
        emit("WriterReport", "ERROR", f"LLM call failed: {e}")
        state["draft"] = _build_fallback_report(topic, ts, hits)
        
    emit("WriterReport", "INFO", "Done.")
    return state
