#!/usr/bin/env python3
"""
End-to-end local pipeline (rerunnable):
- Reads videos from ./downloads
- Extracts audio (skips if exists)
- Transcribes using whisper-cli + ggml CPU model (skips if transcript exists)
- Generates slides + diagrams using Ollama
- Writes Reveal.js HTML slides (skips if final HTML exists)
"""

import os
import sys
import time
import json
import shlex
import subprocess
from pathlib import Path

import requests
from slugify import slugify


# ---------------- CONFIG ----------------
WORKDIR = Path.cwd()

VIDEO_DIR = WORKDIR / "downloads"
AUDIO_DIR = WORKDIR / "audio"
TRANSCRIPT_DIR = WORKDIR / "transcripts"
SLIDES_DIR = WORKDIR / "slides"
DIAGRAMS_DIR = WORKDIR / "diagrams"

# whisper.cpp (CPU ggml model)
WHISPER_CPP_BIN = "/Users/prabhatranjan/whisper.cpp/build/bin/whisper-cli"
WHISPER_MODEL_PATH = "/Users/prabhatranjan/whisper.cpp/models/ggml-base.en.bin"

# LLM (Ollama)
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"  # or "llama3:8b", "mistral", etc.

CHUNK_WORD_TARGET = 450
RATE_LIMIT_SECONDS = 0.4
REVEAL_THEME = "black"
# ----------------------------------------

for d in (AUDIO_DIR, TRANSCRIPT_DIR, SLIDES_DIR, DIAGRAMS_DIR):
    d.mkdir(parents=True, exist_ok=True)


# ---------- utilities ----------
def run_cmd(cmd, check=True):
    print(f"[CMD] {cmd}")
    proc = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
    if proc.returncode != 0 and check:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        raise RuntimeError(f"Command failed: {cmd}")
    return proc.stdout


def list_local_videos(video_dir=VIDEO_DIR):
    exts = (".mp4", ".mkv", ".webm", ".mov")
    videos = [p for p in video_dir.iterdir() if p.suffix.lower() in exts]
    print(f"[INFO] Found {len(videos)} videos in {video_dir}")
    return videos


def extract_audio(video_path, outdir=AUDIO_DIR):
    outpath = outdir / (video_path.stem + ".wav")
    if outpath.exists():
        print(f"[SKIP] Audio already extracted → {outpath}")
        return outpath

    print(f"[AUDIO] Extracting audio from {video_path} → {outpath}")
    cmd = f"ffmpeg -y -i {shlex.quote(str(video_path))} -ac 1 -ar 16000 {shlex.quote(str(outpath))}"
    run_cmd(cmd)
    return outpath


def transcribe_audio(wav_path):
    print(f"[TRANSCRIBE] Starting transcription for {wav_path}")

    expected = TRANSCRIPT_DIR / (wav_path.stem + ".txt")

    # If transcript already exists, skip
    if expected.exists():
        print(f"[SKIP] Transcript already exists → {expected}")
        return expected

    cmd = f"{WHISPER_CPP_BIN} -m {WHISPER_MODEL_PATH} -f {wav_path} -otxt"
    print(f"[TRANSCRIBE] Running:\n  {cmd}")

    proc = subprocess.run(shlex.split(cmd), capture_output=True, text=True)

    print("[TRANSCRIBE] stdout:")
    print(proc.stdout.strip())
    print("[TRANSCRIBE] stderr:")
    print(proc.stderr.strip())

    if proc.returncode != 0:
        print(f"[TRANSCRIBE] whisper-cli failed with exit code {proc.returncode}")
        return None

    # Look for transcript in all known locations
    candidates = [
        Path(str(wav_path).replace(".wav", ".txt")),
        Path("transcript.txt"),
        Path(str(wav_path) + ".txt"),
    ]

    print("[TRANSCRIBE] Searching for transcript candidates...")
    for p in Path(".").rglob(f"{wav_path.stem}*.txt"):
        candidates.append(p)

    seen = set()
    for c in candidates:
        if c in seen:
            continue
        seen.add(c)
        print(f"[TRANSCRIBE] Checking: {c}")
        if c.exists():
            print(f"[TRANSCRIBE] Found transcript → {c}")
            expected.parent.mkdir(parents=True, exist_ok=True)
            c.rename(expected)
            print(f"[TRANSCRIBE] Moved to → {expected}")
            return expected

    print("[TRANSCRIBE] No transcript found after whisper-cli run")
    return None


def read_text_file(p):
    with open(p, "r", encoding="utf-8") as fh:
        return fh.read()


def clean_text(s):
    s = s.replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    return " ".join(s.split())


def chunk_text_by_words(text, target=CHUNK_WORD_TARGET):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        j = min(len(words), i + target)
        chunks.append(" ".join(words[i:j]))
        i = j
    return chunks


def build_llm_prompt_for_chunk(chunk_text, video_id, idx, total):
    return f"""
You are a concise slide and diagram writer for technical lectures.
Given the transcript chunk below, produce a JSON object with keys:
- title
- bullets (3–5)
- notes (2–4 sentences)
- diagram: {{ "nodes": [...], "edges": [[a,b], ...] }}

Transcript chunk ({idx}/{total}) for lecture {video_id}:
\"\"\"{chunk_text}\"\"\"

Output only valid JSON.
"""


