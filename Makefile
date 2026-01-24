# Mandukya Upanishad Video Analysis Pipeline

.PHONY: setup download run index search clean

# 🛠️ Setup the environment
setup:
	@echo "Setting up Python environment..."
	pip install -r requirements.txt
	python3 cognee_setup.py

# 📥 Download a playlist/video
# Usage: make download URL="https://youtube.com/..."
download:
	@if [ -z "$(URL)" ]; then echo "Usage: make download URL=..."; exit 1; fi
	python3 downloader.py "$(URL)"

# 🚀 Run the processing pipeline
run:
	@echo "Starting video processing pipeline..."
	python3 process_pipeline.py

# 🧠 Build the Knowledge Graph (Cognee)
index:
	@echo "Indexing transcripts into Graph, Vector, and RDBMS..."
	python3 cognee_indexer.py

# 🔍 Semantic Search
# Usage: make search QUERY="meaning of aum"
search:
	@if [ -z "$(QUERY)" ]; then echo "Usage: make search QUERY=..."; exit 1; fi
	python3 search.py "$(QUERY)"

# 🧪 Run tests
test:
	@echo "Running tests..."
	PYTHONPATH=. pytest tests/

# 🧹 Clean temporary data
clean:
	@echo "Cleaning temporary audio and transcripts..."
	rm -rf audio/*
	rm -rf slides/frames/*
	@echo "Done."
