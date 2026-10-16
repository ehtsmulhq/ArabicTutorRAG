import os
import warnings

warnings.filterwarnings("ignore")

import pymupdf as fitz  # PyMuPDF
from PIL import Image
import easyocr
import numpy as np

class PDFParser:
    def __init__(self, pdf_dir: str):
        self.pdf_dir = pdf_dir
        self.reader = easyocr.Reader(['ar', 'en'], verbose=False)

    def parse_pdf(self, file_path: str) -> str:
        """Parses a single PDF file and returns its text using PyMuPDF to render images and easyocr for OCR."""
        try:
            doc = fitz.open(file_path)
            text = ""
            # Only process the first 5 pages for the Phase 1 sample (Lesson 1)
            sample_pages = min(5, len(doc))
            for page_num in range(sample_pages):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(dpi=300, colorspace=fitz.csRGB, alpha=False) # High DPI for better OCR
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Extract text using easyocr
                img_np = np.array(img)
                results = self.reader.readtext(img_np, detail=0, paragraph=True)
                page_text = "\n\n".join(results)
                
                text += f"\n--- Page {page_num + 1} ---\n" + page_text
            
            return text
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return ""

    def process_all(self, output_dir: str):
        """Processes all PDFs in the directory and saves text to output_dir."""
        os.makedirs(output_dir, exist_ok=True)
        for filename in os.listdir(self.pdf_dir):
            if filename.lower().endswith('.pdf'):
                file_path = os.path.join(self.pdf_dir, filename)
                print(f"Processing PDF: {filename}")
                text = self.parse_pdf(file_path)
                
                output_path = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}.txt")
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f"Saved extracted text to: {output_path}")

if __name__ == "__main__":
    import pathlib
    base_dir = pathlib.Path(__file__).parent.parent.parent
    parser = PDFParser(str(base_dir / "data" / "raw" / "pdf"))
    parser.process_all(str(base_dir / "data" / "processed" / "pdf_text"))
