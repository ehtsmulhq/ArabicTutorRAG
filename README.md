# Arabic Grammar Teaching Assistant — GraphRAG + Local LLM

## Overview
A Retrieval-Augmented Generation (RAG) system that teaches Arabic grammar using a knowledge graph. It grounds all facts in Dr. V. Abdur Rahim's "Madinah Arabic" book series and explains them in the teaching style of Br. Asif.

## Tech Stack
- **Local LLM:** Ollama (Qwen2.5-7B-Instruct or Llama-3.1-8B-Instruct)
- **Embeddings:** ChromaDB (local default embedding)
- **Graph Store:** NetworkX
- **Data Parsing:** PyMuPDF (PDFs) and Whisper (Videos)
- **Backend:** FastAPI
- **Frontend:** Streamlit

## Setup Instructions

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: PyTorch and Whisper may need specific configurations depending on your OS/GPU (CUDA, MPS).*

2. **Start Local LLM:**
   Make sure Ollama is installed and running, then pull your preferred model:
   ```bash
   ollama run qwen2.5:7b
   ```

3. **Provide Raw Data:**
   - Drop your Madinah Arabic PDFs into `data/raw/pdf`
   - Drop Br. Asif's video files into `data/raw/video`

## Pipeline Execution

Run the scripts sequentially to build your hybrid GraphRAG store.

**Phase 1: Ingestion & Chunking**
```bash
python src/ingestion/pdf_parser.py
python src/ingestion/video_transcriber.py
python src/ingestion/chunker.py
```

**Phase 2: Extraction**
```bash
python src/extraction/entity_extractor.py
python src/extraction/relation_extractor.py
```

**Phase 3: Graph Building**
```bash
python src/graph/graph_builder.py
```

## Running the App

1. **Start Backend (FastAPI):**
   ```bash
   uvicorn src.api.main:app --reload --port 8000
   ```

2. **Start Frontend (Streamlit):**
   ```bash
   streamlit run src/ui/app.py
   ```

## Constraints & Future Improvements
- **Hardware:** All extraction uses local models. If your GPU has limited VRAM, change the Whisper model to `"base"` or `"tiny"` in `video_transcriber.py` and use a smaller quantized Ollama model.
- **Deduplication:** Entity deduplication is currently simple. Fuzzy matching should be added in later phases.
"# ArabicTutorRAG" 
