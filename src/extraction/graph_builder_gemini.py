import json
import yaml
import requests
import networkx as nx
import argparse
import time
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = BASE_DIR / "config" / "schema.yaml"
CHUNKS_PATH = BASE_DIR / "data" / "processed" / "all_chunks.json"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "knowledge_graph_gemini.json"
ENV_PATH = BASE_DIR / ".env"

def load_env():
    if ENV_PATH.exists():
        with open(ENV_PATH, "r") as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    return line.strip().split("=", 1)[1]
    return os.environ.get("GEMINI_API_KEY")

API_KEY = load_env()
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={API_KEY}"

def load_yaml(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def clean_and_parse_json(text: str) -> dict:
    text = text.strip()
    if "`json" in text:
        start = text.find("`json") + 7
        end = text.find("`", start)
        if start != -1 and end != -1:
            text = text[start:end].strip()
    elif "`" in text:
        start = text.find("`") + 3
        end = text.find("`", start)
        if start != -1 and end != -1:
            text = text[start:end].strip()
            
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        return {}

def query_gemini(prompt: str, max_retries=5) -> dict:
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.1
        }
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(GEMINI_URL, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            if "candidates" in data and len(data["candidates"]) > 0:
                text_response = data["candidates"][0]["content"]["parts"][0]["text"]
                return clean_and_parse_json(text_response)
        except requests.RequestException as e:
            status_code = getattr(e.response, 'status_code', None)
            
            # If it's a 503 Service Unavailable or 429 Too Many Requests, wait and retry
            if status_code in [503, 429]:
                wait_time = (attempt + 1) * 10
                print(f"Gemini API busy (Status {status_code}). Retrying in {wait_time} seconds... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
                continue
                
            # Otherwise, print error and return empty
            print(f"Error communicating with Gemini API: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response details: {e.response.text}")
            break
            
    return {}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=1000, help="Max chunks to process")
    args = parser.parse_args()

    if not API_KEY:
        print("Error: GEMINI_API_KEY not found in .env")
        return

    schema = load_yaml(SCHEMA_PATH)
    schema_str = json.dumps(schema, indent=2)

    try:
        with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
            chunks = json.load(f)
    except Exception as e:
        print(f"Error reading chunks file: {e}")
        return
        
    chunks = chunks[:args.limit]
    
    # Resume Logic
    if OUTPUT_PATH.exists():
        try:
            with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                G = nx.node_link_graph(data)
            print(f"Loaded existing graph with {G.number_of_nodes()} nodes.")
        except Exception as e:
            print(f"Could not load existing graph: {e}")
            G = nx.DiGraph()
    else:
        G = nx.DiGraph()

    last_processed = G.graph.get("last_processed_index", -1)

    # Unified Prompt Template
    prompt_template = '''You are an expert Arabic Grammar AI Assistant extracting a Knowledge Graph from Br. Asif's video transcripts.
    
Based on the following schema:
{schema}

Analyze the following BATCH of text chunks. Extract both Entities AND their Relationships across ALL chunks in a SINGLE strictly formatted JSON object. 
Ensure you output ONLY valid JSON. 

Format requirement:
{{
  "entities": [
    {{"name": "entity_name", "type": "Lesson|GrammarRule|VocabItem|Example|AsifExplanation", "description": "brief description", "source": "copy the source exactly"}}
  ],
  "relations": [
    {{"source_entity_name": "name1", "target_entity_name": "name2", "relationship_type": "CONTAINS|DEMONSTRATED_BY|EXPLAINED_BY|PREREQUISITE_OF", "rationale": "Why"}}
  ]
}}

Text Chunks Batch:
{text_chunk}
'''

    BATCH_SIZE = 5
    print(f"Starting Gemini Extraction in BATCHES OF {BATCH_SIZE}. Free tier limit: 15 Requests per Minute.")
    
    for i in range(0, len(chunks), BATCH_SIZE):
        batch_end = min(i + BATCH_SIZE - 1, len(chunks) - 1)
        
        if batch_end <= last_processed:
            continue
            
        print(f"Processing chunks {i+1} to {batch_end+1} / {len(chunks)}...")
        
        batch = chunks[i:i+BATCH_SIZE]
        combined_text = ""
        for idx, c in enumerate(batch):
            combined_text += f"\n--- CHUNK {i+idx+1} ---\nSource: {c.get('source')}\nText: {c.get('text')}\n"
            
        # For default source fallback if model misses it
        default_source = batch[0].get("source", "")
            
        prompt = prompt_template.format(schema=schema_str, text_chunk=combined_text)
        
        # Rate limit protection (15 RPM = 1 request every 4 seconds)
        time.sleep(4.5)
        
        result_data = query_gemini(prompt)
        
        # 1. Extract Entities
        extracted_entities = result_data.get("entities", [])
        if extracted_entities and isinstance(extracted_entities, list):
            for ent in extracted_entities:
                if not isinstance(ent, dict): continue
                name_str = ent.get("name")
                if not name_str: continue
                
                node_id = str(name_str).strip().lower()
                if not G.has_node(node_id):
                    G.add_node(node_id, name=str(name_str).strip(), type=ent.get("type"), description=ent.get("description"), source=ent.get("source", default_source))

        # 2. Extract Relationships
        extracted_relations = result_data.get("relations", [])
        if extracted_relations and isinstance(extracted_relations, list):
            for rel in extracted_relations:
                if not isinstance(rel, dict): continue
                source_ent = rel.get("source_entity_name")
                target_ent = rel.get("target_entity_name")
                rel_type = rel.get("relationship_type")
                rationale = rel.get("rationale")
                
                if source_ent and target_ent and rel_type:
                    source_id = str(source_ent).strip().lower()
                    target_id = str(target_ent).strip().lower()
                    
                    if G.has_node(source_id) and G.has_node(target_id):
                        G.add_edge(source_id, target_id, type=rel_type, rationale=rationale, source=default_source)
                               
        # Checkpoint: Save after batch
        G.graph["last_processed_index"] = batch_end
        print(f"--- Checkpoint: Saving at chunk {batch_end+1} ---")
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(nx.node_link_data(G), f, indent=2, ensure_ascii=False)

    print(f"\nGraph successfully saved to {OUTPUT_PATH}")
    print(f"Total Nodes: {G.number_of_nodes()}")
    print(f"Total Edges: {G.number_of_edges()}")

if __name__ == "__main__":
    main()
