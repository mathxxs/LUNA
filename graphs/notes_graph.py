import datetime
from pathlib import Path
from langgraph.graph import StateGraph, START, END
from agents import NotesState
from agents.linguist import linguist
from agents.structurer import structurer
from agents.gap_detector import gap_detector
from agents.web_researcher import web_researcher
from agents.writer_notes import writer_notes
from agents.critic import critic
from config import OUTPUTS_DIR, slugify
from core.progress import emit

def save_output(state: NotesState) -> NotesState:
    emit("SaveOutput", "INFO", "Starting save_output node")
    
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    title = state.get("title", "")
    slug = slugify(title)
    if not slug:
        slug = "untitled"
        
    path = OUTPUTS_DIR / "notes" / f"{ts}_{slug}.md"
    draft = state.get("draft", "")
    
    try:
        path.write_text(draft, encoding="utf-8")
        state["output_path"] = str(path)
        emit("SaveOutput", "INFO", f"Saved to {path}")
    except Exception as e:
        emit("SaveOutput", "ERROR", f"Failed to save output to {path}: {e}")
        state["output_path"] = ""
        
    state["final_notes"] = draft
    return state

def should_research(state: NotesState) -> str:
    if state.get("web_augment"):
        return "web_researcher"
    return "writer_notes"

def route_after_critic(state: NotesState) -> str:
    verdict = state.get("critic_verdict", "APPROVE")
    iteration = state.get("iteration")
    if iteration is None:
        iteration = 0
        
    if verdict == "REVISE" and iteration < 2:
        state["iteration"] = iteration + 1
        return "writer_notes"
    return "save_output"

def build_notes_graph():
    builder = StateGraph(NotesState)
    
    builder.add_node("linguist", linguist)
    builder.add_node("structurer", structurer)
    builder.add_node("gap_detector", gap_detector)
    builder.add_node("web_researcher", web_researcher)
    builder.add_node("writer_notes", writer_notes)
    builder.add_node("critic", critic)
    builder.add_node("save_output", save_output)
    
    builder.add_edge(START, "linguist")
    builder.add_edge("linguist", "structurer")
    builder.add_edge("structurer", "gap_detector")
    
    builder.add_conditional_edges(
        "gap_detector",
        should_research,
        {
            "web_researcher": "web_researcher",
            "writer_notes": "writer_notes"
        }
    )
    
    builder.add_edge("web_researcher", "writer_notes")
    builder.add_edge("writer_notes", "critic")
    
    builder.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "writer_notes": "writer_notes",
            "save_output": "save_output"
        }
    )
    
    builder.add_edge("save_output", END)
    
    return builder.compile()

notes_graph = build_notes_graph()
