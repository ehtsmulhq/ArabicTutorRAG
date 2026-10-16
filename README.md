<div align="center">

# 🕌 ArabicTutorRAG

### A Hybrid GraphRAG System for Teaching Madinah Arabic Grammar

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-FF6B35?style=for-the-badge)](https://www.trychroma.com/)
[![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-black?style=for-the-badge)](https://ollama.ai)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-Educational-green?style=for-the-badge)](LICENSE)

*Grounded in Dr. V. Abdur Rahim's Madinah Arabic curriculum. Explained in Br. Asif's teaching style. Powered entirely by local AI.*

[🚀 Quick Start](#-quick-start) · [🏗️ Architecture](#️-architecture) · [📂 Project Structure](#-project-structure) · [🗺️ Roadmap](#️-roadmap)

</div>

---

## 📖 Overview

**ArabicTutorRAG** is a production-grade AI tutor built for English-speaking students of the **Madinah Arabic** curriculum. Unlike a generic chatbot that guesses at grammar rules, this system retrieves *exact facts* from a structured knowledge base built from real lecture transcripts before generating any answer.

| ✅ What it does | ❌ What it avoids |
|---|---|
| Grounds every answer in verified transcript data | Hallucinating Arabic grammar rules |
| Speaks in a consistent, encouraging teaching persona | Responding to off-topic or malicious prompts |
| Renders vowel-marked Arabic script (Tashkeel / Harakat) | Raw unvoweled Arabic that confuses beginners |
| Runs 100% locally with zero cloud dependency at inference | Sending student data to external APIs |

---

## 🏗️ Architecture

The system uses a **two-store Hybrid GraphRAG** approach. When a student asks a question, it queries both a vector similarity store *and* a knowledge graph before generating an answer.

```
                    ┌──────────────────────┐
  Student asks ───► │   Security Shield    │ ──► BLOCKED (code/math/off-topic)
                    │  One-Pass JSON Guard │
                    └──────────┬───────────┘
                               │ ✅ Safe
                    ┌──────────▼───────────┐
                    │   Hybrid Retriever   │
                    └─────────┬─┬──────────┘
                              │ │
              ┌───────────────┘ └──────────────┐
              ▼                                 ▼
    ┌──────────────────┐             ┌──────────────────────┐
    │    ChromaDB      │             │   NetworkX Graph     │
    │  Vector Search   │             │  Relationship Walk   │
    │ (Semantic Match) │             │ (1st-degree Expand)  │
    └────────┬─────────┘             └─────────┬────────────┘
             └────────────┬──────────────────────┘
                          ▼
               ┌──────────────────┐
               │  Context Block   │  ← Relevant chunks + graph edges merged
               └────────┬─────────┘
                        ▼
               ┌──────────────────┐
               │  qwen2.5:7b      │  ← Local LLM via Ollama
               │  (Ollama)        │
               └────────┬─────────┘
                        ▼
               📝  Br. Asif's Answer
```

---

## ⚙️ Tech Stack

<div align="center">

| Layer | Technology | Purpose |
|---|---|---|
| 🧠 **Local LLM** | Ollama · `qwen2.5:7b` | Answer generation |
| 🔢 **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` | Semantic encoding |
| 🗄️ **Vector Store** | ChromaDB (local, persistent) | Similarity search |
| 🕸️ **Knowledge Graph** | NetworkX + JSON | Relationship traversal |
| 🤖 **Graph Extraction** | Gemini 3.5 Flash Lite API | Entity & relation extraction |
| 📺 **Data Source** | YouTube Transcript API | Lecture transcript ingestion |
| ⚡ **Backend** | FastAPI | REST API serving |
| 🖥️ **Frontend** | Streamlit | Chat web interface |

</div>

---

## 🚀 Quick Start

### Prerequisites

Ensure the following are installed before proceeding:

- [Python 3.10+](https://www.python.org/downloads/)
- [Ollama](https://ollama.ai/download) (for local LLM inference)
- A free [Gemini API Key](https://aistudio.google.com/app/apikey) (only needed for the one-time graph extraction phase)

---

### Step 1 — Clone & Install

```bash
git clone https://github.com/ehtsmulhq/ArabicTutorRAG.git
cd ArabicTutorRAG
pip install -r requirements.txt
```

### Step 2 — Configure Environment

```bash
cp .env.example .env
```

Open `.env` and add your Gemini key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### Step 3 — Pull the Local LLM

```bash
ollama pull qwen2.5:7b
```

---

## 🔧 Pipeline Execution

Run each phase **in order** to build the full knowledge store from scratch.

```
  Transcripts  ──►  Chunks  ──►  Graph  ──►  Vectors  ──►  Query Engine
   (Phase 1)        (Phase 1)    (Phase 2)    (Phase 3)      (Phase 3)
```

### Phase 1 — Ingest & Clean Transcripts

```bash
# Download transcripts from Br. Asif's YouTube playlist
python src/ingestion/youtube_transcriber.py

# Fix Arabic phonetic misspellings and remove [Music] tags
python src/ingestion/transcript_cleaner.py

# Chunk transcripts into semantic units
python src/ingestion/chunker.py
```

> 📦 **Output:** `data/processed/all_chunks.json` — 848 clean transcript chunks

### Phase 2 — Extract Knowledge Graph

```bash
python src/extraction/graph_builder_gemini.py
```

> 📦 **Output:** `data/processed/knowledge_graph_gemini.json`
>
> ⚠️ **Note:** This step uses the Gemini API. Processing 848 chunks in batches of 5 consumes approximately 170 API calls. The free tier is sufficient.

### Phase 3 — Build Vector Database

```bash
python src/retrieval/build_vector_db.py
```

> 📦 **Output:** `data/processed/chroma_db/` — 848 locally embedded vectors (ChromaDB)

---

## 💬 Running the Tutor

Choose any of the three interfaces below:

<details>
<summary><b>🖥️ Option A — Terminal CLI (Fastest)</b></summary>

```bash
python src/retrieval/query_engine.py
```

Type your Arabic grammar question at the `Student:` prompt. Type `quit` to exit.

> **Note:** Windows terminals may render Arabic script right-to-left incorrectly. Use the Web UI for proper rendering.

</details>

<details>
<summary><b>🌐 Option B — Streamlit Web UI (Recommended)</b></summary>

```bash
streamlit run src/ui/app.py
```

Opens at `http://localhost:8501`. Arabic text is rendered correctly in all browsers.

</details>

<details>
<summary><b>⚡ Option C — FastAPI REST Backend</b></summary>

```bash
uvicorn src.api.main:app --reload --port 8000
```

Interactive Swagger docs available at `http://localhost:8000/docs`.

</details>

---

## 📂 Project Structure

```
ArabicTutorRAG/
│
├── 📁 config/
│   ├── schema.yaml              # Entity type definitions (Lesson, GrammarRule, VocabItem…)
│   └── prompts.yaml             # LLM extraction prompt templates
│
├── 📁 data/
│   ├── raw/
│   │   ├── pdf/                 # Drop Madinah Arabic PDFs here
│   │   └── video/               # Drop lecture video files here (optional)
│   └── processed/
│       ├── all_chunks.json              # 848 clean transcript chunks
│       ├── knowledge_graph_gemini.json  # Extracted knowledge graph (Gemini)
│       ├── knowledge_graph.json         # Extracted knowledge graph (local LLM fallback)
│       └── chroma_db/                   # Persistent vector store (git-ignored)
│
├── 📁 src/
│   ├── ingestion/               # Phase 1 · Transcript download, cleaning, chunking
│   │   ├── youtube_transcriber.py
│   │   ├── transcript_cleaner.py
│   │   └── chunker.py
│   ├── extraction/              # Phase 2 · Entity & relationship extraction
│   │   ├── graph_builder_gemini.py
│   │   └── graph_builder.py     # Local LLM fallback
│   ├── retrieval/               # Phase 3 · Hybrid GraphRAG query engine
│   │   ├── build_vector_db.py
│   │   ├── hybrid_retriever.py
│   │   └── query_engine.py      # Main entry point
│   ├── api/                     # FastAPI backend
│   │   └── main.py
│   └── ui/                      # Streamlit web interface
│       └── app.py
│
├── .env.example                 # Environment variable template
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🛡️ Security

This project implements a **One-Pass JSON Security Shield** at the query engine level:

1. Every student message is embedded into a single Gemini/Ollama prompt that **simultaneously** classifies intent and generates the answer.
2. The response is forced into a strict JSON schema: `{"is_safe": boolean, "answer": "..."}`.
3. If `is_safe` is `false`, the answer field is discarded and a hardcoded refusal is displayed — the model never generates code, solves math, or discusses off-topic subjects.

**This means zero extra API calls for security compared to a two-pass approach.**

---

## ⚠️ Known Limitations

| Issue | Impact | Workaround |
|---|---|---|
| **Arabic Script Quality** | Local 7B model may output improperly connected letters | Use Streamlit UI (browser handles RTL correctly) |
| **Hallucination Risk** | Small LLMs fabricate facts not in retrieved context | Switch to Gemini / OpenAI API for production |
| **CPU Inference Speed** | 60–120 sec/query without a GPU | Use `qwen2.5:3b` or a cloud API |
| **Graph Coverage** | Only Book 1 transcripts are indexed | Re-run pipeline with Books 2 & 3 videos |

---

## 📄 License

This project is built for educational purposes.

- The **Madinah Arabic curriculum** content is based on the works of **Dr. V. Abdur Rahim** (available in the public domain via lqtoronto.com).
- **Video transcripts** are sourced from Br. Asif's YouTube channel for non-commercial educational use only.
- All original code in this repository is available under the **MIT License**.

---

<div align="center">

Built with ❤️ for the Madinah Arabic learning community.

</div>
