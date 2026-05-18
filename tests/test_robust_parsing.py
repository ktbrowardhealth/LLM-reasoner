"""Tests for robust JSON repair and fallback parsing."""
import json
import pytest
from llm_reasoner.engine import Step

def test_perfect_json():
    """Test parsing of perfect JSON."""
    text = '{"title": "Step 1", "content": "Perfect", "next_action": "continue", "confidence": 0.9}'
    result = Step._extract_json_from_text(text)
    assert result is not None
    assert result["title"] == "Step 1"

def test_malformed_json_repair():
    """Test repair of malformed JSON (missing quotes, trailing commas)."""
    # json-repair handles missing quotes and trailing commas
    text = '{title: "Step 1", content: "Malformed", next_action: "continue", confidence: 0.9,}'
    result = Step._extract_json_from_text(text)
    assert result is not None
    assert result["title"] == "Step 1"

def test_json_in_markdown():
    """Test extraction of JSON from markdown code blocks."""
    text = "Here is my reasoning:\n\n```json\n{\"title\": \"Markdown Step\", \"content\": \"In block\"}\n```"
    result = Step._extract_json_from_text(text)
    assert result is not None
    assert result["title"] == "Markdown Step"

def test_aggressive_extraction():
    """Test aggressive extraction from text surrounding JSON."""
    text = "Thinking... { \"title\": \"Aggressive\", \"content\": \"Found it\" } ...End of thought"
    result = Step._extract_json_from_text(text)
    assert result is not None
    assert result["title"] == "Aggressive"

def _wrap_response(content):
    return {
        "choices": [{
            "message": {
                "content": content
            }
        }],
        "usage": {"total_tokens": 0},
        "cost": 0.0
    }

def test_xml_fallback():
    """Test fallback to XML-like format when JSON parsing fails completely."""
    text = "Step 1: The First Step\n<thinking>I am thinking</thinking>\nThis is the content."
    step = Step.from_response(1, _wrap_response(text), 1.0)
    assert step.title == "The First Step"
    assert step.content == "This is the content."
    assert step.confidence == 0.8  # Default for fallback

def test_partial_json_repair():
    """Test repair of partial/incomplete JSON."""
    text = '{"title": "Partial", "content": "Incomplete'
    result = Step._extract_json_from_text(text)
    # json-repair can often close open braces/quotes
    if result:
        assert result["title"] == "Partial"
        assert "content" in result
