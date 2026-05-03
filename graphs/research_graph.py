import datetime
from pathlib import Path
from langgraph.graph import StateGraph, START, END
from agents import ResearchState
from agents.planner import planner
from agents.searcher import searcher
from agents.synthesizer import synthesizer
from agents.writer_report import writer_report
from agents.critic import critic
from config import OUTPUTS_DIR, slugify
from core.progress import emit

def save_output(state: ResearchState) -> ResearchState:
    emit("SaveOutput", "INFO", "Starting save_output node")
    
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    topic = state.get("topic", "")
    slug = slugify(topic)
    if not slug:
        slug = "untitled"
        
    path = OUTPUTS_DIR / "research" / f"{ts}_{slug}.md"
    draft = state.get("draft", "")
    
    try:
        path.write_text(draft, encoding="utf-8")
        state["output_path"] = str(path)
        emit("SaveOutput", "INFO", f"Saved to {path}")
    except Exception as e:
        emit("SaveOutput", "ERROR", f"Failed to save output to {path}: {e}")
        state["output_path"] = ""
        
    state["final_report"] = draft
    return state

def route_after_critic(state: ResearchState) -> str:
    verdict = state.get("critic_verdict", "APPROVE")
    iteration = state.get("iteration")
    if iteration is None:
        iteration = 0
        
    if verdict == "REVISE" and iteration < 2:
        state["iteration"] = iteration + 1
        return "writer_report"
    return "save_output"

def build_research_graph():
    builder = StateGraph(ResearchState)
    
    builder.add_node("planner", planner)
    builder.add_node("searcher", searcher)
    builder.add_node("synthesizer", synthesizer)
    builder.add_node("writer_report", writer_report)
    builder.add_node("critic", critic)
    builder.add_node("save_output", save_output)
    
    builder.add_edge(START, "planner")
    builder.add_edge("planner", "searcher")
    builder.add_edge("searcher", "synthesizer")
    builder.add_edge("synthesizer", "writer_report")
    builder.add_edge("writer_report", "critic")
    
    builder.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "writer_report": "writer_report",
            "save_output": "save_output"
        }
    )
    
    builder.add_edge("save_output", END)
    
    return builder.compile()

research_graph = build_research_graph()
