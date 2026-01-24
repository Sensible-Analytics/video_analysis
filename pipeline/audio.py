from pathlib import Path
from .utils import run_cmd, AUDIO_DIR
import shlex


def extract_audio(video_path: Path) -> Path:
    outpath = AUDIO_DIR / (video_path.stem + ".wav")
    if outpath.exists():
        print(f"[SKIP] Audio already extracted → {outpath}")
        return outpath

    print(f"[AUDIO] Extracting audio from {video_path} → {outpath}")
    cmd = f"ffmpeg -y -i {shlex.quote(str(video_path))} -ac 1 -ar 16000 {shlex.quote(str(outpath))}"
    run_cmd(cmd)
    return outpath
