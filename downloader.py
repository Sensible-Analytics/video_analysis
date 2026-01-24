#!/usr/bin/env python3
"""
Downloads YouTube playlists or individual videos using yt-dlp.
Optimized for the lecture processing pipeline.
"""

import os
import json
import argparse
import logging
import subprocess
from pathlib import Path

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = Path.cwd() / "downloads"

def download_youtube_content(url, output_dir=DEFAULT_OUTPUT_DIR, audio_only=False):
    """
    Downloads content from YouTube using yt-dlp.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Base command
    cmd = [
        "yt-dlp",
        "--print", "filename",
        "--no-playlist" if "list=" not in url else "--yes-playlist",
        "--output", f"{output_dir}/%(id)s.%(ext)s",
        "--write-info-json",
        "--restrict-filenames",
    ]

    if audio_only:
        cmd += ["-x", "--audio-format", "wav", "--audio-quality", "0"]
    else:
        # Preferred format: mp4 (good for generic compatibility)
        cmd += ["-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"]

    cmd.append(url)

    logger.info(f"Starting download: {url}")
    try:
        proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("Download completed successfully.")
        
        # Log the filename if captured
        if proc.stdout:
            for line in proc.stdout.splitlines():
                if line.strip():
                    logger.info(f"Downloaded: {line.strip()}")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Download failed for {url}")
        logger.error(f"Error: {e.stderr}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download YouTube videos/playlists for processing.")
    parser.add_argument("url", help="YouTube URL (Video or Playlist)")
    parser.add_argument("--out", "-o", default=str(DEFAULT_OUTPUT_DIR), help="Output directory")
    parser.add_argument("--audio", "-a", action="store_true", help="Download audio only (WAV)")
    
    args = parser.parse_args()
    
    try:
        download_youtube_content(args.url, Path(args.out), args.audio)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        exit(1)
