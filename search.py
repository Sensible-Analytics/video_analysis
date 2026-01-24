#!/usr/bin/env python3
"""
Performs semantic search queries against the local vector index.
"""

import json
import logging
import requests
import argparse
import numpy as np
from pathlib import Path
from typing import List, Dict

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Constants
WORKDIR = Path.cwd()
INDEX_FILE = WORKDIR / "vector_index.json"
OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
EMBEDDING_MODEL = "nomic-embed-text"

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def get_embedding(text: str) -> List[float]:
    payload = {
        "model": EMBEDDING_MODEL,
        "prompt": text
    }
    try:
        r = requests.post(OLLAMA_EMBED_URL, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()["embedding"]
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return []

def search(query: str, top_k: int = 5):
    if not INDEX_FILE.exists():
        logger.error(f"Index file not found. Please run indexer.py first.")
        return

    with open(INDEX_FILE, "r") as f:
        index_data = json.load(f)

    query_embedding = get_embedding(query)
    if not query_embedding:
        return

    results = []
    for item in index_data:
        score = cosine_similarity(query_embedding, item["embedding"])
        results.append((score, item))

    # Sort by score descending
    results.sort(key=lambda x: x[0], reverse=True)

    logger.info(f"\nTop {top_k} results for: '{query}'\n" + "="*50)
    for score, item in results[:top_k]:
        file_name = item["file"]
        text_snippet = item["text"][:200] + "..."
        logger.info(f"Score: {score:.4f} | File: {file_name}")
        logger.info(f"Content: {text_snippet}")
        logger.info("-" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search processed lessons semantically.")
    parser.add_argument("query", help="Your search query")
    parser.add_argument("--top_k", "-k", type=int, default=5, help="Number of results to show")
    
    args = parser.parse_args()
    search(args.query, args.top_k)
