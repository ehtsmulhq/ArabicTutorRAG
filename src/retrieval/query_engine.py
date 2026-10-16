import json
import requests
import chromadb
from chromadb.utils import embedding_functions
import networkx as nx
from pathlib import Path
import argparse

# Try to load RTL and Arabic shaping libraries for the terminal
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    def format_terminal_text(text):
        # Reshape Arabic letters to connect them, then apply Bi-Directional algorithm
        reshaped_text = arabic_reshaper.reshape(text)
        return get_display(reshaped_text)
except ImportError:
    def format_terminal_text(text):
        return text

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CHROMA_DIR = BASE_DIR / "data" / "processed" / "chroma_db"
GEMINI_GRAPH = BASE_DIR / "data" / "processed" / "knowledge_graph_gemini.json"
OLLAMA_GRAPH = BASE_DIR / "data" / "processed" / "knowledge_graph.json"

GRAPH_PATH = GEMINI_GRAPH if GEMINI_GRAPH.exists() else OLLAMA_GRAPH

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"

class ArabicTutorEngine:
    def __init__(self):
        print("Loading Vector Database...")
        self.chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        self.collection = self.chroma_client.get_collection(name="madinah_arabic", embedding_function=self.ef)
        
        print(f"Loading Knowledge Graph from {GRAPH_PATH.name}...")
        try:
            with open(GRAPH_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.graph = nx.node_link_graph(data)
        except Exception as e:
            print(f"Error loading graph: {e}")
            self.graph = nx.DiGraph()

    def get_graph_context(self, question: str) -> str:
        question_lower = question.lower()
        matched_nodes = []
        for node_id, data in self.graph.nodes(data=True):
            name = str(data.get("name", "")).lower()
            if name and name in question_lower and len(name) > 3:
                matched_nodes.append(node_id)
                
        if not matched_nodes:
            return "No specific graph concepts explicitly triggered."
            
        graph_context = []
        for node in matched_nodes:
            node_data = self.graph.nodes[node]
            graph_context.append(f"Concept: {node_data.get('name')} ({node_data.get('type')}) - {node_data.get('description')}")
            for neighbor in self.graph.successors(node):
                edge_data = self.graph.get_edge_data(node, neighbor)
                neighbor_data = self.graph.nodes[neighbor]
                graph_context.append(f"  -> {edge_data.get('type')}: {neighbor_data.get('name')} (Rationale: {edge_data.get('rationale')})")
        return "\\n".join(graph_context)

    def get_vector_context(self, question: str, k=3) -> str:
        results = self.collection.query(query_texts=[question], n_results=k)
        chunks = results.get("documents", [[]])[0]
        sources = results.get("metadatas", [[]])[0]
        context_str = ""
        for chunk, meta in zip(chunks, sources):
            context_str += f"[Source: {meta.get('source')}]\\n{chunk}\\n\\n"
        return context_str

    def query(self, question: str):
        print("\\nSearching transcripts (Vector DB)...")
        vector_context = self.get_vector_context(question)
        
        print("Searching relationships (Knowledge Graph)...")
        graph_context = self.get_graph_context(question)
        
        prompt = f'''You are Br. Asif, a friendly and expert teacher of Madinah Arabic. 
A student has asked you a question. Use the provided context from your video transcripts and knowledge graph to answer them.
Speak in a distinct, encouraging, and clear teaching style. You may occasionally use terms like "Insha'Allah", but DO NOT overuse filler phrases like "brothers and sisters". Be natural and focus strictly on the grammar.

CRITICAL LANGUAGE RULE (MUST OBEY):
Your ENTIRE conversational response MUST be written in ENGLISH. You are teaching English-speaking students!
DO NOT write your explanations in Arabic. DO NOT translate your sentences into Arabic.
The ONLY time you should use Arabic script is when quoting a specific vocabulary word or grammar example (e.g., "The word for book is كِتَابٌ").

CRITICAL INSTRUCTION FOR ARABIC TEXT: 
Whenever you do mention that specific Arabic word or example, you MUST write it in actual Arabic script with FULL vowel signs (Tashkeel/Harakat) and double vowel signs (Tanween). For example, write مُحَمَّدٌ instead of just "muhammadun".

CRITICAL GUARDRAIL & OUTPUT FORMAT:
You must output STRICTLY valid JSON.
If the student asks you to write code, do math, or talk about subjects outside of Arabic grammar, you MUST flag "is_safe" as false.
If the question is safely about Arabic, set "is_safe" to true and write your answer.

Output Schema:
{{
  "is_safe": true or false,
  "answer": "Your complete answer written ENTIRELY IN ENGLISH. Leave blank if is_safe is false."
}}

If the answer is not in the context, do not guess-just explain what you can based on the text provided.

--- TRANSCRIPT CONTEXT ---
{vector_context}

--- KNOWLEDGE GRAPH CONTEXT ---
{graph_context}

--- STUDENT QUESTION ---
{question}
'''
        
        print(f"Generating answer via local {MODEL_NAME} (One-Pass JSON)...\\n")
        print("================= BR. ASIF'S ANSWER =================")
        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL_NAME, 
                    "prompt": prompt, 
                    "stream": False,
                    "format": "json"
                },
                timeout=120
            )
            response.raise_for_status()
            json_text = response.json().get("response", "")
            
            try:
                result = json.loads(json_text)
                if not result.get("is_safe", True) or str(result.get("is_safe")).lower() == "false":
                    print("Brothers and sisters, I am an Arabic language teacher. I do not write code, solve math, or discuss outside topics. Let us focus on our Arabic lesson, Insha'Allah!")
                else:
                    answer = result.get("answer", "")
                    print(format_terminal_text(answer))
            except json.JSONDecodeError:
                # Fallback if local model fails to output clean JSON
                print("Error: The local model failed to output valid JSON. Raw output:")
                print(json_text)
                    
            print("\\n=====================================================\\n")
        except Exception as e:
            print(f"\\nError communicating with Ollama: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ask", type=str, help="The question to ask")
    args = parser.parse_args()

    engine = ArabicTutorEngine()
    if args.ask:
        engine.query(args.ask)
    else:
        print("\\nWelcome to the Madinah Arabic GraphRAG Tutor!")
        print("Type 'quit' or 'exit' to stop.\\n")
        while True:
            try:
                q = input("\\nStudent: ")
                if q.lower() in ['quit', 'exit', 'q']: break
                if not q.strip(): continue
                engine.query(q)
            except KeyboardInterrupt:
                break

if __name__ == "__main__":
    main()