def call_local_llm(prompt, model=MODEL_NAME, max_tokens=512, temperature=0.0):
    payload = {
        "model": model,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": True
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
                print(f"[LLM] JSON parse error on line: {line}")
                continue

        return full_text.strip()

    except Exception as e:
        print(f"[ERROR] LLM call failed: {e}")
        return None

def safe_parse_json(s):
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


def render_graphviz_svg(diagram_obj, out_svg_path):
    from graphviz import Digraph

    g = Digraph(format="svg")
    for n in diagram_obj.get("nodes", []):
        g.node(slugify(n), label=n)
    for a, b in diagram_obj.get("edges", []):
        g.edge(slugify(a), slugify(b))

    out_svg_path.parent.mkdir(parents=True, exist_ok=True)
    g.render(filename=str(out_svg_path.with_suffix("")), cleanup=True)
    return out_svg_path


def render_reveal_html(slides, title, outpath):
    slide_sections = []
    for s in slides:
        bullets_li = "\n".join(f"<li>{b}</li>" for b in s.get("bullets", []))
        notes_html = f"<aside class='notes'>{s.get('notes','')}</aside>"
        diagram_html = ""
        if s.get("diagram_svg"):
            diagram_html = f"<div><img src='{s['diagram_svg']}' style='max-width:80%;'/></div>"
        section = f"""
<section>
  <h2>{s.get('title','')}</h2>
  <ul>{bullets_li}</ul>
  {diagram_html}
  {notes_html}
</section>
"""
        slide_sections.append(section)

    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4/dist/reveal.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4/dist/theme/{REVEAL_THEME}.css">
</head>
<body>
  <div class="reveal"><div class="slides">{''.join(slide_sections)}</div></div>
  <script src="https://cdn.jsdelivr.net/npm/reveal.js@4/dist/reveal.js"></script>
  <script>Reveal.initialize({{hash:true}});</script>
</body>
</html>
"""
    outpath.parent.mkdir(parents=True, exist_ok=True)
    with open(outpath, "w", encoding="utf-8") as fh:
        fh.write(html)


# ---------- main processing ----------
def process_video_file(video_path):
    video_id = video_path.stem
    print(f"\n[INFO] Processing video: {video_id}")
    final_html = SLIDES_DIR / f"{slugify(video_id)}.html"

    # 1. Skip if slides already exist
    if final_html.exists():
        print(f"[SKIP] Slides already exist → {final_html}")
        return

    # 2. Audio (rerunnable)
    wav = AUDIO_DIR / f"{video_id}.wav"
    if wav.exists():
        print(f"[SKIP] Audio already exists → {wav}")
    else:
        wav = extract_audio(video_path)

    # 3. Transcription (rerunnable)
    transcript_path = TRANSCRIPT_DIR / f"{video_id}.txt"
    if transcript_path.exists():
        print(f"[SKIP] Transcript already exists → {transcript_path}")
    else:
        transcript_path = transcribe_audio(wav)
        if transcript_path is None or not transcript_path.exists():
            print(f"[ERROR] No transcript produced for {video_id}")
            return

    print(f"[INFO] Using transcript → {transcript_path}")

    # 4. Read + clean transcript
    raw = read_text_file(transcript_path)
    cleaned = clean_text(raw)
    chunks = chunk_text_by_words(cleaned)

    # 5. Generate slides + diagrams
    slides = []
    total_chunks = len(chunks)
    print(f"[INFO] Generating slides from {total_chunks} chunks")

    for idx, chunk in enumerate(chunks, start=1):
        print(f"[INFO] Chunk {idx}/{total_chunks}")
        prompt = build_llm_prompt_for_chunk(chunk, video_id, idx, total_chunks)
        llm_out = call_local_llm(prompt)

        if not llm_out:
            print(f"[WARN] Empty LLM output for chunk {idx}")
            continue

        parsed = safe_parse_json(llm_out)
        if not parsed:
            print(f"[WARN] JSON parse failed for chunk {idx}")
            continue

        # Diagram
        diagram_svg = None
        diagram_obj = parsed.get("diagram") or {}
        if diagram_obj.get("nodes"):
            svg_path = DIAGRAMS_DIR / f"{video_id}_chunk{idx}.svg"
            try:
                render_graphviz_svg(diagram_obj, svg_path)
                diagram_svg = os.path.relpath(svg_path, SLIDES_DIR)
            except Exception as e:
                print(f"[WARN] Diagram render failed for chunk {idx}: {e}")

        slides.append({
            "title": parsed.get("title", ""),
            "bullets": parsed.get("bullets", []),
            "notes": parsed.get("notes", ""),
            "diagram_svg": diagram_svg,
        })

        time.sleep(RATE_LIMIT_SECONDS)

    # 6. Write final slides
    if not slides:
        print(f"[ERROR] No slides generated for {video_id}")
        return

    render_reveal_html(slides, f"Lecture {video_id}", final_html)
    print(f"[INFO] Slides written → {final_html}")


def main():
    videos = list_local_videos()
    for video_path in videos:
        try:
            process_video_file(video_path)
        except Exception as e:
            print(f"[ERROR] processing {video_path}: {e}")


if __name__ == "__main__":
    main()
