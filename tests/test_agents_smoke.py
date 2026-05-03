import pytest
from agents.linguist import linguist
from agents.structurer import structurer
from agents.gap_detector import gap_detector
from agents.web_researcher import web_researcher
from agents.writer_notes import writer_notes
from agents.critic import critic
from agents.planner import planner
from agents.searcher import searcher
from agents.synthesizer import synthesizer
from agents.writer_report import writer_report

class FakeLLM:
    def __init__(self, response: str):
        self.response = response
    def invoke(self, prompt, **kwargs) -> str:
        return self.response

def test_linguist(monkeypatch):
    monkeypatch.setattr("agents.linguist.get_llm", lambda t: FakeLLM("test linted output"))
    state = {"raw_notes": "test raw"}
    out = linguist(state.copy())
    
    assert "linted" in out
    assert isinstance(out["linted"], str)
    assert out["raw_notes"] == "test raw"

def test_structurer(monkeypatch):
    monkeypatch.setattr("agents.structurer.get_llm", lambda t: FakeLLM("test structured output"))
    state = {"linted": "test linted"}
    out = structurer(state.copy())
    
    assert "structured" in out
    assert isinstance(out["structured"], str)
    assert out["linted"] == "test linted"

def test_gap_detector(monkeypatch):
    fake_json = '[{"location": "A", "missing": "B", "hint": "C"}]'
    monkeypatch.setattr("agents.gap_detector.get_llm", lambda t: FakeLLM(fake_json))
    state = {"structured": "test structured"}
    out = gap_detector(state.copy())
    
    assert "gaps" in out
    assert isinstance(out["gaps"], list)
    assert len(out["gaps"]) == 1
    assert "location" in out["gaps"][0]
    assert out["structured"] == "test structured"

def test_web_researcher(monkeypatch):
    monkeypatch.setattr("agents.web_researcher.get_llm", lambda t: FakeLLM("test summary URL: http://example.com"))
    monkeypatch.setattr("agents.web_researcher.search_and_fetch", lambda q, k: [{"url": "http://example.com", "snippet": "foo"}])
    
    state = {"gaps": [{"location": "A", "missing": "B", "hint": "C"}], "web_augment": True}
    out = web_researcher(state.copy())
    
    assert "web_findings" in out
    assert isinstance(out["web_findings"], list)
    if out["web_findings"]:
        assert "summary" in out["web_findings"][0]
    assert out["gaps"] == state["gaps"]
    assert out["web_augment"] == state["web_augment"]

def test_writer_notes(monkeypatch):
    monkeypatch.setattr("agents.writer_notes.get_llm", lambda t: FakeLLM("final draft"))
    state = {
        "structured": "test", 
        "gaps": [{"location": "A", "missing": "B", "hint": "C"}], 
        "web_findings": [{"summary": "foo", "source": "bar"}],
        "critic_feedback": ""
    }
    out = writer_notes(state.copy())
    
    assert "draft" in out
    assert isinstance(out["draft"], str)
    assert out["structured"] == "test"
    assert out["gaps"] == [{"location": "A", "missing": "B", "hint": "C"}]

def test_critic(monkeypatch):
    monkeypatch.setattr("agents.critic.get_llm", lambda t, **kwargs: FakeLLM("I REVISE this draft"))
    state = {"draft": "test draft"}
    out = critic(state.copy())
    
    assert "critic_verdict" in out
    assert out["critic_verdict"] == "REVISE"
    assert "critic_feedback" in out
    assert isinstance(out["critic_feedback"], str)
    assert out["draft"] == "test draft"

def test_planner(monkeypatch):
    monkeypatch.setattr("agents.planner.get_llm", lambda t: FakeLLM("query 1\nquery 2\nquery 3"))
    state = {"topic": "AI"}
    out = planner(state.copy())
    
    assert "sub_queries" in out
    assert isinstance(out["sub_queries"], list)
    assert len(out["sub_queries"]) == 3
    assert out["topic"] == "AI"

def test_searcher(monkeypatch):
    monkeypatch.setattr("agents.searcher.search_and_fetch", lambda q, k: [{"url": "http://x", "fulltext": "a" * 300}])
    state = {"sub_queries": ["query 1"]}
    out = searcher(state.copy())
    
    assert "hits" in out
    assert isinstance(out["hits"], list)
    assert len(out["hits"]) == 1
    assert out["hits"][0]["query"] == "query 1"
    assert out["sub_queries"] == ["query 1"]

def test_synthesizer(monkeypatch):
    fake_json = '{"groups": [{"theme": "A", "items": [0]}]}'
    monkeypatch.setattr("agents.synthesizer.get_llm", lambda t: FakeLLM(fake_json))
    state = {"hits": [{"title": "t", "snippet": "s"}]}
    out = synthesizer(state.copy())
    
    assert "synthesis" in out
    assert isinstance(out["synthesis"], dict)
    assert "groups" in out["synthesis"]
    assert out["hits"] == state["hits"]

def test_writer_report(monkeypatch):
    monkeypatch.setattr("agents.writer_report.get_llm", lambda t: FakeLLM("final report draft"))
    state = {"topic": "AI", "synthesis": {}, "hits": [], "critic_feedback": ""}
    out = writer_report(state.copy())
    
    assert "draft" in out
    assert isinstance(out["draft"], str)
    assert out["topic"] == "AI"

def test_writer_report_sanitize(monkeypatch):
    duplicated_output = "## Sintesi\nSintesi\nContenuto reale"
    monkeypatch.setattr("agents.writer_report.get_llm", lambda t: FakeLLM(duplicated_output))
    state = {"topic": "AI", "synthesis": {}, "hits": [], "critic_feedback": ""}
    out = writer_report(state.copy())
    
    import re
    draft = out["draft"]
    assert not re.search(r"^(##\s+(Sintesi|Notizie / Findings|Discrepanze tra fonti|Fonti))\s*\n\s*(?:\2)\s*(?:\n|$)", draft, re.MULTILINE)
    assert "Contenuto reale" in draft
