#!/usr/bin/env python3
"""
Indexes transcript chunks into a local vector store using Ollama embeddings.
Enables semantic search across all processed lessons.
"""

import os
import json
import logging
import requests
import numpy as np
from pathlib import Path
from typing import List, Dict

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Constants
WORKDIR = Path.cwd()
TRANSCRIPT_DIR = WORKDIR / "transcripts"
INDEX_FILE = WORKDIR / "vector_index.json"
EMBEDDING_MODEL = "nomic-embed-text" # Great local embedding model
OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"

def get_embedding(text: str) -> List[float]:
    payload = {
        "model": EMBEDDING_MODEL,
        "prompt": text
    }
    try:
        r = requests.post(OLLAMA_EMBED_URL, json=payload, timeout=60)
        r.raise_for_status()
        return r.json()["embedding"]
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return []

def index_transcripts():
    if not TRANSCRIPT_DIR.exists():
        logger.error(f"Transcript directory not found: {TRANSCRIPT_DIR}")
        return

    index_data = []
    
    # Check if index already exists to avoid re-indexing everything
    if INDEX_FILE.exists():
        with open(INDEX_FILE, "r") as f:
            try:
                index_data = json.load(f)
            except json.JSONDecodeError:
                index_data = []

    indexed_files = {item["file"] for item in index_data}
    
    transcript_files = list(TRANSCRIPT_DIR.glob("*.txt"))
    logger.info(f"Checking {len(transcript_files)} transcript files...")

    for txt_file in transcript_files:
        if txt_file.name in indexed_files:
            continue
            
        logger.info(f"Indexing: {txt_file.name}")
        content = txt_file.read_text(encoding="utf-8")
        
        # Simple chunking for indexing (can be improved)
        chunks = content.split("\n\n") # Assume segments or paragraphs
        for i, chunk in enumerate(chunks):
            chunk = chunk.strip()
            if len(chunk) < 50: # Skip very short snippets
                continue
                
            embedding = get_embedding(chunk)
            if embedding:
                index_data.append({
                    "file": txt_file.name,
                    "chunk_id": i,
                    "text": chunk,
                    "embedding": embedding
                })

    # Save the index
    with open(INDEX_FILE, "w") as f:
        json.dump(index_data, f)
    
    logger.info(f"Indexing complete. Total entries in index: {len(index_data)}")

if __name__ == "__main__":
    index_transcripts()
