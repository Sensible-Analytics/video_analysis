# 🧘 Mandukya AI: Smart Video Lesson Companion

Welcome! **Mandukya AI** is a powerful, locally-run tool designed to help you get the most out of educational videos and lectures—originally created for deep study of the Mandukya Upanishad, but useful for any topic. 

## 🌟 What Does It Do?
Instead of just watching a video, this application acts as your advanced study companion. It automatically:
- **Listens and Transcribes:** Turns the video's audio into written text.
- **Captures Visuals:** Automatically takes screenshots whenever the presenter changes a slide.
- **Connects Concepts:** Builds a "Knowledge Graph" (a web of ideas) to help you understand how different topics in the lesson relate to each other.
- **Creates Interactive Presentations:** Generates a ready-to-view slideshow containing the diagrams, transcripts, and exact YouTube video timestamps so you can easily review the material.

All of this happens **privately on your own computer**—no cloud subscriptions required!

## 🚀 Getting Started (Technical Setup)

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
make run  # Start the background brain
cd frontend && npm install && npm start # Launch the Split-Helix UI
```
and generates Reveal.js slides in the `slides/` directory.

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
