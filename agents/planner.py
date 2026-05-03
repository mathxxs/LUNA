import re
from pathlib import Path
from agents import ResearchState
from core.llm import get_llm, ModelTier
from core.progress import emit

def planner(state: ResearchState) -> ResearchState:
    emit("Planner", "INFO", "Starting…")
    
    prompt_path = Path(__file__).parent.parent / "prompts" / "planner.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")
    
    llm = get_llm(ModelTier.HEAVY)
    topic = state.get("topic", "")
    
    full_prompt = f"{system_prompt}\n\nArgomento: {topic}"
    
    try:
        emit("Planner", "INFO", "Invoking LLM for query planning")
        result = llm.invoke(full_prompt).strip()
        
        lines = result.split('\n')
        sub_queries = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Drop lines starting with #, -, or digits-then-punctuation
            if re.match(r'^[\#\-]', line) or re.match(r'^\d+[\.\)]', line):
                continue
            sub_queries.append(line)
            
        # Clamp to 3-6
        sub_queries = sub_queries[:6]
        
        if len(sub_queries) < 3:
            emit("Planner", "WARNING", "Less than 3 sub-queries generated, padding with original topic")
            while len(sub_queries) < 3:
                sub_queries.append(topic)
                
        state["sub_queries"] = sub_queries
        
    except Exception as e:
        emit("Planner", "WARNING", f"LLM call failed: {e}")
        state["sub_queries"] = [topic, topic, topic]
        
    emit("Planner", "INFO", "Done.")
    return state
