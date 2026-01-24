import subprocess
import shlex
import sys
from pathlib import Path

WORKDIR = Path.cwd()

VIDEO_DIR = WORKDIR / "downloads"
AUDIO_DIR = WORKDIR / "audio"
TRANSCRIPT_DIR = WORKDIR / "transcripts"
SLIDES_DIR = WORKDIR / "slides"
DIAGRAMS_DIR = WORKDIR / "diagrams"

for d in (AUDIO_DIR, TRANSCRIPT_DIR, SLIDES_DIR, DIAGRAMS_DIR):
    d.mkdir(parents=True, exist_ok=True)


def run_cmd(cmd, check=True):
    print(f"[CMD] {cmd}")
    proc = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
    if proc.returncode != 0 and check:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        raise RuntimeError(f"Command failed: {cmd}")
    return proc.stdout, proc.stderr


def list_local_videos(video_dir=VIDEO_DIR):
    exts = (".mp4", ".mkv", ".webm", ".mov")
    videos = [p for p in video_dir.iterdir() if p.suffix.lower() in exts]
    print(f"[INFO] Found {len(videos)} videos in {video_dir}")
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
