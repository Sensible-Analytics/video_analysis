import pytest
import subprocess
import os
import shutil
from pathlib import Path

def test_pipeline_e2e_dry_run(tmp_path):
    """
    E2E test that runs the main pipeline with mocked binaries.
    """
    workdir = tmp_path / "e2e"
    workdir.mkdir()
    
    # Create fake project structure
    (workdir / "downloads").mkdir()
    (workdir / "downloads" / "test_video.mp4").write_text("fake video content")
    
    # Create fake whisper binary
    whisper_bin = workdir / "fake_whisper"
    whisper_bin.write_text(f"#!/bin/bash\necho 'fake' > {workdir}/transcripts/test_video.txt\necho 'WEBVTT' > {workdir}/transcripts/test_video.vtt")
    whisper_bin.chmod(0o755)
    
    # Create environment variables for test
    env = os.environ.copy()
    env["VIDEO_DIR"] = str(workdir / "downloads")
    env["AUDIO_DIR"] = str(workdir / "audio")
    env["TRANSCRIPT_DIR"] = str(workdir / "transcripts")
    env["SLIDES_DIR"] = str(workdir / "slides")
    env["WHISPER_CPP_BIN"] = str(whisper_bin)
    env["WHISPER_MODEL_PATH"] = str(workdir / "fake_model.bin")
    env["PYTHONPATH"] = "."
    
    # Run the pipeline (we'll only run one iteration or mock the LLM part if possible)
    # We'll use a specific script to run just one file
    cmd = ["python3", "process_pipeline.py"]
    
    # Since process_pipeline.py runs against ALL videos, and we have one, it should work.
    # We'll mock the LLM response by monkeypatching or just letting it fail if Ollama is not there.
    # Actually, let's use a wrapper to mock requests.post for Ollama.
    
    # For a true E2E without Ollama, we'd need to mock the Ollama API locally.
    # Let's just verify it starts and fails at the right place, OR mock the LLM call.
    
    # We can use a small python snippet to run the pipeline with mocked LLM
    test_script = workdir / "run_e2e.py"
    test_script.write_text(f"""
import sys
import os
sys.path.insert(0, '{os.getcwd()}')
from unittest.mock import patch, MagicMock
from pathlib import Path
import process_pipeline

# Mock Ollama and Cognee
with patch("process_pipeline.call_local_llm") as mock_llm, \\
     patch("process_pipeline.HAS_COGNEE", False), \\
     patch("process_pipeline.run_cmd") as mock_run:
    
    mock_llm.return_value = '{{"title": "E2E Slide", "bullets": ["E2E Point"], "diagram_type": "none"}}'
    mock_run.return_value = ("stdout", "stderr")
    
    process_pipeline.process_video_file(Path("{workdir}/downloads/test_video.mp4"))
""")

    result = subprocess.run(["python3", str(test_script)], env=env, capture_output=True, text=True)
    
    print(f"STDOUT: {result.stdout}")
    print(f"STDERR: {result.stderr}")
    
    assert result.returncode == 0 or "Error" not in result.stderr
    assert (workdir / "slides" / "test-video.html").exists()
    assert "E2E Slide" in (workdir / "slides" / "test-video.html").read_text()
