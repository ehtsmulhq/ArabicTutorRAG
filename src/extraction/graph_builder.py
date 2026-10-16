import json
import yaml
import requests
import networkx as nx
import argparse
import re
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROMPTS_PATH = BASE_DIR / "config" / "prompts.yaml"
SCHEMA_PATH = BASE_DIR / "config" / "schema.yaml"
CHUNKS_PATH = BASE_DIR / "data" / "processed" / "all_chunks.json"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "knowledge_graph.json"

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"

def load_yaml(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def clean_and_parse_json(text: str) -> dict:
    text = text.strip()
    # Naive extraction if wrapped in markdown
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        if start != -1 and end != -1:
            text = text[start:end].strip()
    elif text.startswith("```"):
        start = 3
        end = text.find("```", start)
        if end != -1:
            text = text[start:end].strip()
            
    # Fix trailing commas before closing braces/brackets (common LLM hallucination)
    text = re.sub(r',\s*([\]}])', r'\1', text)
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fallback: find outermost curly braces
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end != 0:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
    return {}

def query_ollama(prompt: str) -> dict:
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "format": "json",
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=600)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error communicating with Ollama: {e}")
        return {}
        
    result = response.json()
    response_text = result.get("response", "")
    return clean_and_parse_json(response_text)

def main():
    parser = argparse.ArgumentParser(description="Build Knowledge Graph from Text Chunks")
    parser.add_argument("--limit", type=int, default=10, help="Number of chunks to process")
    args = parser.parse_args()

    try:
        prompts = load_yaml(PROMPTS_PATH)
        schema = load_yaml(SCHEMA_PATH)
    except Exception as e:
        print(f"Error loading YAML configs: {e}")
        return
        
    entity_prompt_template = prompts["extraction"]["entity_extraction"]
    rel_prompt_template = prompts["extraction"]["relationship_extraction"]
    
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

    for i, chunk in enumerate(chunks):
        if i <= last_processed:
            continue
            
        print(f"Processing chunk {i+1}/{len(chunks)}...")
        text_chunk = chunk.get("text", "")
        source = chunk.get("source", "")
        
        # 1. Extract Entities
        prompt_entities = entity_prompt_template.format(schema=schema_str, text_chunk=text_chunk)
        entities_data = query_ollama(prompt_entities)
        
        extracted_entities = entities_data.get("entities", [])
        if not extracted_entities or not isinstance(extracted_entities, list):
            print("No valid entities extracted for this chunk.")
            continue
            
        for ent in extracted_entities:
            if not isinstance(ent, dict):
                continue
            name = ent.get("name")
            if not name:
                continue
                
            name_str = str(name).strip()
            node_id = name_str.lower()
            
            # Avoid overwriting existing nodes, just merge sources if needed
            if not G.has_node(node_id):
                G.add_node(node_id, 
                           name=name_str,
                           type=ent.get("type"), 
                           description=ent.get("description"), 
                           source=ent.get("source") or source)
                           
        # 2. Extract Relationships
        entities_str = json.dumps(extracted_entities, indent=2, ensure_ascii=False)
        prompt_relations = rel_prompt_template.format(schema=schema_str, entities=entities_str)
        relations_data = query_ollama(prompt_relations)
        
        extracted_relations = relations_data.get("relations", [])
        if not extracted_relations or not isinstance(extracted_relations, list):
            print("No valid relations extracted for this chunk.")
            continue
            
        for rel in extracted_relations:
            if not isinstance(rel, dict):
                continue
            source_ent = rel.get("source_entity_name")
            target_ent = rel.get("target_entity_name")
            rel_type = rel.get("relationship_type")
            rationale = rel.get("rationale")
            
            if source_ent and target_ent and rel_type:
                source_str = str(source_ent).strip()
                target_str = str(target_ent).strip()
                source_id = source_str.lower()
                target_id = target_str.lower()
                
                # Ensure nodes exist
                if not G.has_node(source_id):
                    G.add_node(source_id, name=source_str, source=source)
                if not G.has_node(target_id):
                    G.add_node(target_id, name=target_str, source=source)
                    
                G.add_edge(source_id, target_id, type=rel_type, rationale=rationale, source=source)
                
        # Checkpoint: Save 1 by 1
        G.graph["last_processed_index"] = i
        print(f"--- Checkpoint: Saving at chunk {i+1} ---")
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(nx.node_link_data(G), f, indent=2, ensure_ascii=False)

    # Save graph
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    graph_data = nx.node_link_data(G)
    try:
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)
        print(f"\nGraph successfully saved to {OUTPUT_PATH}")
        print(f"Total Nodes: {G.number_of_nodes()}")
        print(f"Total Edges: {G.number_of_edges()}")
    except Exception as e:
        print(f"Error saving knowledge graph: {e}")

if __name__ == "__main__":
    main()

