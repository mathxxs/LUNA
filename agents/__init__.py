from typing import TypedDict, Literal, List, Dict, Any

class NotesState(TypedDict):
    raw_notes: str                    # user input (pasted text or extracted from file)
    title: str                        # user-provided or LLM-generated
    web_augment: bool                 # user toggle
    linted: str                       # output of Linguist
    structured: str                   # output of Structurer
    gaps: List[Dict[str, str]]        # [{"location": str, "missing": str, "hint": str}]
    web_findings: List[Dict[str, Any]]# [{"gap_ref": int, "summary": str, "source": str}]
    draft: str                        # Writer output
    critic_verdict: Literal["APPROVE", "REVISE"]
    critic_feedback: str
    iteration: int                    # capped at 2
    final_notes: str                  # APPROVED output
    output_path: str

class ResearchState(TypedDict):
    topic: str
    sub_queries: List[str]            # planner output
    hits: List[Dict[str, str]]        # [{"query": str, "title": str, "url": str, "snippet": str, "fulltext": str}]
    synthesis: Dict[str, Any]         # {"groups": [{"theme": str, "items": [hit_indices]}]}
    draft: str
    critic_verdict: Literal["APPROVE", "REVISE"]
    critic_feedback: str
    iteration: int                    # capped at 2
    final_report: str
    output_path: str
