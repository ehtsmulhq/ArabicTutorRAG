import warnings

warnings.filterwarnings("ignore")

import whisper
import os
import json

class VideoTranscriber:
    def __init__(self, video_dir: str, model_size: str = "medium"):
        """
        model_size can be 'tiny', 'base', 'small', 'medium', 'large-v3'
        Uses local inference via whisper.
        """
        self.video_dir = video_dir
        print(f"Loading Whisper model '{model_size}'...")
        # device is handled automatically, but can enforce 'cuda' or 'cpu' if needed
        self.model = whisper.load_model(model_size)
        print("Model loaded.")

    def transcribe_video(self, file_path: str):
        """Transcribes a single video and returns the result (with timestamps)."""
        try:
            print(f"Transcribing {file_path}...")
            initial_prompt = "damma, fatha, kasra, tanween, sukun, Insha'Allah, madinah, tajweed, quran, arabic"
            result = self.model.transcribe(file_path, initial_prompt=initial_prompt, fp16=False)
            return result
        except Exception as e:
            print(f"Error transcribing {file_path}: {e}")
            return None

    def process_all(self, output_dir: str):
        """Processes all videos in the directory and saves transcripts."""
        os.makedirs(output_dir, exist_ok=True)
        for filename in os.listdir(self.video_dir):
            if filename.lower().endswith(('.mp4', '.mkv', '.avi', '.mp3', '.wav')):
                file_path = os.path.join(self.video_dir, filename)
                result = self.transcribe_video(file_path)
                
                if result:
                    # Save raw text
                    text_output_path = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}.txt")
                    with open(text_output_path, 'w', encoding='utf-8') as f:
                        f.write(result['text'])
                    
                    # Save detailed JSON with timestamps
                    json_output_path = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}.json")
                    with open(json_output_path, 'w', encoding='utf-8') as f:
                        json.dump(result['segments'], f, indent=4, ensure_ascii=False)
                        
                    print(f"Saved transcript to: {text_output_path}")

if __name__ == "__main__":
    import pathlib
    base_dir = pathlib.Path(__file__).parent.parent.parent
    transcriber = VideoTranscriber(str(base_dir / "data" / "raw" / "video"), model_size="base") # Use base for testing speed
    transcriber.process_all(str(base_dir / "data" / "processed" / "video_transcripts"))
