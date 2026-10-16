import json
import networkx as nx
import os
import chromadb
from chromadb.utils import embedding_functions

class GraphBuilder:
    def __init__(self, graph_data_file: str, db_path: str = "../../data/chroma_db", graph_path: str = "../../data/graph.graphml"):
        self.graph_data_file = graph_data_file
        self.db_path = db_path
        self.graph_path = graph_path
        self.graph = nx.DiGraph()
        
        # Setup ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=self.db_path)
        # Using a default local embedding model (sentence-transformers under the hood)
        self.embedding_func = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.chroma_client.get_or_create_collection(
            name="arabic_grammar",
            embedding_function=self.embedding_func
        )

    def build(self):
        if not os.path.exists(self.graph_data_file):
            print(f"{self.graph_data_file} not found.")
            return

        with open(self.graph_data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        docs = []
        metadatas = []
        ids = []

        for item in data:
            chunk_id = str(item.get("chunk_id"))
            text = item.get("text", "")
            source = item.get("source", "")
            entities = item.get("entities", [])
            relations = item.get("relations", [])
            
            # Prepare Vector DB insertion
            docs.append(text)
            
            # Record entity names as metadata for linking
            entity_names = [e.get("name") for e in entities if "name" in e]
            metadatas.append({"source": source, "entities": ",".join(entity_names)})
            ids.append(f"chunk_{chunk_id}")

            # Build Graph
            # Normalization helper
            def normalize(name):
                return name.strip().lower()

            # Pass 1: Add nodes with normalization
            for ent in entities:
                raw_name = ent.get("name")
                if not raw_name:
                    continue
                    
                ent_name = normalize(raw_name)
                ent_type = ent.get("type")
                description = ent.get("description", "")
                
                if self.graph.has_node(ent_name):
                    # Merge descriptions if different
                    existing_desc = self.graph.nodes[ent_name].get("description", "")
                    if description and description not in existing_desc:
                        description = existing_desc + " | " + description
                        
                self.graph.add_node(ent_name, type=ent_type, description=description, raw_name=raw_name, chunk_id=chunk_id)
                ent["normalized_name"] = ent_name

            for rel in relations:
                src = rel.get("source_entity_name")
                tgt = rel.get("target_entity_name")
                r_type = rel.get("relationship_type")
                
                if src and tgt and r_type:
                    src_norm = normalize(src)
                    tgt_norm = normalize(tgt)
                    
                    if not self.graph.has_node(src_norm):
                        self.graph.add_node(src_norm, raw_name=src)
                    if not self.graph.has_node(tgt_norm):
                        self.graph.add_node(tgt_norm, raw_name=tgt)
                        
                    self.graph.add_edge(src_norm, tgt_norm, type=r_type, rationale=rel.get("rationale", ""))

        # Insert to Vector DB
        print("Adding chunks to Vector Database...")
        # Add in batches if necessary, but assuming small enough for simple insert
        if docs:
            self.collection.add(
                documents=docs,
                metadatas=metadatas,
                ids=ids
            )
            print(f"Added {len(docs)} documents to ChromaDB.")

        # Save Graph
        os.makedirs(os.path.dirname(self.graph_path), exist_ok=True)
        nx.write_graphml(self.graph, self.graph_path)
        print(f"Graph with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges saved to {self.graph_path}")

if __name__ == "__main__":
    builder = GraphBuilder("../../data/processed/graph_data.json")
    builder.build()
