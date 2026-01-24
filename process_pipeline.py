#!/usr/bin/env python3
"""
End-to-end local pipeline for generating lecture slides with Mermaid diagrams.

Features:
- Rerunnable (skip audio, skip transcript, skip slides)
- Whisper.cpp transcription (ggml CPU)
- Streaming-safe Ollama client
- Mermaid-only diagrams (mindmap, flowchart, hierarchy, timeline)
- 40/60 flexbox layout
- Light Mermaid theme
- Reveal.js slide generation
- Full logging
"""

import os
import sys
import json
import time
import shlex
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, List
import re
from slugify import slugify
import requests
from dotenv import load_dotenv

# Optional Cognee integration
try:
    import cognee
    import asyncio
    HAS_COGNEE = True
except Exception:
    HAS_COGNEE = False

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

class Config:
    @property
    def WORKDIR(self):
        return Path.cwd()

    @property
    def VIDEO_DIR(self):
        return Path(os.getenv("VIDEO_DIR", self.WORKDIR / "downloads"))

    @property
    def AUDIO_DIR(self):
        return Path(os.getenv("AUDIO_DIR", self.WORKDIR / "audio"))

    @property
    def TRANSCRIPT_DIR(self):
        return Path(os.getenv("TRANSCRIPT_DIR", self.WORKDIR / "transcripts"))

    @property
    def SLIDES_DIR(self):
        return Path(os.getenv("SLIDES_DIR", self.WORKDIR / "slides"))

    # Whisper.cpp
    @property
    def WHISPER_CPP_BIN(self):
        return os.getenv("WHISPER_CPP_BIN", "/Users/prabhatranjan/whisper.cpp/build/bin/whisper-cli")
    
    @property
    def WHISPER_MODEL_PATH(self):
        return os.getenv("WHISPER_MODEL_PATH", "/Users/prabhatranjan/whisper.cpp/models/ggml-base.en.bin")

    # LLM
    @property
    def OLLAMA_API_URL(self):
        return os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
    
    @property
    def MODEL_NAME(self):
        return os.getenv("MODEL_NAME", "qwen2.5-coder:7b")
    
    @property
    def FALLBACK_MODELS(self):
        val = os.getenv("FALLBACK_MODELS", "llama3:latest")
        return [m.strip() for m in val.split(",")]
    
    @property
    def RATE_LIMIT_SECONDS(self):
        return float(os.getenv("RATE_LIMIT_SECONDS", "0.4"))
    
    @property
    def CHUNK_WORD_TARGET(self):
        return int(os.getenv("CHUNK_WORD_TARGET", "450"))

    # Reveal.js
    @property
    def REVEAL_THEME(self):
        return os.getenv("REVEAL_THEME", "black")

    @property
    def MERMAID_THEME(self):
        return os.getenv("MERMAID_THEME", "default")

    @property
    def FRAMES_DIR(self):
        return self.SLIDES_DIR / "frames"

# Create singleton instance
Config = Config()

# Initialize directories
def init_dirs():
    for d in (Config.AUDIO_DIR, Config.TRANSCRIPT_DIR, Config.SLIDES_DIR, Config.FRAMES_DIR):
        d.mkdir(parents=True, exist_ok=True)

init_dirs()

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Config.WORKDIR / "pipeline.log")
    ]
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# UTILITIES
# ---------------------------------------------------------

def run_cmd(cmd, check=True):
    logger.info(f"Running command: {cmd}")
    proc = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
    if proc.returncode != 0 and check:
        logger.error(f"Command failed: {cmd}")
        logger.error(f"stdout: {proc.stdout}")
        logger.error(f"stderr: {proc.stderr}")
        raise RuntimeError(f"Command failed: {cmd}")
    return proc.stdout, proc.stderr


def list_local_videos():
    exts = (".mp4", ".mkv", ".webm", ".mov")
    videos = [p for p in Config.VIDEO_DIR.iterdir() if p.suffix.lower() in exts]
    logger.info(f"Found {len(videos)} videos in {Config.VIDEO_DIR}")
    return videos


def read_text_file(p: Path) -> str:
    with open(p, "r", encoding="utf-8") as fh:
        return fh.read()


