import json
import os
import argparse
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CHUNKS_PATH = BASE_DIR / "data" / "processed" / "all_chunks.json"
CHROMA_DIR = BASE_DIR / "data" / "processed" / "chroma_db"

def main():
    print("Initializing local ChromaDB and embedding model...")
    # Initialize persistent ChromaDB
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    
    # Use a fast, free local embedding model
    # default is all-MiniLM-L6-v2 which is great for fast text search
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    collection = client.get_or_create_collection(
        name="madinah_arabic", 
        embedding_function=sentence_transformer_ef
    )

    print(f"Loading chunks from {CHUNKS_PATH}...")
    try:
        with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
            chunks = json.load(f)
    except Exception as e:
        print(f"Error reading chunks file: {e}")
        return

    documents = []
    metadatas = []
    ids = []

    print("Preparing data for Vector Database...")
    for i, chunk in enumerate(chunks):
        text = chunk.get("text", "").strip()
        source = chunk.get("source", "")
        
        if not text:
            continue
            
        documents.append(text)
        metadatas.append({"source": source, "chunk_index": i})
        ids.append(f"chunk_{i}")

    # Add to ChromaDB in batches of 100
    batch_size = 100
    total_added = 0
    
    print(f"Embedding and saving {len(documents)} chunks to Vector DB...")
    for i in range(0, len(documents), batch_size):
        end = min(i + batch_size, len(documents))
        
        collection.add(
            documents=documents[i:end],
            metadatas=metadatas[i:end],
            ids=ids[i:end]
        )
        total_added += (end - i)
        print(f"  Inserted {total_added}/{len(documents)} chunks...")

    print(f"\nSuccess! Vector Database built at: {CHROMA_DIR}")
    print(f"Total embedded chunks in collection: {collection.count()}")

if __name__ == "__main__":
    main()
