import chromadb
import networkx as nx
import ollama
import yaml
import os

class HybridRetriever:
    def __init__(self, db_path: str = "../../data/chroma_db", graph_path: str = "../../data/graph.graphml", config_path: str = "../../config"):
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.collection = self.chroma_client.get_collection("arabic_grammar")
        self.graph = nx.read_graphml(graph_path) if os.path.exists(graph_path) else nx.DiGraph()
        
        with open(os.path.join(config_path, "prompts.yaml"), 'r') as f:
            self.prompts = yaml.safe_load(f)
            
        self.model_name = "qwen2.5:7b"

    def retrieve(self, question: str, top_k: int = 3) -> dict:
        # 1. Vector Search
        results = self.collection.query(
            query_texts=[question],
            n_results=top_k
        )
        
        retrieved_texts = []
        entity_names = set()
        
        if results['documents'] and len(results['documents'][0]) > 0:
            retrieved_texts = results['documents'][0]
            metadatas = results['metadatas'][0]
            
            for meta in metadatas:
                if 'entities' in meta and meta['entities']:
                    for e in meta['entities'].split(','):
                        entity_names.add(e.strip().lower())

        # 2. Graph Traversal
        style_examples = []
        prerequisites = []
        
        for ent in entity_names:
            if self.graph.has_node(ent):
                # Look for AsifExplanation
                for neighbor in self.graph.successors(ent):
                    edge_data = self.graph.get_edge_data(ent, neighbor)
                    if edge_data and edge_data.get('type') == 'EXPLAINED_BY':
                        node_data = self.graph.nodes[neighbor]
                        if node_data.get('type') == 'AsifExplanation':
                            style_examples.append(f"{neighbor}: {node_data.get('description', '')}")
                            
                # Look for prerequisites
                for neighbor in self.graph.predecessors(ent):
                    edge_data = self.graph.get_edge_data(neighbor, ent)
                    if edge_data and edge_data.get('type') == 'PREREQUISITE_OF':
                        node_data = self.graph.nodes[neighbor]
                        prerequisites.append(f"{neighbor}: {node_data.get('description', '')}")

        return {
            "texts": retrieved_texts,
            "style_examples": style_examples,
            "prerequisites": prerequisites
        }

    def generate_answer(self, question: str) -> str:
        context_data = self.retrieve(question)
        
        context_str = "\n".join(context_data["texts"])
        if context_data["prerequisites"]:
            context_str += "\n\nPrerequisite Concepts:\n" + "\n".join(context_data["prerequisites"])
            
        style_str = "\n".join(context_data["style_examples"]) if context_data["style_examples"] else "Use your best enthusiastic teaching style, referencing the Madinah book concepts clearly."
        
        prompt_template = self.prompts['generation']['rag_answer']
        prompt = prompt_template.format(
            context=context_str,
            style_examples=style_str,
            question=question
        )
        
        try:
            response = ollama.chat(model=self.model_name, messages=[
                {
                    'role': 'user',
                    'content': prompt
                }
            ], options={"temperature": 0.7})
            
            return response['message']['content']
        except Exception as e:
            return f"Error generating answer: {e}"

if __name__ == "__main__":
    retriever = HybridRetriever()
    ans = retriever.generate_answer("How do I form a nominal sentence in Arabic?")
    print(ans)
