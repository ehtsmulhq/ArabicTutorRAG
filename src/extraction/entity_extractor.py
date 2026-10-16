import json
import yaml
import ollama
import os

class EntityExtractor:
    def __init__(self, model_name="qwen2.5:7b", config_path="../../config"):
        self.model_name = model_name
        with open(os.path.join(config_path, "schema.yaml"), 'r') as f:
            self.schema = yaml.safe_load(f)
        with open(os.path.join(config_path, "prompts.yaml"), 'r') as f:
            self.prompts = yaml.safe_load(f)

    def extract_entities(self, chunk_text: str) -> list:
        schema_str = yaml.dump(self.schema['entities'])
        prompt_template = self.prompts['extraction']['entity_extraction']
        prompt = prompt_template.format(schema=schema_str, text_chunk=chunk_text)
        
        try:
            response = ollama.chat(model=self.model_name, messages=[
                {
                    'role': 'system',
                    'content': 'You are a precise JSON-only data extraction assistant.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ], format='json', options={"temperature": 0.1})
            
            content = response.get('message', {}).get('content', '').strip()
            if not content:
                return []
                
            # Find the first { and last } to handle potential markdown wrappers
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = content[start:end]
                data = json.loads(json_str)
                return data.get('entities', [])
            return []
        except Exception as e:
            print(f"Error during extraction: {e}")
            return []

    def process_all_chunks(self, chunks_file: str, output_file: str):
        if not os.path.exists(chunks_file):
            print(f"{chunks_file} does not exist.")
            return

        with open(chunks_file, 'r', encoding='utf-8') as f:
            chunks = json.load(f)

        extracted_data = []
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i+1}/{len(chunks)}...")
            entities = self.extract_entities(chunk['text'])
            extracted_data.append({
                "chunk_id": i,
                "text": chunk['text'],
                "source": chunk['source'],
                "entities": entities
            })

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, indent=4, ensure_ascii=False)
        print(f"Saved extracted entities to {output_file}")

if __name__ == "__main__":
    extractor = EntityExtractor(model_name="qwen2.5:7b") # Assuming qwen2.5 is pulled
    extractor.process_all_chunks("../../data/processed/all_chunks.json", "../../data/processed/entities.json")
