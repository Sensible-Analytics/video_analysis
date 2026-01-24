from pathlib import Path
import subprocess
import shlex
from .utils import TRANSCRIPT_DIR

WHISPER_CPP_BIN = "/Users/prabhatranjan/whisper.cpp/build/bin/whisper-cli"
WHISPER_MODEL_PATH = "/Users/prabhatranjan/whisper.cpp/models/ggml-base.en.bin"


def transcribe_audio(wav_path: Path) -> Path | None:
    print(f"[TRANSCRIBE] Starting transcription for {wav_path}")

    expected = TRANSCRIPT_DIR / (wav_path.stem + ".txt")
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

    candidates: list[Path] = [
        Path(str(wav_path).replace(".wav", ".txt")),
        Path("transcript.txt"),
        Path(str(wav_path) + ".txt"),
    ]

    print("[TRANSCRIBE] Searching for transcript candidates...")
    for p in Path(".").rglob(f"{wav_path.stem}*.txt"):
        candidates.append(p)

    seen: set[Path] = set()
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
