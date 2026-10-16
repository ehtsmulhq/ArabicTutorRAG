import streamlit as st
import json
import requests
import chromadb
from chromadb.utils import embedding_functions
import networkx as nx
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CHROMA_DIR = BASE_DIR / "data" / "processed" / "chroma_db"
GEMINI_GRAPH = BASE_DIR / "data" / "processed" / "knowledge_graph_gemini.json"
OLLAMA_GRAPH = BASE_DIR / "data" / "processed" / "knowledge_graph.json"

GRAPH_PATH = GEMINI_GRAPH if GEMINI_GRAPH.exists() else OLLAMA_GRAPH
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"

st.set_page_config(page_title="Madinah Arabic Tutor", page_icon="🕌", layout="centered")

# --- CSS for Arabic Text Formatting ---
st.markdown("""
<style>
    .arabic-text {
        font-size: 28px !important;
        font-family: 'Amiri', 'Traditional Arabic', serif;
        direction: rtl;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

# --- Initialization ---
@st.cache_resource
def load_databases():
    # Load Chroma
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = chroma_client.get_collection(name="madinah_arabic", embedding_function=ef)
    
    # Load Graph
    try:
        with open(GRAPH_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            graph = nx.node_link_graph(data)
    except Exception:
        graph = nx.DiGraph()
        
    return collection, graph

collection, graph = load_databases()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Wa'alaikum salam! I am Br. Asif. Welcome to your Madinah Arabic lesson. What would you like to learn today?"}
    ]

# --- Helper Functions ---
def get_graph_context(question: str) -> str:
    question_lower = question.lower()
    matched_nodes = []
    for node_id, data in graph.nodes(data=True):
        name = str(data.get("name", "")).lower()
        if name and name in question_lower and len(name) > 3:
            matched_nodes.append(node_id)
            
    if not matched_nodes:
        return "No specific graph concepts explicitly triggered."
        
    graph_context = []
    for node in matched_nodes:
        node_data = graph.nodes[node]
        graph_context.append(f"Concept: {node_data.get('name')} ({node_data.get('type')}) - {node_data.get('description')}")
        for neighbor in graph.successors(node):
            edge_data = graph.get_edge_data(node, neighbor)
            neighbor_data = graph.nodes[neighbor]
            graph_context.append(f"  -> {edge_data.get('type')}: {neighbor_data.get('name')} (Rationale: {edge_data.get('rationale')})")
    return "\\n".join(graph_context)

def get_vector_context(question: str, k=3) -> str:
    results = collection.query(query_texts=[question], n_results=k)
    chunks = results.get("documents", [[]])[0]
    sources = results.get("metadatas", [[]])[0]
    context_str = ""
    for chunk, meta in zip(chunks, sources):
        context_str += f"[Source: {meta.get('source')}]\\n{chunk}\\n\\n"
    return context_str

# --- UI ---
st.title("🕌 Madinah Arabic Tutor (GraphRAG)")
st.caption("Powered by Local Qwen2.5:7b, NetworkX, and ChromaDB")

# Display chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input
if prompt := st.chat_input("Ask Br. Asif a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    with st.chat_message("assistant"):
        with st.spinner("Retrieving facts and generating answer..."):
            vector_context = get_vector_context(prompt)
            graph_context = get_graph_context(prompt)
            
            system_prompt = f'''You are Br. Asif, a friendly and expert teacher of Madinah Arabic. 
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
{prompt}
'''
            try:
                response = requests.post(
                    OLLAMA_URL,
                    json={
                        "model": MODEL_NAME, 
                        "prompt": system_prompt, 
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
                        final_answer = "Brothers and sisters, I am an Arabic language teacher. I do not write code, solve math, or discuss outside topics. Let us focus on our Arabic lesson, Insha'Allah!"
                    else:
                        final_answer = result.get("answer", "")
                except json.JSONDecodeError:
                    final_answer = "Error: The local model failed to output valid JSON. Raw output: " + json_text
                        
                st.markdown(final_answer)
                st.session_state.messages.append({"role": "assistant", "content": final_answer})
                
            except Exception as e:
                st.error(f"Error communicating with Ollama: {e}")
