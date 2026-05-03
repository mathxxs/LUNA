import datetime
import tempfile
import time
from pathlib import Path

import streamlit as st

from core.progress import subscribe, unsubscribe
from core.io_utils import load_file
from graphs.notes_graph import notes_graph
from graphs.research_graph import research_graph
from config import OUTPUTS_DIR, QWEN_LIGHT, QWEN_MEDIUM, QWEN_HEAVY, EMBED_MODEL

NOTES_PHASES = [
    "Linguist", "Structurer", "GapDetector",
    "WebResearcher", "WriterNotes", "Critic", "SaveOutput",
]
RESEARCH_PHASES = [
    "Planner", "Searcher", "Synthesizer",
    "WriterReport", "Critic", "SaveOutput",
]

def parse_library_title(filename: str) -> str:
    """Extract a friendly title from the generated filename."""
    name = filename
    if name.endswith(".md"):
        name = name[:-3]
    parts = name.split("_")
    # match pattern YYYY-MM-DD_HH-MM-SS_slug
    if len(parts) >= 3 and len(parts[0]) == 10 and len(parts[1]) == 8:
        name = "_".join(parts[2:])
    return name.replace("_", " ").capitalize()

def make_progress_tracker(phases: list[str], placeholder):
    completed_phases = set()
    current_phase = None
    
    def on_event(stage: str, level: str, message: str):
        nonlocal current_phase
        if stage in phases:
            if message.strip().lower() == "done.":
                completed_phases.add(stage)
                if current_phase == stage:
                    current_phase = None
            else:
                current_phase = stage
                
        lines = []
        for p in phases:
            if p in completed_phases:
                lines.append(f"- :white_check_mark: {p}")
            elif p == current_phase:
                lines.append(f"- :hourglass_flowing_sand: **{p}**")
            else:
                lines.append(f"- :white_circle: {p}")
                
        # Le fasi non usate non riceveranno eventi e manterranno :white_circle: come previsto
        placeholder.markdown("\n".join(lines))
    return on_event

st.set_page_config(page_title="LUNA", page_icon="luna_logo_icon.png", layout="wide", initial_sidebar_state="expanded")

st.image("logo_luna.png", use_container_width=True)
st.caption("**Local University Notes Assistant** — Sistema multi-agente locale per Note Enhancement e Topic Research (100% Locale, zero cloud).")
st.divider()

