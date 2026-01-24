import pytest
import os
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from process_pipeline import process_video_file, Config

@pytest.fixture
def temp_dirs(tmp_path):
    # Mocking Config via environment variables
    env_patch = patch.dict(os.environ, {
        "SLIDES_DIR": str(tmp_path / "slides"),
        "AUDIO_DIR": str(tmp_path / "audio"),
        "TRANSCRIPT_DIR": str(tmp_path / "transcripts"),
        "FRAMES_DIR": str(tmp_path / "frames"),
    })
    
    with env_patch:
        for d in (Config.SLIDES_DIR, Config.AUDIO_DIR, Config.TRANSCRIPT_DIR, Config.FRAMES_DIR):
            d.mkdir(parents=True, exist_ok=True)
        yield tmp_path

@patch("process_pipeline.run_cmd")
@patch("process_pipeline.transcribe_audio")
@patch("process_pipeline.call_local_llm")
@patch("process_pipeline.extract_frames")
def test_process_video_file_integration(mock_frames, mock_llm, mock_transcribe, mock_run, temp_dirs):
    video_path = Path("tests/dummy.mp4")
    # Setup mocks
    mock_run.return_value = ("stdout", "stderr")
    mock_transcribe.return_value = {
        "txt": temp_dirs / "transcripts" / "dummy.txt",
        "vtt": temp_dirs / "transcripts" / "dummy.vtt"
    }
    
    # Create dummy transcript files
    (temp_dirs / "transcripts" / "dummy.txt").write_text("This is a test transcript chunk.")
    (temp_dirs / "transcripts" / "dummy.vtt").write_text("WEBVTT\n\n00:00:00.000 --> 00:00:05.000\nThis is a test")
    
    mock_llm.return_value = '{"title": "Test Slide", "bullets": ["Point 1"], "diagram_type": "none"}'
    mock_frames.return_value = [{"path": temp_dirs / "frames" / "dummy" / "f_0001.jpg", "time": 0.0}]
    
    # Run processing
    process_video_file(video_path)
    
    # Assertions
    expected_html = temp_dirs / "slides" / "dummy.html"
    assert expected_html.exists()
    assert "Test Slide" in expected_html.read_text()
