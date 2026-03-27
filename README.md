<div align="center">

# 🧘 Mandukya AI

### **Turn Videos Into Deep Understanding**

**AI-powered video study companion — your personal lecture assistant**

[![🚀 Try It Now](https://img.shields.io/badge/Get_Started-00C7B7?style=for-the-badge&logo=github&logoColor=white)](#-getting-started-technical-setup)
[![💻 GitHub](https://img.shields.io/badge/View_Code-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Sensible-Analytics/video_analysis)

</div>

---

## 🤯 Watched a 2-Hour Lecture and Remembered Nothing?

If you're serious about learning, you know the pain:
- ❌ Taking notes while watching is impossible
- ❌ Can't find that one concept from last week
- ❌ Re-watching hours of content to find a specific moment
- ❌ No way to search what was said in a video
- ❌ Your notes don't connect concepts together

**What if AI could watch the videos for you, take perfect notes, and help you understand the big picture?**

---

## ✨ What Mandukya AI Does

### 🎯 **Automatic Transcription**
Upload any video — lectures, YouTube, courses:
- Whisper AI speech-to-text (super accurate)
- Speaker identification
- Timestamped transcript
- Export as subtitles

**Searchable video content.**

### 📸 **Smart Visual Capture**
- Detects slide changes automatically
- Screenshots key diagrams and charts
- Captures important visual moments
- OCR extracts text from slides

**See the highlights without watching.**

### 🧠 **Knowledge Graph**
This is the magic:
- Extracts concepts from the content
- Connects related ideas together
- Shows you the "big picture"
- Find hidden relationships

**Not just notes — actual understanding.**

### 🎬 **Interactive Presentations**
- Auto-generated Reveal.js slides
- Transcript snippets with timestamps
- Jump to exact moments in video
- Review key points quickly

**Navigate 2-hour lectures in 10 minutes.**

### 🔍 **Semantic Search**
Ask questions like:
- "What did they say about consciousness?"
- "Find the part about the four states"
- "Show me all diagrams"
- "Summarize the main teaching"

**AI understands the content, not just the words.**

---

## 🔒 Privacy First

**Your videos NEVER leave your computer:**
- ✅ **100% local processing** — No cloud, no subscriptions
- ✅ **Your data stays yours** — Everything on your machine
- ✅ **Open source** — Audit every line of code
- ✅ **Offline capable** — Works without internet

**Perfect for sensitive or private content.**

---

## 🚀 Get Started

### Prerequisites
- [Ollama](https://ollama.ai/) installed and running
- [Whisper.cpp](https://github.com/ggerganov/whisper.cpp) compiled locally
- Python 3.10+

### Quick Setup
```bash
# Clone
git clone https://github.com/Sensible-Analytics/video_analysis.git
cd video_analysis

# Setup
make setup

# Add your Whisper paths to .env
```

### Usage Pipeline

**Step 1: Download a Video**
```bash
make download URL="https://www.youtube.com/watch?v=..."
```

**Step 2: Process & Transcribe**
```bash
make run
```

**Step 3: Launch the Split-Helix UI**
```bash
cd frontend
npm install
npm start
```

**Step 4: Build Knowledge Graph**
```bash
make index
```

**Step 5: Search & Discover**
```bash
make search QUERY="What are the main concepts?"
```

**That's it. Deep understanding in minutes.**

---

## 🎯 Perfect For

**Students**
> "Upload lecture recordings. Get searchable notes. Study 3x faster."

**Researchers**
> "Interview transcripts without manual transcription. Find quotes instantly."

**Philosophy/Spiritual Seekers**
> "Deep study of philosophical texts — connect concepts across lectures."

**Online Learners**
> "Coursera, YouTube tutorials, conference talks — make them all searchable."

---

## 🛠️ Architecture

```
Video Input → Whisper.cpp → Transcript
           → FFmpeg → Visual Frames
           ↓
     Cognee AI → Knowledge Graph
           ↓
     Ollama LLM → Insights & Diagrams
           ↓
     Split-Helix UI → Interactive Experience
```

**Privacy-first. Local processing. Deep understanding.**

---

## 💡 What Makes This Different

**Other video tools:**
- Upload to their servers ❌
- Monthly subscription ❌
- Basic transcripts only ❌
- No concept connections ❌

**Mandukya AI:**
- Runs on YOUR computer ✅
- Free forever ✅
- Knowledge graphs + transcripts ✅
- Connects concepts automatically ✅

---

## 🎓 Originally Built For

This tool was created for deep study of the **Mandukya Upanishad** — exploring the four states of consciousness (waking, dreaming, deep sleep, pure consciousness).

But it works beautifully for ANY educational content:
- University lectures
- YouTube tutorials
- Conference talks
- Online courses
- Interview recordings

---

## 🛠️ Tech Stack

- **Whisper.cpp** — Local speech recognition
- **Ollama** — Local LLM for insights
- **Cognee** — Knowledge graph generation
- **FFmpeg** — Video processing
- **Python** — Backend processing
- **React** — Split-Helix UI

---

## 🤝 Built By

**[Sensible Analytics](https://www.sensibleanalytics.co)** — AI that respects your privacy

Want custom AI learning tools? [Let's talk](mailto:hello@sensibleanalytics.co).

---

<div align="center">

**Start understanding deeper.**

[🚀 Get Started](#-getting-started-technical-setup) · [⭐ Star on GitHub](https://github.com/Sensible-Analytics/video_analysis)

</div>

---

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