st.markdown(
    """
    <style>
    /* Hero banner: cap altezza, crop al centro, angoli arrotondati */
    [data-testid="stImage"] img {
        max-height: 260px;
        object-fit: cover;
        width: 100% !important;
        border-radius: 12px;
    }

    /* Bottoni primari: più grandi e leggibili */
    div.stButton > button[kind="primary"] p {
        font-size: 1.3rem !important;
        font-weight: bold !important;
    }
    div.stButton > button[kind="primary"] {
        padding: 0.8rem 2rem !important;
        height: auto !important;
    }

    /* Tab più grandi */
    button[data-baseweb="tab"] p {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
    }

    /* Tab attiva: testo magenta in linea con la palette */
    button[data-baseweb="tab"][aria-selected="true"] p {
        color: #E04AAD !important;
    }

    /* Link in giallo caldo, hover magenta */
    a, a:visited {
        color: #F0D078 !important;
    }
    a:hover {
        color: #E04AAD !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
(OUTPUTS_DIR / "notes").mkdir(parents=True, exist_ok=True)
(OUTPUTS_DIR / "research").mkdir(parents=True, exist_ok=True)

# --- SIDEBAR ---
st.sidebar.header("Stato")
st.sidebar.markdown("**Modelli attivi:**")
st.sidebar.markdown(
    f"1. `{QWEN_LIGHT}`\n"
    f"2. `{QWEN_MEDIUM}`\n"
    f"3. `{QWEN_HEAVY}`\n"
    f"4. `{EMBED_MODEL}`"
)

notes_count = len(list((OUTPUTS_DIR / "notes").glob("*.md")))
research_count = len(list((OUTPUTS_DIR / "research").glob("*.md")))
st.sidebar.metric("Output salvati", notes_count + research_count)

st.sidebar.divider()
st.sidebar.header("Guida rapida")
st.sidebar.markdown(
    "- 1. Tab **Migliora i miei appunti** — incolla testo o carica file.\n"
    "- 2. Tab **Ricerca su un argomento** — inserisci un topic.\n"
    "- 3. Tab **Libreria** — sfoglia i file generati."
)
st.sidebar.divider()
st.sidebar.caption("Progetto accademico — Laboratorio di Data Science, UNIVPM 2025/2026.")

# --- TABS ---
tab_notes, tab_research, tab_library = st.tabs([
    "📝 Migliora i miei appunti",
    "🔍 Ricerca su un argomento",
    "📚 Libreria",
])

# --- TAB 1: Migliora i miei appunti ---
with tab_notes:
    if "notes_output" not in st.session_state:
        with st.container(border=True):
            st.markdown("📝 **Come funziona**")
            st.markdown(
                "Incolla appunti italiani o carica un file. "
                "La pipeline corregge la grammatica, aggiunge heading e "
                "segnala lacune. Con il toggle web attivo, integra "
                "informazioni online citando le fonti."
            )

    st.subheader("Inserisci i tuoi appunti")
    
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        notes_text = st.text_area("Incolla il testo qui", height=300, key="notes_text")
    with col_input2:
        notes_file = st.file_uploader("Oppure carica un file (.md / .txt / .pdf)", type=["md", "txt", "pdf"], key="notes_file")
        
    notes_title = st.text_input("Titolo (opzionale)", key="notes_title")
    notes_web = st.toggle("Integra con ricerca web", value=False, key="notes_web")
    
    if st.button("Esegui pipeline", key="notes_run", type="primary"):
        resolved_text = ""
        if notes_text.strip():
            resolved_text = notes_text
        elif notes_file is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{notes_file.name.split('.')[-1]}") as tmp:
                tmp.write(notes_file.getvalue())
                tmp_path = Path(tmp.name)
            try:
                resolved_text = load_file(str(tmp_path))
            finally:
                tmp_path.unlink()
                
        if not resolved_text.strip():
            st.warning("Inserisci o carica del testo prima di eseguire.")
        else:
            resolved_title = notes_title.strip() if notes_title.strip() else "appunti"
            
            initial_state = {
                "raw_notes": resolved_text,
                "title": resolved_title,
                "web_augment": notes_web,
            }
            
            events = []
            def on_event_notes(stage, level, message):
                events.append((stage, level, message))
                status.update(label=f"[{stage}] {message}")
                
            with st.status("Esecuzione in corso…", expanded=True) as status:
                progress_placeholder = st.empty()
                tracker = make_progress_tracker(NOTES_PHASES, progress_placeholder)
                
                def combined_on_event(stage, level, message):
                    on_event_notes(stage, level, message)
                    tracker(stage, level, message)

                subscribe(combined_on_event)
                try:
                    out = notes_graph.invoke(initial_state)
                    status.update(label="Completato", state="complete")
                    st.session_state["notes_output"] = out
                except Exception as e:
                    status.update(label=f"Errore: {e}", state="error")
                finally:
                    unsubscribe(combined_on_event)
                
                for stage, level, message in events:
                    st.write(f"`[{stage}]` {message}")

    out = st.session_state.get("notes_output")
    if out:
        st.subheader("Risultato")
        col_orig, col_clean = st.columns(2)
        with col_orig:
            st.caption("Originale")
            st.markdown(out.get("raw_notes", ""))
        with col_clean:
            st.caption("Ripulito")
            st.markdown(out.get("final_notes", ""))
            
        output_path = out.get("output_path", "")
        if output_path:
            file_name = Path(output_path).name
            st.download_button(
                "Scarica .md",
                data=out.get("final_notes", ""),
                file_name=file_name,
                mime="text/markdown",
                key="dl_notes_main"
            )

# --- TAB 2: Ricerca su un argomento ---
with tab_research:
    if "research_output" not in st.session_state:
        with st.container(border=True):
            st.markdown("🔍 **Come funziona**")
            st.markdown(
                "Inserisci un argomento. La pipeline pianifica sotto-query, "
                "cerca sul web, sintetizza i risultati e produce un report "
                "Markdown con sezione Fonti."
            )

    st.subheader("Argomento da ricercare")
    research_topic = st.text_input("Argomento", key="research_topic", placeholder="es. machine learning")
    research_subq = st.slider("Numero di sotto-query", min_value=3, max_value=6, value=4, key="research_subq")
    
    if st.button("Esegui ricerca", key="research_run", type="primary"):
        if not research_topic.strip():
            st.warning("Inserisci un argomento prima di eseguire.")
        else:
            initial_state = {"topic": research_topic.strip()}
            
            events = []
            def on_event_research(stage, level, message):
                events.append((stage, level, message))
                status.update(label=f"[{stage}] {message}")
                
            with st.status("Esecuzione in corso…", expanded=True) as status:
                progress_placeholder = st.empty()
                tracker = make_progress_tracker(RESEARCH_PHASES, progress_placeholder)
                
                def combined_on_event(stage, level, message):
                    on_event_research(stage, level, message)
                    tracker(stage, level, message)

                subscribe(combined_on_event)
                try:
                    out = research_graph.invoke(initial_state)
                    status.update(label="Completato", state="complete")
                    st.session_state["research_output"] = out
                except Exception as e:
                    status.update(label=f"Errore: {e}", state="error")
                finally:
                    unsubscribe(combined_on_event)
                    
                for stage, level, message in events:
                    st.write(f"`[{stage}]` {message}")
                    
    out_r = st.session_state.get("research_output")
    if out_r:
        st.subheader("Report")
        st.markdown(out_r.get("final_report", ""))
        
        output_path_r = out_r.get("output_path", "")
        if output_path_r:
            file_name_r = Path(output_path_r).name
            st.download_button(
                "Scarica .md",
                data=out_r.get("final_report", ""),
                file_name=file_name_r,
                mime="text/markdown",
                key="dl_research_main"
            )

# --- TAB 3: Libreria ---
with tab_library:
    st.subheader("File generati")
    
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        lib_kind = st.radio("Tipo", ["Tutti", "Appunti", "Ricerca"], horizontal=True, key="lib_kind")
    with col_filter2:
        lib_query = st.text_input("Cerca per nome", key="lib_query").lower()
        
    notes_files = list((OUTPUTS_DIR / "notes").glob("*.md"))
    research_files = list((OUTPUTS_DIR / "research").glob("*.md"))
    
    all_files = []
    if lib_kind in ["Tutti", "Appunti"]:
        all_files.extend([("Appunti", f) for f in notes_files])
    if lib_kind in ["Tutti", "Ricerca"]:
        all_files.extend([("Ricerca", f) for f in research_files])
        
    filtered_files = [
        (kind, f) for kind, f in all_files 
        if lib_query in f.name.lower()
    ]
    
    filtered_files.sort(key=lambda x: x[1].stat().st_mtime, reverse=True)
    
    if not filtered_files:
        st.info("Nessun file corrisponde ai filtri.")
    else:
        for kind, f in filtered_files:
            icon = "📝" if kind == "Appunti" else "🔍"
            friendly_title = parse_library_title(f.name)
            expander_label = f"{icon} {friendly_title}"
            
            with st.expander(expander_label):
                mtime = datetime.datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                st.caption(f"{mtime} • {f.name} • {kind}")
                
                content = f.read_text(encoding='utf-8')
                preview = content[:600] + ('…' if len(content) > 600 else '')
                st.markdown(preview)
                
                col_btn1, col_btn2 = st.columns([1, 10])
                with col_btn1:
                    st.download_button(
                        "Scarica", 
                        data=content.encode("utf-8"),
                        file_name=f.name, 
                        mime="text/markdown", 
                        key=f"dl_{f.name}"
                    )
                with col_btn2:
                    if st.button("Elimina", key=f"del_{f.name}"):
                        f.unlink()
                        st.toast("File eliminato.", icon="🗑️")
                        time.sleep(0.5)
                        st.rerun()

# --- FOOTER ---
st.divider()
st.caption(
    "LABORATORIO DI DATA SCIENCE A.A 2025/2026 - PROF. MENSI, STUDENTE: SOARES CAMPOS MATHEUS"
)
