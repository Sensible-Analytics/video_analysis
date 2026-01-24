import pytest
import json
from process_pipeline import safe_parse_json, chunk_text_by_words, clean_text

def test_safe_parse_json_valid():
    s = '{"title": "Test", "bullets": ["b1"]}'
    assert safe_parse_json(s) == {"title": "Test", "bullets": ["b1"]}

def test_safe_parse_json_with_markdown():
    s = 'Some text before ```json\n{"title": "Test"}\n``` after'
    assert safe_parse_json(s) == {"title": "Test"}

def test_safe_parse_json_trailing_comma():
    s = '{"title": "Test", "bullets": ["b1",],}'
    parsed = safe_parse_json(s)
    assert parsed["title"] == "Test"
    assert parsed["bullets"] == ["b1"]

def test_chunk_text_by_words():
    text = "one two three four five"
    assert chunk_text_by_words(text, 2) == ["one two", "three four", "five"]

def test_clean_text():
    text = "Hello\u2019s \u201cWorld\u201d   extra spaces"
    assert clean_text(text) == "Hello's \"World\" extra spaces"