def write_text_file(p: Path, content: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(content)


def clean_text(s: str) -> str:
    s = s.replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    return " ".join(s.split())


def chunk_text_by_words(text: str, target: int):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        j = min(len(words), i + target)
        chunks.append(" ".join(words[i:j]))
        i = j
    return chunks


def parse_vtt_timestamps(vtt_path: Path) -> List[Dict]:
    """
    Parses a VTT file and returns a list of segments with start/end times and text.
    """
    import re
    if not vtt_path.exists():
        return []
    
    content = vtt_path.read_text(encoding="utf-8")
    # Match 00:00:00.000 --> 00:00:00.000
    timestamp_pattern = re.compile(r"(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})")
    
    segments = []
    lines = content.splitlines()
    for i, line in enumerate(lines):
        match = timestamp_pattern.match(line)
        if match:
            start_str = match.group(1)
            # Text is usually on the next line
            text = ""
            if i + 1 < len(lines):
                text = lines[i+1].strip()
            
            # Convert timestamp to total seconds
            h, m, s = start_str.split(":")
            seconds = int(h)*3600 + int(m)*60 + float(s)
            
            segments.append({
                "start": seconds,
                "text": text
            })
    return segments


def find_start_time_for_chunk(chunk_text: str, segments: List[Dict]) -> float:
    """
    Finds the approximate start time for a chunk of text by searching for its
    first few words in the VTT segments.
    """
    first_words = " ".join(chunk_text.split()[:5]).lower()
    for seg in segments:
        if first_words in seg["text"].lower():
            return seg["start"]
    return segments[0]["start"] if segments else 0.0


def extract_frames(video_path: Path) -> List[Dict]:
    """
    Detects scene changes and extracts frames using ffmpeg.
    Returns a list of {'path': Path, 'time': float}.
    """
    video_id = video_path.stem
    out_dir = Config.FRAMES_DIR / video_id
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # We use a lower threshold (0.05) to capture major slide changes
    # -vsync vfr: variable frame rate output
    # select='gt(scene,0.05)': select frames where scene change > 5%
    cmd = (
        f"ffmpeg -y -i {shlex.quote(str(video_path))} "
        f"-vf \"select='gt(scene,0.05)',showinfo\" "
        f"-vsync vfr {shlex.quote(str(out_dir))}/f_%04d.jpg"
    )
    
    logger.info(f"Extracting frames (scene detection) for {video_id}...")
    stdout, stderr = run_cmd(cmd)
    
    frames = []
    # Parse showinfo output from stderr to get timestamps
    import re
    # showinfo line looks like: [Parsed_showinfo_1 @ 0x...] n:   0 pts: 123456 pts_time:12.3456 ...
    pts_pattern = re.compile(r"pts_time:(\d+\.\d+)")
    
    timestamps = pts_pattern.findall(stderr)
    
    # List actual files extracted
    extracted_files = sorted(list(out_dir.glob("f_*.jpg")))
    
    for i, file_path in enumerate(extracted_files):
        time_val = float(timestamps[i]) if i < len(timestamps) else 0.0
        frames.append({
            "path": file_path,
            "time": time_val
        })
    
    logger.info(f"Extracted {len(frames)} frames for {video_id}")
    return frames


def find_closest_frame(target_time: float, frames: List[Dict]) -> Optional[Path]:
    if not frames:
        return None
    # Find the frame that occurred most recently BEFORE or at the target time
    closest = None
    for f in frames:
        if f["time"] <= target_time:
            closest = f["path"]
        else:
            break
    return closest or frames[0]["path"]


# ---------------------------------------------------------
# AUDIO EXTRACTION
# ---------------------------------------------------------

def extract_audio(video_path: Path) -> Path:
    outpath = Config.AUDIO_DIR / (video_path.stem + ".wav")
    if outpath.exists():
        logger.info(f"Audio already extracted → {outpath}")
        return outpath

    logger.info(f"Extracting audio from {video_path} → {outpath}")
    cmd = f"ffmpeg -y -i {shlex.quote(str(video_path))} -ac 1 -ar 16000 {shlex.quote(str(outpath))}"
    run_cmd(cmd)
    return outpath


# ---------------------------------------------------------
# TRANSCRIPTION (WHISPER.CPP)
# ---------------------------------------------------------

def transcribe_audio(wav_path: Path) -> Dict[str, Path]:
    logger.info(f"Starting transcription for {wav_path}")

    results = {}
    base_expected = Config.TRANSCRIPT_DIR / wav_path.stem
    txt_expected = base_expected.with_suffix(".txt")
    vtt_expected = base_expected.with_suffix(".vtt")

    if txt_expected.exists() and vtt_expected.exists():
        logger.info(f"Transcripts already exist → {txt_expected}, {vtt_expected}")
        return {"txt": txt_expected, "vtt": vtt_expected}

    # Generate both TXT and VTT
    cmd = f"{Config.WHISPER_CPP_BIN} -m {Config.WHISPER_MODEL_PATH} -f {wav_path} -otxt -ovtt"
    logger.debug(f"Running: {cmd}")

    proc = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
    if proc.returncode != 0:
        logger.error(f"whisper-cli failed for {wav_path} (code {proc.returncode})")
        logger.error(f"stderr: {proc.stderr}")
        return {}

    # Map extensions to expected paths
    ext_map = {".txt": txt_expected, ".vtt": vtt_expected}
    
    for ext, expected_path in ext_map.items():
        candidates = [
            Path(str(wav_path).replace(".wav", ext)),
            Path(f"transcript{ext}"),
            Path(str(wav_path) + ext),
        ]
        
        # Search for candidates
        for p in Path(".").rglob(f"{wav_path.stem}*{ext}"):
            candidates.append(p)

        found = False
        for c in candidates:
            if c.exists():
                logger.info(f"Found {ext} transcript → {c}")
                expected_path.parent.mkdir(parents=True, exist_ok=True)
                c.rename(expected_path)
                results[ext.strip(".")] = expected_path
                found = True
                break
        
        if not found and expected_path.exists():
             results[ext.strip(".")] = expected_path

    if not results:
        logger.error("[TRANSCRIBE] No transcript files found after whisper-cli run")
    
    return results


async def get_cognee_context(query: str) -> str:
    """
    Retrieves semantic and graph context from Cognee.
    """
    if not HAS_COGNEE:
        return ""
    
    try:
        # Cognee search uses query_text and datasets (list of strings)
        search_results = await cognee.search(
            query_text = query,
            datasets = ["mandukya_upanishad"]
        )
        
        context_parts = []
        # Cognee returns result objects
        for result in search_results[:3]:
            # Try to extract content from Cognee result object
            text = getattr(result, "text", None) or str(result)
            context_parts.append(f"Related Context: {text}")
        
        return "\n".join(context_parts)
    except Exception as e:
        logger.warning(f"Cognee search failed: {e}")
        return ""


# ---------------------------------------------------------
# LLM (OLLAMA STREAMING)
# ---------------------------------------------------------

def build_llm_prompt_for_chunk(chunk_text: str, video_id: str, idx: int, total: int, graph_context: str = "") -> str:
    context_block = f"\nAdditional Knowledge Graph Context:\n{graph_context}\n" if graph_context else ""
    
    return f"""
You MUST output ONLY a single JSON object.
No explanations.
No commentary.
No Markdown.
No backticks.
No text before or after the JSON.

JSON schema:
{{
  "title": "string",
  "bullets": ["string", ...],
  "notes": "string",
  "diagram_type": "mindmap" | "flowchart" | "hierarchy" | "timeline" | "none",
  "mermaid": "string"
}}

Guidance:
- If conceptual, use "mindmap".
- If a process, use "flowchart" or "timeline".
- If layered (gross/subtle/causal/turiya), use "hierarchy".
- If no diagram is appropriate, use "diagram_type": "none" and "mermaid": "".
{context_block}
Transcript chunk ({idx}/{total}) for lecture {video_id}:
\"\"\"{chunk_text}\"\"\"
"""


def call_local_llm(prompt: str, model_name: Optional[str] = None) -> Optional[str]:
    model = model_name or Config.MODEL_NAME
    payload = {
        "model": model,
        "prompt": prompt,
        "max_tokens": 512,
        "temperature": 0.0,
        "stream": True,
    }

    try:
        r = requests.post(Config.OLLAMA_API_URL, json=payload, stream=True, timeout=300)
        r.raise_for_status()

        full_text = ""
        for line in r.iter_lines():
            if not line:
                continue
            try:
                obj = json.loads(line.decode("utf-8"))
            except Exception as e:
                print(f"[LLM] Line JSON decode error: {e} | line={line}")
                continue

            if "response" in obj:
                full_text += obj["response"]

        full_text = full_text.strip()
        time.sleep(RATE_LIMIT_SECONDS)
        return full_text if full_text else None

    except Exception as e:
        print(f"[ERROR] LLM call failed: {e}")
        return None


def safe_parse_json(s: str):
    if not s:
        return None

    # Step 1: Clean potential markdown formatting
    # Handle cases where LLM puts JSON inside ```json ... ``` or ``` ... ```
    if "```" in s:
        # Match the content between first and last code block delimiters
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", s, re.DOTALL)
        if match:
            s = match.group(1)
        else:
            # Fallback if the above regex fails but ``` is present
            s = s.replace("```json", "").replace("```", "").strip()

    # Step 2: Extract content between outermost braces
    start = s.find("{")
    end = s.rfind("}")

    if start == -1 or end == -1 or end <= start:
        return None

    candidate = s[start:end + 1]

    # Step 3: Final attempt at parsing
    try:
        return json.loads(candidate)
    except Exception as e:
        logger.warning(f"JSON parsing failed: {e}. Attempting further cleanup.")
        # Try a more aggressive cleanup if needed (e.g., removing trailing commas)
        try:
             # Basic cleanup: remove trailing commas in lists/objects
            cleaned = re.sub(r',\s*([\]}])', r'\1', candidate)
            return json.loads(cleaned)
        except Exception:
            logger.error(f"Definitive JSON parse failure for: {candidate}")
            return None


# ---------------------------------------------------------
# MERMAID NORMALIZATION
# ---------------------------------------------------------

class DiagramSpec:
    def __init__(self, diagram_type: str, mermaid: str):
        self.diagram_type = diagram_type
        self.mermaid = mermaid


def normalize_mermaid(diagram_type: str, mermaid: str) -> Optional[DiagramSpec]:
    if not mermaid or not mermaid.strip():
        return None

    m = mermaid.strip().strip("`").strip()

    dt = diagram_type.lower()
    if dt == "mindmap" and not m.lower().startswith("mindmap"):
        m = "mindmap\n  " + m
    elif dt == "flowchart" and "flowchart" not in m.lower():
        m = "flowchart TD\n  " + m
    elif dt == "hierarchy" and not m.lower().startswith("graph"):
        m = "graph TD\n  " + m
    elif dt == "timeline" and "timeline" not in m.lower():
        m = "flowchart TD\n  " + m

    return DiagramSpec(dt, m)


# ---------------------------------------------------------
# SLIDE GENERATION (REVEAL.JS + MERMAID)
# ---------------------------------------------------------

def render_slide_section(slide: Dict) -> str:
    title = slide.get("title", "")
    bullets = slide.get("bullets", [])
    notes = slide.get("notes", "")
    diagram: Optional[DiagramSpec] = slide.get("diagram")
    start_time = slide.get("start_time", 0.0)
    video_id = slide.get("video_id", "")
    screenshot_path = slide.get("screenshot")
    
    # Construct YouTube link
    yt_link = ""
    if video_id and len(video_id) == 11:
        time_str = int(start_time)
        yt_link = f'<div class="timestamp"><a href="https://youtu.be/{video_id}?t={time_str}" target="_blank">🔗 View at {time_str}s</a></div>'

    bullets_html = "\n".join(f"<li>{b}</li>" for b in bullets)
    notes_html = f"<aside class='notes'>{notes}</aside>" if notes else ""

    screenshot_html = ""
    if screenshot_path:
        # Use relative path for HTML
        rel_screenshot = os.path.relpath(screenshot_path, Config.SLIDES_DIR)
        screenshot_html = f'<div class="screenshot"><img src="{rel_screenshot}" alt="Slide Screenshot"></div>'

    if diagram:
        mermaid_block = f"<pre class='mermaid'>\n{diagram.mermaid}\n</pre>"
    else:
        mermaid_block = "<div>No diagram</div>"

    return f"""
<section>
  <div class="two-col">
    <div class="left">
      <h2>{title}</h2>
      {yt_link}
      <ul>{bullets_html}</ul>
      {notes_html}
    </div>
    <div class="right">
      {screenshot_html}
      {mermaid_block}
    </div>
  </div>
</section>
"""


def render_reveal_html(slides: List[Dict], title: str, outpath: Path):
    slide_sections = [render_slide_section(s) for s in slides]

    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4/dist/reveal.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4/dist/theme/{Config.REVEAL_THEME}.css">
  <style>
    .two-col {{
      display: flex;
      gap: 20px;
      align-items: flex-start;
    }}
    .two-col .left {{
      flex: 0 0 40%;
    }}
    .two-col .right {{
      flex: 0 0 60%;
    }}
    .mermaid {{
      font-size: 0.9rem;
    }}
    .timestamp a {{
      color: #aaa;
      font-size: 0.8rem;
      text-decoration: none;
    }}
    .timestamp a:hover {{
      text-decoration: underline;
    }}
    .screenshot img {{
      max-width: 100%;
      border-radius: 8px;
      box-shadow: 0 4px 10px rgba(0,0,0,0.5);
      margin-bottom: 20px;
    }}
  </style>
</head>
<body>
  <div class="reveal">
    <div class="slides">
      {''.join(slide_sections)}
    </div>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/reveal.js@4/dist/reveal.js"></script>
  <script>
    Reveal.initialize({{hash:true}});
  </script>
  <script type="module">
    import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs";
    mermaid.initialize({{ startOnLoad: true, theme: "{Config.MERMAID_THEME}" }});
  </script>
</body>
</html>
"""
    write_text_file(outpath, html)
    logger.info(f"Slides written → {outpath}")


def slides_output_path(video_id: str) -> Path:
    return Config.SLIDES_DIR / f"{slugify(video_id)}.html"


# ---------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------

def process_video_file(video_path: Path):
    video_id = video_path.stem
    logger.info(f"Processing video: {video_id}")

    final_html = slides_output_path(video_id)
    if final_html.exists():
        logger.info(f"Slides already exist → {final_html}")
        return

    # Audio
    wav = Config.AUDIO_DIR / f"{video_id}.wav"
    if wav.exists():
        logger.info(f"Audio already exists → {wav}")
    else:
        wav = extract_audio(video_path)

    # Visuals
    frames = extract_frames(video_path)

    # Transcript
    transcripts = transcribe_audio(wav)
    transcript_path = transcripts.get("txt")
    vtt_path = transcripts.get("vtt")

    if not transcript_path or not transcript_path.exists():
        logger.error(f"No text transcript produced for {video_id}")
        return

    logger.info(f"Using transcript → {transcript_path}")
    vtt_segments = parse_vtt_timestamps(vtt_path) if vtt_path else []

    # Read + chunk
    raw = read_text_file(transcript_path)
    cleaned = clean_text(raw)
    chunks = chunk_text_by_words(cleaned, Config.CHUNK_WORD_TARGET)
    total_chunks = len(chunks)
    logger.info(f"Generating slides from {total_chunks} chunks")

    slides: List[Dict] = []

    for idx, chunk in enumerate(chunks, start=1):
        logger.info(f"Chunk {idx}/{total_chunks}")
        
        # Retrieve graph context if available
        graph_context = ""
        if HAS_COGNEE:
            try:
                # We use the first 100 characters as a semantic anchor for the graph search
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we are already in an event loop (e.g. pytest-asyncio), we can't use run_until_complete
                    # This is a bit tricky for a synchronous loop. 
                    # For now, let's just skip context if loop is running to avoid crash.
                    pass
                else:
                    graph_context = loop.run_until_complete(get_cognee_context(chunk[:100]))
            except Exception as e:
                logger.warning(f"Failed to get graph context: {e}")

        prompt = build_llm_prompt_for_chunk(chunk, video_id, idx, total_chunks, graph_context)
        
        # Enhanced multi-model fallback logic
        llm_out = None
        models_to_try = [Config.MODEL_NAME] + Config.FALLBACK_MODELS
        
        for model in models_to_try:
            logger.info(f"Trying model: {model}")
            for attempt in range(2):
                llm_out = call_local_llm(prompt, model_name=model)
                if llm_out:
                    parsed = safe_parse_json(llm_out)
                    if parsed:
                        break # Success
                    else:
                        logger.warning(f"JSON parse failed for model {model} (attempt {attempt+1})")
                        llm_out = None
                else:
                    logger.warning(f"LLM call failed for model {model} (attempt {attempt+1})")
                time.sleep(1)
            
            if llm_out:
                break # Found a model that works
        
        if not llm_out:
            logger.error(f"All models failed for chunk {idx}")
            continue

        # We already successfully parsed it in the loop
        parsed = safe_parse_json(llm_out)

        diagram_spec = None
        diagram_type = (parsed.get("diagram_type") or "none").lower()
        mermaid_raw = parsed.get("mermaid") or ""

        if diagram_type != "none":
            diagram_spec = normalize_mermaid(diagram_type, mermaid_raw)
            if not diagram_spec:
                logger.warning(f"Invalid Mermaid for chunk {idx}, skipping diagram")

        start_time = find_start_time_for_chunk(chunk, vtt_segments)
        screenshot = find_closest_frame(start_time, frames)

        slide = {
            "title": parsed.get("title", ""),
            "bullets": parsed.get("bullets", []),
            "notes": parsed.get("notes", ""),
            "diagram": diagram_spec,
            "start_time": start_time,
            "video_id": video_id,
            "screenshot": screenshot
        }
        slides.append(slide)

    if not slides:
        logger.error(f"No slides generated for {video_id}")
        return

    render_reveal_html(slides, f"Lecture {video_id}", final_html)


def main():
    # Load environment variables for Cognee/Ollama
    load_dotenv()
    
    videos = list_local_videos()
    for video_path in videos:
        try:
            process_video_file(video_path)
        except Exception as e:
            logger.exception(f"Fatal error processing {video_path}: {e}")


if __name__ == "__main__":
    main()
