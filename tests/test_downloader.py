import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from downloader import download_youtube_content

@patch("downloader.subprocess.run")
def test_download_youtube_content(mock_run, tmp_path):
    mock_run.return_value = MagicMock(returncode=0, stdout="dummy_id.mp4\n")
    
    url = "https://www.youtube.com/watch?v=dummy"
    output_dir = tmp_path / "downloads"
    
    download_youtube_content(url, output_dir=output_dir, audio_only=True)
    
    # Check if command was called
    called_args = mock_run.call_args[0][0]
    assert "yt-dlp" in called_args
    assert "--audio-format" in called_args
    assert "wav" in called_args
    assert url in called_args
