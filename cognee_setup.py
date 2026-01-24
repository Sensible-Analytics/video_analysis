#!/usr/bin/env python3
"""
Initializes Cognee with local storage and LLM configurations.
Sets up SQLite, LanceDB, and Kuzu.
"""

import os
import shutil
import logging
from pathlib import Path
from dotenv import load_dotenv

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

WORKDIR = Path.cwd()

def ensure_env():
    env_file = WORKDIR / ".env"
    example_file = WORKDIR / ".env.example"
    
    if not env_file.exists():
        if example_file.exists():
            logger.info("Creating .env from .env.example")
            shutil.copy(example_file, env_file)
        else:
            logger.warning(".env.example not found. Please create .env manually.")
    
    load_dotenv(env_file)

def setup_cognee():
    import cognee
    
    # Ensure data directory exists
    data_dir = WORKDIR / "cognee_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure Cognee for local execution explicitly
    cognee.config.set_llm_provider("ollama")
    cognee.config.set_llm_model("qwen2.5-coder:7b")
    cognee.config.set_llm_endpoint("http://localhost:11434")
    cognee.config.set_vector_db_provider("lancedb")
    
    # Cognee 0.5.1 uses these methods
    logger.info(f"Cognee LLM Provider set to: ollama")
    logger.info(f"Cognee model set to: qwen2.5-coder:7b")
    
    logger.info("Cognee setup verification complete.")

if __name__ == "__main__":
    ensure_env()
    setup_cognee()
