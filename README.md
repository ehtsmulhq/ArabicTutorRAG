# 🕌 Arabic Grammar Teaching Assistant — GraphRAG + Local LLM

> A Hybrid **Graph**RAG system that teaches Madinah Arabic grammar with grounded facts, zero hallucination, and a custom AI persona.

---

## 📖 What is this?

This project is an AI-powered Arabic grammar tutor built for **English-speaking students** studying the **Madinah Arabic curriculum** (by Dr. V. Abdur Rahim).

Instead of relying on a generic chatbot, this system:

1. **Extracts** grammar rules, vocabulary, and teaching examples from Br. Asif's YouTube lecture transcripts.
2. **Stores** them in a **Knowledge Graph** (NetworkX) + **Vector Database** (ChromaDB) — a Hybrid GraphRAG architecture.
3. **Retrieves** the exact relevant facts when a student asks a question.
4. **Generates** a perfectly accurate answer in Br. Asif's teaching style via a local LLM (Qwen2.5:7b).
5. **Guards** against prompt injection and out-of-scope requests (e.g., "write me Python code") via a One-Pass JSON Security Shield.

---

## 🏗️ Architecture

```
Student Question
      │
      ▼
┌─────────────────────────────────────┐
│         Security Shield             │  ← Blocks non-Arabic requests
│     (One-Pass JSON Classifier)      │
└─────────────────────────────────────┘
      │ Safe? ✅
      ▼
┌─────────────┐    ┌──────────────────┐
│  ChromaDB   │    │  NetworkX Graph  │
│(Vector Sim) │    │ (Relationships)  │
└─────────────┘    └──────────────────┘
      │                    │
      └────────┬───────────┘
               ▼
        ┌─────────────┐
        │  Local LLM  │  ← qwen2.5:7b via Ollama
        │  (Qwen2.5)  │
        └─────────────┘
               │
               ▼
        Br. Asif's Answer 🎓
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| **Local LLM** | [Ollama](https://ollama.ai) — `qwen2.5:7b` |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` |
| **Vector Store** | [ChromaDB](https://www.trychroma.com/) (local, persistent) |
| **Knowledge Graph** | [NetworkX](https://networkx.org/) + JSON persistence |
| **Graph Extraction** | Google Gemini 3.5 Flash Lite API |
| **Data Source** | YouTube transcripts (Br. Asif's Madinah Arabic playlist) |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/) |
| **Frontend (Dev)** | [Streamlit](https://streamlit.io/) |

---

## 🚀 Quick Start

### 1. Prerequisites

- **Python 3.10+**
- **[Ollama](https://ollama.ai/download)** installed and running
- A **Gemini API key** (free tier works) for the graph extraction phase

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

```bash
# Copy the example file and fill in your key
cp .env.example .env
```

Then edit `.env`:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Pull the Local LLM

```bash
ollama pull qwen2.5:7b
```

---

## 🔧 Pipeline Execution

Run the scripts in this exact order to build the full knowledge store from scratch.

### Phase 1 — Ingest Transcripts

Fetches transcripts from the Br. Asif YouTube playlist and cleans them:

```bash
python src/ingestion/youtube_transcriber.py
python src/ingestion/transcript_cleaner.py
python src/ingestion/chunker.py
```

> **Output:** `data/processed/all_chunks.json` — 848 clean transcript chunks.

### Phase 2 — Extract Knowledge Graph

Uses the Gemini API to extract grammar entities and relationships from the chunks:

```bash
python src/extraction/graph_builder_gemini.py
```

> **Output:** `data/processed/knowledge_graph_gemini.json`  
> ⚠️ This step consumes Gemini API quota. Processing 848 chunks in batches of 5 takes ~170 API calls.

### Phase 3 — Build Vector Database

Embeds all chunks locally into a persistent ChromaDB vector store:

```bash
python src/retrieval/build_vector_db.py
```

> **Output:** `data/processed/chroma_db/` — 848 embedded vectors.

---

## 💬 Running the Tutor

### Option A — Terminal Chat (Quickest)

```bash
python src/retrieval/query_engine.py
```

### Option B — Streamlit Web UI

```bash
streamlit run src/ui/app.py
```

The Streamlit UI renders Arabic text correctly in the browser (unlike the Windows terminal, which can display Arabic right-to-left characters backwards).

### Option C — FastAPI Backend

```bash
uvicorn src.api.main:app --reload --port 8000
```

Interactive API docs available at: `http://localhost:8000/docs`

---

## 📂 Project Structure

```
ArabicTutorRAG/
├── config/
│   ├── schema.yaml          # Entity type definitions (Lesson, GrammarRule, etc.)
│   └── prompts.yaml         # LLM extraction prompt templates
├── data/
│   ├── raw/
│   │   ├── pdf/             # Drop Madinah Arabic PDFs here
│   │   └── video/           # Drop lecture video files here (optional)
│   └── processed/
│       ├── all_chunks.json              # 848 clean transcript chunks
│       ├── knowledge_graph_gemini.json  # Extracted knowledge graph
│       └── chroma_db/                   # Local vector database (git-ignored)
├── src/
│   ├── ingestion/           # Phase 1: Transcript download, cleaning, chunking
│   ├── extraction/          # Phase 2: Entity & relationship extraction
│   ├── retrieval/           # Phase 3: Hybrid GraphRAG query engine
│   ├── api/                 # FastAPI backend
│   └── ui/                  # Streamlit frontend
├── .env.example             # Environment variable template
├── requirements.txt
└── README.md
```

---

## 🛡️ Security Features

- **One-Pass JSON Security Shield:** Every query is evaluated for safety by the same LLM call that generates the answer. Out-of-scope requests (math, code, unrelated topics) are blocked before any database is searched.
- **No secrets in repo:** `.env`, `cookies.txt`, ChromaDB binaries, and large PDFs are all git-ignored.

---

## ⚠️ Known Limitations

| Issue | Details |
|---|---|
| **Arabic Script** | The local 7B model sometimes outputs improperly connected Arabic letters. Use the Web UI (Streamlit) for correct RTL rendering. |
| **Hallucination Risk** | `qwen2.5:7b` can hallucinate grammar facts not in its retrieved context. For production use, switch to a cloud LLM (Gemini / OpenAI / Groq). |
| **Slow on CPU** | Without a GPU, generation may take 60–120 seconds per query. Consider a smaller model (`qwen2.5:3b`) or a cloud API. |
| **Graph Coverage** | The current graph was extracted from Book 1 transcripts only. Books 2 and 3 can be added by re-running the pipeline with more videos. |

---

## 🗺️ Roadmap

- [x] Phase 1: YouTube transcript ingestion & cleaning
- [x] Phase 2: Hybrid GraphRAG extraction (NetworkX + ChromaDB)
- [x] Phase 3: CLI query engine with security shield
- [x] Phase 4: Streamlit Web UI
- [ ] Phase 5: React/Next.js frontend + FastAPI production backend
- [ ] Phase 6: QLoRA fine-tuning on extracted Q&A dataset
- [ ] Phase 7: Multi-book ingestion (Madinah Books 2 & 3)

---

## 📄 License

This project is for educational purposes. The Madinah Arabic curriculum content is based on the works of Dr. V. Abdur Rahim (public domain). Video transcripts sourced from Br. Asif's YouTube channel for non-commercial educational use only.
