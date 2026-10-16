import json
import os
import re

def clean_text(text: str) -> str:
    # Remove bracketed tags like [Music], [Applause], etc.
    text = re.sub(r'\[.*?\]', '', text)
    
    # Remove common English filler words/stutters (uh, um, ah).
    text = re.sub(r'\b(uh|um|ah)\b', '', text, flags=re.IGNORECASE)
    
    # Apply dictionary-based replacement for common phonetic misspellings
    replacements = {
        r'\bal\s*if\b': 'Alif',
        r'\bdamma\b': 'Damma',
        r'\bfatha\b': 'Fatha',
        r'\bkasra\b': 'Kasra',
        r'\bsukun\b': 'Sukun',
        r'\btanween\b': 'Tanween',
        r'\bmajroor\b': 'Majroor',
        r'\bin\s*sha\s*allah\b|\binshallah\b': "Insha'Allah",
        r'\bsubhana\s+tal[a]?\b': "subhanahu wa ta'ala",
    }
    
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
    # Trim excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def process_transcripts(input_dir: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    for filename in os.listdir(input_dir):
        if filename.endswith('.json'):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)
            
            with open(input_path, 'r', encoding='utf-8') as f:
                segments = json.load(f)
                
            cleaned_segments = []
            for seg in segments:
                if 'text' in seg:
                    original_text = seg['text']
                    cleaned = clean_text(original_text)
                    seg['text'] = cleaned
                cleaned_segments.append(seg)
                
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned_segments, f, indent=4, ensure_ascii=False)
                
    print(f"Cleaned transcripts saved to {output_dir}")

if __name__ == "__main__":
    import pathlib
    base_dir = pathlib.Path(__file__).parent.parent.parent
    input_dir = base_dir / "data" / "processed" / "video_transcripts"
    output_dir = base_dir / "data" / "processed" / "video_transcripts_cleaned"
    process_transcripts(str(input_dir), str(output_dir))
