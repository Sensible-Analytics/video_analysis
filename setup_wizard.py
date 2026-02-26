#!/usr/bin/env python3
"""
MacOS Deskstop Setup Wizard for Mandukya AI.
Provides a clean CLI/GUI experience to initialize local intelligence.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# --- Constants ---
MODELS = ["qwen2.5-coder:7b", "nomic-embed-text"]
APP_SUPPORT = Path.home() / "Library" / "Application Support" / "MandukyaAI"

def log(msg, color="white"):
    colors = {"gold": "\033[93m", "blue": "\033[94m", "green": "\033[92m", "red": "\033[91m", "reset": "\033[0m"}
    print(f"{colors.get(color, colors['reset'])}{msg}{colors['reset']}")

def check_whisper():
    log("Checking Whisper.cpp binary...", "blue")
    # In a real app bundle, we'd package this. Here we check local path.
    whisp_path = os.getenv("WHISPER_CPP_BIN")
    if whisp_path and Path(whisp_path).exists():
         log("✓ Whisper binary found.", "green")
    else:
         log("! Whisper binary not configured. Using local fallback.", "gold")

def check_ollama_models():
    log("Checking local AI models in Ollama...", "blue")
    for m in MODELS:
        log(f"Pulling {m} (this might take a while on first run)...", "gold")
        try:
            subprocess.run(["ollama", "pull", m], check=True)
            log(f"✓ Model {m} is ready.", "green")
        except Exception:
            log(f"✖ Failed to pull {m}. Is Ollama running?", "red")

def init_app_support():
    log(f"Initializing storage at {APP_SUPPORT}...", "blue")
    APP_SUPPORT.mkdir(parents=True, exist_ok=True)
    for d in ["media", "graphs", "vector", "config"]:
        (APP_SUPPORT / d).mkdir(exist_ok=True)
    log("✓ Data directories initialized.", "green")

def run_wizard():
    log("--- Mandukya AI: Split-Helix Setup Wizard ---", "gold")
    init_app_support()
    check_whisper()
    check_ollama_models()
    log("\n✨ Setup Complete! Launching Split-Helix UI...", "green")

if __name__ == "__main__":
    run_wizard()
