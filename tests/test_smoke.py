import os
from app.config import load_config
from app.sources import load_sources
from app.llm import generate_text
from app.report import build_final_report

def test_config_loads():
    config = load_config()
    assert config is not None
    assert hasattr(config, "LLM_PROVIDER")

def test_source_config_loads():
    sources = load_sources()
    # It returns a SourceConfig dataclass, not a dict
    assert hasattr(sources, "rss")
    
def test_mock_llm_returns_text():
    # Force mock provider
    result = generate_text("Test prompt", provider="mock")
    assert isinstance(result, str)
    assert len(result) > 0

def test_report_builder():
    config = load_config()
    summary = "This is a summary."
    ideas = "### 1. Test Idea\nPitch."
    
    report = build_final_report(summary, ideas, config)
    
    assert isinstance(report, str)
    assert "Daily Tech & AI Opportunity Brief" in report
    assert "This is a summary." in report
    assert "### 1. Test Idea" in report
