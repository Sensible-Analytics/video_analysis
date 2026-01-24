import json
import time
from typing import Optional
import requests

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"  # adjust if you use llama3:8b, mistral, etc.
RATE_LIMIT_SECONDS = 0.4
CHUNK_WORD_TARGET = 450


def build_llm_prompt_for_chunk(chunk_text: str, video_id: str, idx: int, total: int) -> str:
    return f"""
You are creating lecture slides for Mandukya Upanishad content.

Given the transcript chunk below, produce a JSON object with the following keys:

- "title": a short, clear slide title
- "bullets": an array of 3–5 concise bullet points
- "notes": 2–4 sentences of speaker notes
- "diagram_type": one of ["mindmap", "flowchart", "hierarchy", "timeline", "none"]
- "mermaid": a Mermaid diagram string appropriate for the diagram_type, or "" if diagram_type is "none"

Rules:
- If the content is conceptual (relationships between ideas), use "mindmap".
- If the content is a process or sequence, use "flowchart" or "timeline".
- If the content is layered (gross/subtle/causal/turiya), use "hierarchy".
- Mermaid must NOT be wrapped in backticks.
- Mermaid must be valid syntax for the chosen diagram_type.
- Output ONLY valid JSON, no extra text.

Transcript chunk ({idx}/{total}) for lecture {video_id}:
\"\"\"{chunk_text}\"\"\"
"""


def call_local_llm(prompt: str, model: str = MODEL_NAME, max_tokens: int = 512, temperature: float = 0.0) -> Optional[str]:
    payload = {
        "model": model,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": True,
    }

    try:
        r = requests.post(OLLAMA_API_URL, json=payload, stream=True, timeout=300)
        r.raise_for_status()

        full_text = ""
        for line in r.iter_lines():
            if not line:
                continue
            try:
                obj = json.loads(line.decode("utf-8"))
                if "response" in obj:
                    full_text += obj["response"]
            except Exception as e:
                print(f"[LLM] JSON parse error on line: {line} ({e})")
                continue

        time.sleep(RATE_LIMIT_SECONDS)
        return full_text.strip() if full_text.strip() else None

    except Exception as e:
        print(f"[ERROR] LLM call failed: {e}")
        return None


def safe_parse_json(s: str):
    try:
        return json.loads(s)
    except Exception:
        start = s.find("{")
        end = s.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(s[start:end + 1])
            except Exception:
                return None
        return None
