import json
import os
import re

class Chunker:
    def __init__(self, max_chunk_words=300, overlap_words=50):
        self.max_chunk_words = max_chunk_words
        self.overlap_words = overlap_words

    def chunk_text(self, text: str, source_meta: str) -> list:
        """
        Splits raw text into chunks. 
        A sentence-based chunker with overlap, respecting paragraph boundaries where possible.
        """
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        current_chunk_sentences = []
        current_word_count = 0

        for para in paragraphs:
            # Simple sentence splitting heuristic
            sentences = re.split(r'(?<=[.!?])\s+', para.strip())
            for sentence in sentences:
                if not sentence:
                    continue
                words = sentence.split()
                if not words:
                    continue
                    
                if current_word_count + len(words) > self.max_chunk_words and current_chunk_sentences:
                    # Save current chunk
                    chunks.append({
                        "text": " ".join(current_chunk_sentences),
                        "source": source_meta
                    })
                    # Start new chunk with overlap (keep last few sentences up to overlap_words)
                    overlap_sentences = []
                    overlap_words_count = 0
                    for s in reversed(current_chunk_sentences):
                        s_words = len(s.split())
                        if overlap_words_count + s_words <= self.overlap_words:
                            overlap_sentences.insert(0, s)
                            overlap_words_count += s_words
                        else:
                            break
                            
                    current_chunk_sentences = overlap_sentences + [sentence]
                    current_word_count = overlap_words_count + len(words)
                else:
                    current_chunk_sentences.append(sentence)
                    current_word_count += len(words)

        if current_chunk_sentences:
            chunks.append({
                "text": " ".join(current_chunk_sentences),
                "source": source_meta
            })
            
        return chunks

    def chunk_video_transcript(self, segments: list, source_meta: str) -> list:
        """
        Chunks video transcript segments using sentence-aware regex splitting.
        Each segment from Whisper has 'start', 'end', and 'text'.
        """
        chunks = []
        if not segments:
            return chunks

        # Flatten segments into a list of words with their interpolated timestamps
        words_with_times = []
        for seg in segments:
            text = seg.get('text', '').strip()
            if not text:
                continue
            seg_words = text.split()
            start = seg.get('start', 0.0)
            end = seg.get('end', 0.0)
            
            # Interpolate word timestamps within the segment
            duration = end - start
            time_per_word = duration / len(seg_words) if seg_words else 0
            
            for i, w in enumerate(seg_words):
                w_start = start + i * time_per_word
                w_end = w_start + time_per_word
                words_with_times.append({'word': w, 'start': w_start, 'end': w_end})

        if not words_with_times:
            return chunks

        # Join all words to form the full text and split into sentences
        full_text = " ".join([w['word'] for w in words_with_times])
        raw_sentences = re.split(r'(?<=[.!?])\s+', full_text)

        # Map sentences back to their start and end times
        sentences_meta = []
        word_idx = 0
        for s in raw_sentences:
            if not s:
                continue
            s_words = s.split()
            if not s_words:
                continue

            s_start = words_with_times[word_idx]['start']
            s_end = words_with_times[word_idx + len(s_words) - 1]['end']

            sentences_meta.append({
                'text': s,
                'words': len(s_words),
                'start': s_start,
                'end': s_end
            })
            word_idx += len(s_words)

        # Build chunks with overlap
        current_chunk = []
        current_word_count = 0

        for s_meta in sentences_meta:
            # If a single "sentence" (like unpunctuated YouTube captions) is too large on its own,
            # break it down forcefully so it doesn't break the vector DB limits.
            if s_meta['words'] > self.max_chunk_words:
                # First flush anything currently pending
                if current_chunk:
                    c_start = current_chunk[0]['start']
                    c_end = current_chunk[-1]['end']
                    c_text = " ".join([x['text'] for x in current_chunk])
                    chunks.append({
                        "text": c_text,
                        "source": f"{source_meta} (Time: {c_start:.1f}s - {c_end:.1f}s)"
                    })
                    current_chunk = []
                    current_word_count = 0
                
                # Force-split this massive string into pieces
                massive_words = s_meta['text'].split()
                w_start = s_meta['start']
                w_end = s_meta['end']
                time_per_w = (w_end - w_start) / len(massive_words) if len(massive_words) > 0 else 0
                
                piece_start_idx = 0
                while piece_start_idx < len(massive_words):
                    piece_words = massive_words[piece_start_idx : piece_start_idx + self.max_chunk_words]
                    p_start = w_start + piece_start_idx * time_per_w
                    p_end = p_start + len(piece_words) * time_per_w
                    
                    chunks.append({
                        "text": " ".join(piece_words),
                        "source": f"{source_meta} (Time: {p_start:.1f}s - {p_end:.1f}s)"
                    })
                    piece_start_idx += self.max_chunk_words - self.overlap_words # shift by max minus overlap
                
                continue
                
            if current_word_count + s_meta['words'] > self.max_chunk_words and current_chunk:
                # Save current chunk
                c_start = current_chunk[0]['start']
                c_end = current_chunk[-1]['end']
                c_text = " ".join([x['text'] for x in current_chunk])
                chunks.append({
                    "text": c_text,
                    "source": f"{source_meta} (Time: {c_start:.1f}s - {c_end:.1f}s)"
                })

                # Start new chunk with overlap
                overlap_chunk = []
                overlap_words = 0
                for x in reversed(current_chunk):
                    if overlap_words + x['words'] <= self.overlap_words:
                        overlap_chunk.insert(0, x)
                        overlap_words += x['words']
                    else:
                        break

                current_chunk = overlap_chunk + [s_meta]
                current_word_count = overlap_words + s_meta['words']
            else:
                current_chunk.append(s_meta)
                current_word_count += s_meta['words']

        # Add remaining
        if current_chunk:
            c_start = current_chunk[0]['start']
            c_end = current_chunk[-1]['end']
            c_text = " ".join([x['text'] for x in current_chunk])
            chunks.append({
                "text": c_text,
                "source": f"{source_meta} (Time: {c_start:.1f}s - {c_end:.1f}s)"
            })

        return chunks

    def process_all(self, video_json_dir: str, output_file: str):
        all_chunks = []
        
        # We are no longer taking data from the book (PDFs). Only transcripts.
        
        # Process Videos
        if os.path.exists(video_json_dir):
            for filename in os.listdir(video_json_dir):
                if filename.endswith('.json'):
                    with open(os.path.join(video_json_dir, filename), 'r', encoding='utf-8') as f:
                        segments = json.load(f)
                        chunks = self.chunk_video_transcript(segments, source_meta=f"Video: {filename}")
                        all_chunks.extend(chunks)
                        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_chunks, f, indent=4, ensure_ascii=False)
        print(f"Generated {len(all_chunks)} chunks, saved to {output_file}")

if __name__ == "__main__":
    import pathlib
    base_dir = pathlib.Path(__file__).parent.parent.parent
    chunker = Chunker(max_chunk_words=300)
    chunker.process_all(
        str(base_dir / "data" / "processed" / "video_transcripts_cleaned"),
        str(base_dir / "data" / "processed" / "all_chunks.json")
    )
