from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os

# Ensure the parent directory is in the path to import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.retrieval.hybrid_retriever import HybridRetriever

app = FastAPI(title="Arabic Grammar Assistant API")

try:
    retriever = HybridRetriever(
        db_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/chroma_db")),
        graph_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/graph.graphml")),
        config_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "../../config"))
    )
except Exception as e:
    print(f"Warning: Could not initialize retriever: {e}")
    retriever = None

class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    answer: str

@app.post("/ask", response_model=AnswerResponse)
async def ask_question(req: QuestionRequest):
    if retriever is None:
        raise HTTPException(status_code=503, detail="Retriever is not initialized. Please ensure the pipeline has been run first.")
        
    answer = retriever.generate_answer(req.question)
    return AnswerResponse(answer=answer)

@app.get("/health")
async def health_check():
    return {"status": "ok", "retriever_loaded": retriever is not None}
