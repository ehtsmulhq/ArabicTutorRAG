## Goal Description
The objective is to transition the "Arabic Grammar Teaching Assistant" from a local, single-user prototype to a scalable, commercial B2C SaaS platform. This plan incorporates the deep-dive perspectives of the entire Dev Team (PM, Architect, Developer, and QA) to ensure business viability, structural maintainability, technical feasibility, and rigorous quality assurance.

The core of this transformation involves a structural refactor into a domain-driven architecture (`core/`, `pipeline/`, `app/`) to eliminate technical debt and hardcoded paths, paving the way for cloud deployment and multi-tenant user access.

---

## Dev Team Deep Dives (Context)

### 1. PM Deep Dive: Monetization & Go-To-Market
*   **Target Niche:** Classical/Quranic Arabic learners studying the Madinah curriculum (a highly motivated, underserved market compared to conversational Arabic apps).
*   **Business Model:** B2C Freemium. Free tier with basic search and limited queries; Pro tier ($5-$10/mo) with unlimited queries and personalized spaced-repetition quizzes based on user weak points.
*   **GTM Strategy:** Community seeding in highly specific Islamic/Arabic learning subreddits, Discord servers, and partnerships with YouTube creators teaching the curriculum.
*   **Product Roadmap:** V1 (Q&A/Search) -> V2 (Automated Quizzes/Flashcards) -> V3 (Curriculum Progress Tracking).

### 2. Architect Deep Dive: Domain Separation & Cloud Infrastructure
*   **Domain Boundaries:** Splitting the monolithic `src/` directory into offline data processing (`pipeline/`) and real-time serving (`app/`), connected by shared utilities (`core/`).
*   **Infrastructure Shift:** To scale cost-effectively, the heavy Graph extraction will be run as a batch process, maintaining a "read-only global state." The retrieval engine will be scaled on CPU instances, likely requiring a shift from local Ollama to a serverless LLM provider for production inference.
*   **Data Persistence:** In-memory `NetworkX` must eventually be replaced by a persistent Graph DB (e.g., Neo4j).

### 3. Developer Deep Dive: Code Cleanup & Frontend Rewrite
*   **Import/Path Hell:** Hardcoded relative paths and duplicated code (e.g., multiple `graph_builder.py` files) must be resolved via a centralized `core/config.py`.
*   **Frontend Limitations:** Streamlit is unsuitable for a consumer-facing mobile SaaS. The UI must be rewritten in React/Next.js.
*   **Backend Scaling:** The FastAPI backend needs to be containerized (Docker), with async queues (Celery) to prevent blocking during LLM generation.

### 4. QA Deep Dive: Regression Testing & Trust
*   **Hallucination Risk:** In religious and grammatical contexts, incorrect AI answers destroy trust. Manual testing is no longer viable at scale.
*   **Golden Master Test:** Before *any* structural refactoring occurs, a baseline dataset of inputs (PDF/video) and expected outputs (Graph JSON/ChromaDB state) must be captured to mechanically assert feature parity post-refactor.
*   **Automated Evals:** Integration of a RAG evaluation framework (like Ragas) for ongoing accuracy monitoring.

---

## User Review Required
> [!IMPORTANT]
> **LLM Provider Decision:** Scaling this via a local Ollama instance (GPU dependency) will be incredibly expensive. Do you approve transitioning the production application to an API-based LLM (e.g., OpenAI, Anthropic, or Groq) while keeping Ollama for local dev?

> [!WARNING]
> **Streamlit Deprecation:** To fulfill the PM's B2C vision, Streamlit must be replaced. Do you approve building a new React/Next.js frontend?

## Open Questions
1. **Curated vs. User-Uploaded:** Will V1 of the SaaS strictly serve a curated knowledge graph built by us, or do you intend to allow users to upload their own PDFs? (Assuming Curated for this plan to keep costs low).
2. **Graph Database:** Should we immediately migrate from `NetworkX` to `Neo4j` during this structural refactor, or wait until post-launch?

---

## Proposed Changes

### 1. QA: Golden Master Test Suite
Before touching application code, we must secure the pipeline.
#### [NEW] `tests/test_golden_master.py`
A script that runs a small, predefined PDF and transcript through the current pipeline and asserts the output exactly matches a checked-in "golden" `knowledge_graph.json` and ChromaDB state.

### 2. Core: Configuration & Shared Logic
Centralize paths and LLM clients to eliminate hardcoded strings.
#### [NEW] `src/core/config.py`
```python
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = PROJECT_ROOT / "data"
    PROCESSED_DIR: Path = DATA_DIR / "processed"
    GRAPH_JSON_PATH: Path = PROCESSED_DIR / "knowledge_graph.json"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    class Config:
        env_file = ".env"

settings = Settings()
```
#### [NEW] `src/core/llm_client.py`
Centralized wrapper for Ollama/API interactions to be shared by extraction and retrieval.

### 3. Pipeline: Offline Data Processing
Consolidate the ingestion and extraction logic.
#### [MODIFY] `src/extraction/` -> `src/pipeline/extraction/`
#### [MODIFY] `src/ingestion/` -> `src/pipeline/ingestion/`
#### [DELETE] `src/extraction/graph_builder_gemini.py`
Remove unused/duplicate code. Consolidate graph building into `src/pipeline/graph_build/`.

### 4. App: Online Serving
Isolate the user-facing application layer.
#### [MODIFY] `src/api/` -> `src/app/api/`
#### [MODIFY] `src/retrieval/` -> `src/app/retrieval/`
#### [MODIFY] `src/ui/app.py`
Keep Streamlit strictly for internal admin/debugging.
#### [NEW] `frontend/`
Initialize a new Next.js or React project for the consumer-facing UI.

### 5. Infrastructure: Dockerization
#### [NEW] `Dockerfile.api`
Containerize the FastAPI service.
#### [NEW] `docker-compose.yml`
Orchestrate the API, frontend, and optionally a local Ollama instance for development.

---

## Verification Plan

### Automated Tests
1. Generate the Golden Master baseline: `python scripts/generate_golden_master.py`
2. Execute the structural refactor (moving files, updating imports to use `core.config`).
3. Run the verification suite:
   ```bash
   pytest tests/test_golden_master.py
   ```
   *Success criteria: The test passes, proving the structural changes did not alter the extraction or retrieval logic.*

### Manual Verification
1. Start the refactored FastAPI server and run queries via Swagger UI (`/docs`) to ensure the hybrid retriever accurately traverses the NetworkX graph and ChromaDB.
2. Verify that the Streamlit admin UI (and eventually the new React frontend) connects successfully to the backend endpoints.
