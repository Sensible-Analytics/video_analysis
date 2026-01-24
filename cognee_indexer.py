#!/usr/bin/env python3
"""
Uses Cognee to index transcripts into RDBMS, Vector, and Graph databases.
Enables cross-lesson entity resolution and relationship extraction.
"""

import os
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
import cognee

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

WORKDIR = Path.cwd()
TRANSCRIPT_DIR = WORKDIR / "transcripts"

async def run_indexing_pipeline():
    # 1. Load configuration
    load_dotenv(WORKDIR / ".env")
    
    # Configure Cognee for local execution explicitly
    cognee.config.set_llm_provider("ollama")
    cognee.config.set_llm_model("qwen2.5-coder:7b")
    cognee.config.set_llm_endpoint("http://localhost:11434")
    cognee.config.set_vector_db_provider("lancedb")
    
    if not TRANSCRIPT_DIR.exists():
        logger.error(f"Transcript directory not found: {TRANSCRIPT_DIR}")
        return

    # 2. Get all text transcript files
    transcript_files = list(TRANSCRIPT_DIR.glob("*.txt"))
    logger.info(f"Processing {len(transcript_files)} transcripts via Cognee...")

    for txt_file in transcript_files:
        logger.info(f"Ingesting: {txt_file.name}")
        
        # Ingest text content into Cognee
        # datasets serve as partitions in Cognee
        await cognee.add(
            data = str(txt_file),
            dataset_name = "mandukya_upanishad"
        )

    # 3. Cognify: Run the knowledge extraction pipeline
    # This identifies entities, resolves relationships, and builds the graph + vector index.
    logger.info("Starting Cognee Cognify pipeline (this may take a while)...")
    try:
        await cognee.cognify(dataset_name = "mandukya_upanishad")
        logger.info("Cognee indexing complete.")
    except Exception as e:
        logger.error(f"Cognify pipeline failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_indexing_pipeline())
