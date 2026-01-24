# 🧘 Mandukya Upanishad: Advanced Video Analysis & Knowledge Graph

An end-to-end local pipeline for transforming video lessons into an interactive, graph-augmented learning experience.

## 🌟 Key Features
- **Cognee Integration**: Transforms linear transcripts into a multidimensional Knowledge Graph using **SQLite (RDBMS)**, **LanceDB (Vector)**, and **Kuzu (Graph)**.
- **GraphRAG**: Uses graph-traversal to provide cross-lesson context to the LLM during summarization.
- **Visual Delta Analysis**: Automatically captures screenshots of slide changes in the video.
- **Interactive Slides**: Generates Reveal.js presentations with Mermaid diagrams and timestamped YouTube anchors.
- **Local First**: Everything runs on your machine using Ollama and Whisper.cpp.

## 🚀 Getting Started

### 1. Prerequisites
- [Ollama](https://ollama.ai/) installed and running.
- [Whisper.cpp](https://github.com/ggerganov/whisper.cpp) compiled locally.
- Python 3.10+

### 2. Setup
```bash
make setup
```
This will install dependencies and create your `.env` file. Edit `.env` to point to your Whisper binary and model.

### 3. Usage Pipeline

#### Step A: Download Lessons
```bash
make download URL="https://www.youtube.com/playlist?list=..."
```

#### Step B: Process Videos
```bash
make run
```
This extracts audio, transcribes it, captures screenshots, and generates Reveal.js slides in the `slides/` directory.

#### Step C: Build Knowledge Graph
```bash
make index
```
Uses **Cognee** to extract entities and relationships across all lessons, building your local RDBMS, Vector, and Graph databases.

#### Step D: Semantic Discovery
```bash
make search QUERY="The four states of consciousness"
```

## 🏗️ Architecture
The system follows a modular "Knowledge Extraction" architecture:
1. **Perception**: Whisper.cpp (Audio -> Text) & FFmpeg (Video -> Frames).
2. **Memory**: Cognee (Text -> RDBMS/Vector/Graph).
3. **Reasoning**: Ollama (Context + Chunk -> Insights/Diagrams).
4. **Presentation**: Reveal.js (Data -> UI).

---
*Created for the study of Mandukya Upanishad.*
