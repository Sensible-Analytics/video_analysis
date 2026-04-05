# Architectural Guardrails

> **Mandukya AI** — Smart Video Lesson Companion  
> A locally-run knowledge extraction pipeline for educational videos.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Pipeline (Backend)** | Python 3.10+ | Core processing: download, transcribe, index, search |
| **Audio Transcription** | Whisper.cpp | Local audio-to-text transcription |
| **Video Processing** | FFmpeg / ffmpeg-python | Frame extraction, slide detection |
| **Knowledge Graph** | Cognee + Kùzu + LanceDB | RDBMS, Vector, and Graph databases |
| **LLM / Reasoning** | Ollama | Local LLM for insights, diagrams, slide generation |
| **Frontend** | React 18 + React Three Fiber + Three.js | Split-Helix 3D UI |
| **UI Components** | Lucide React | Icon library |
| **Presentation** | Reveal.js | Generated slideshow output |
| **Package Management** | pip (Python), npm (Frontend) | Dependency management |
| **Task Runner** | Make | Unified CLI (`make setup`, `make download`, etc.) |

---

## Architectural Principles

### 1. Local-First, Privacy-First
- **No cloud dependencies** for core functionality. All processing runs locally.
- Ollama, Whisper.cpp, and Cognee all operate on the user's machine.
- Never introduce cloud API calls without explicit ADR approval.

### 2. Modular Pipeline Architecture
The system follows a four-stage pipeline:

```
Perception → Memory → Reasoning → Presentation
```

Each stage is **independently testable** and communicates via **file-based artifacts** (transcripts, frames, slides) and **database records** (Cognee knowledge graph).

| Stage | Input | Output |
|-------|-------|--------|
| **Perception** | YouTube URL / Video file | Transcripts (`.txt`), Frames (`.png`) |
| **Memory** | Transcripts | Knowledge Graph (RDBMS + Vector + Graph DB) |
| **Reasoning** | Knowledge Graph + Context | Insights, Mermaid diagrams, Slide content |
| **Presentation** | Slide content | Reveal.js HTML slides |

### 3. File-Based Communication
- Pipeline stages communicate through **files on disk**, not in-memory state.
- `transcripts/` — Audio transcription outputs
- `downloads/` — Downloaded video/audio files
- `slides/` — Generated Reveal.js presentations
- `audio/` — Extracted audio tracks
- `diagrams/` — Generated Mermaid/visual diagrams

### 4. Frontend-Backend Separation
- **Backend**: Python pipeline scripts (`process_pipeline.py`, `indexer.py`, `search.py`, etc.)
- **Frontend**: React SPA in `frontend/` directory
- Communication: File system + database queries (no REST API layer currently)
- The frontend reads from the same data stores the pipeline writes to.

---

## Directory Structure

```
video_analysis/
├── pipeline/              # Pipeline modules
├── transcripts/           # Generated transcripts
├── downloads/             # Downloaded media
├── slides/                # Generated Reveal.js slides
├── audio/                 # Extracted audio files
├── diagrams/              # Generated diagrams
├── frontend/              # React SPA (Split-Helix UI)
│   ├── src/
│   ├── public/
│   └── package.json
├── docs/                  # Documentation
│   ├── architecture/      # Architecture diagrams
│   └── adr/               # Architecture Decision Records
├── tests/                 # Test suite
├── process_pipeline.py    # Main pipeline orchestrator
├── indexer.py             # Knowledge graph indexing
├── search.py              # Semantic search
├── downloader.py          # YouTube download
├── slide.py               # Slide generation
├── generate_slide.py      # Slide generation helper
├── cognee_setup.py        # Cognee configuration
├── cognee_indexer.py      # Cognee indexing logic
├── setup_wizard.py        # Interactive setup
├── requirements.txt       # Python dependencies
├── Makefile               # Task runner
└── ARCHITECTURAL_GUARDRAILS.md  # This file
```

---

## Guardrails

### Pipeline Guardrails
1. **No blocking UI calls** — Pipeline scripts must be non-interactive (except `setup_wizard.py`).
2. **Idempotent operations** — Re-running a stage should not duplicate data.
3. **Graceful degradation** — If Ollama is unavailable, pipeline should fail with clear error, not silently skip.
4. **Logging** — Use `pipeline.log` for structured logging. No `print()` statements in production code.

### Frontend Guardrails
1. **No backend server required** — Frontend reads directly from file system / database.
2. **React 18 only** — Do not upgrade React major version without ADR.
3. **Three.js for 3D** — All 3D visualization uses React Three Fiber + Three.js.
4. **No external API calls** — Frontend must not call external services.

### Data Guardrails
1. **Cognee is the source of truth** — Knowledge graph data lives in Cognee-managed databases.
2. **Files are artifacts** — Transcripts, slides, and diagrams are outputs, not inputs (except for pipeline consumption).
3. **No hardcoded paths** — Use `.env` configuration for all file paths.

### Dependency Guardrails
1. **Local-first dependencies** — Prefer local tools (Whisper.cpp, Ollama) over cloud APIs.
2. **Pin major versions** — `requirements.txt` and `package.json` should pin major versions.
3. **New dependency requires ADR** — Any new external service or major library addition needs an Architecture Decision Record.

---

## Running the System

```bash
# Setup (one-time)
make setup

# Download a lesson
make download URL="https://www.youtube.com/playlist?list=..."

# Run the pipeline
make run

# Build knowledge graph
make index

# Search
make search QUERY="your query"

# Frontend
cd frontend && npm start
```

---

## Decision Records

All architectural decisions are tracked in `docs/adr/`.  
See `docs/adr/TEMPLATE.md` for the format.

---

## C4 Diagrams

System architecture diagrams are in `docs/architecture/diagrams/` in Mermaid format.
Start with `system-context.mmd` for the C4 System Context view.
