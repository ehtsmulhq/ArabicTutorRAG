import json
import yaml
import ollama
import os

class RelationExtractor:
    def __init__(self, model_name="qwen2.5:7b", config_path="../../config"):
        self.model_name = model_name
        with open(os.path.join(config_path, "schema.yaml"), 'r') as f:
            self.schema = yaml.safe_load(f)
        with open(os.path.join(config_path, "prompts.yaml"), 'r') as f:
            self.prompts = yaml.safe_load(f)

    def extract_relations(self, entities: list) -> list:
        if not entities:
            return []
            
        schema_str = yaml.dump(self.schema['relationships'])
        entities_str = json.dumps(entities, indent=2, ensure_ascii=False)
        
        prompt_template = self.prompts['extraction']['relationship_extraction']
        prompt = prompt_template.format(schema=schema_str, entities=entities_str)
        
        try:
            response = ollama.chat(model=self.model_name, messages=[
                {
                    'role': 'system',
                    'content': 'You are a precise JSON-only relation extraction assistant. Find relationships between provided entities only.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ], format='json', options={"temperature": 0.1})
            
            content = response.get('message', {}).get('content', '').strip()
            if not content:
                return []
                
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = content[start:end]
                data = json.loads(json_str)
                return data.get('relations', [])
            return []
        except Exception as e:
            print(f"Error during relation extraction: {e}")
            return []

    def process_all(self, entities_file: str, output_file: str):
        if not os.path.exists(entities_file):
            print(f"{entities_file} does not exist.")
            return

        with open(entities_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for i, item in enumerate(data):
            print(f"Extracting relations for chunk {i+1}/{len(data)}...")
            relations = self.extract_relations(item.get('entities', []))
            item['relations'] = relations

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Saved extracted relations to {output_file}")

if __name__ == "__main__":
    extractor = RelationExtractor(model_name="qwen2.5:7b")
    extractor.process_all("../../data/processed/entities.json", "../../data/processed/graph_data.json")
