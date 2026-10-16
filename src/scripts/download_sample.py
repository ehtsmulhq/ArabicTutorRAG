import os
import requests
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
}

def download_file(url, dest_path):
    print(f"Downloading {url} to {dest_path}...")
    try:
        response = requests.get(url, stream=True, headers=HEADERS)
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Successfully downloaded {dest_path}")
    except Exception as e:
        print(f"Failed to download {url}: {e}")

def get_madinah_book_1_pdf():
    base_url = "https://lqtoronto.com/downloads.html"
    try:
        response = requests.get(base_url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the Madinah Book 1 PDF link
        for a in soup.find_all('a', href=True):
            text = a.text.lower()
            href = a['href']
            # Heuristic for Madinah Book 1 Arabic text or handouts
            if 'book 1' in text and href.endswith('.pdf'):
                return urljoin(base_url, href)
            # Sometimes they just link the raw file name
            if 'madina' in href.lower() and '1' in href and href.endswith('.pdf'):
                return urljoin(base_url, href)
                
        # Fallback to known structure if parsing fails
        return "https://lqtoronto.com/downloads/madinabooks/madina-book-1.pdf"
    except Exception as e:
        print(f"Error fetching PDF link: {e}")
        return "https://lqtoronto.com/downloads/madinabooks/madina-book-1.pdf"

def get_lesson_1_video():
    # LQToronto uses a video download page or media page
    base_url = "https://lqtoronto.com/videodl.html"
    try:
        response = requests.get(base_url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for Book 1 Lesson 1 (often organized as DVD 1, Part A etc.)
        for a in soup.find_all('a', href=True):
            text = a.text.lower()
            href = a['href']
            # Look for video extensions (mp4, avi)
            if href.endswith('.mp4') or href.endswith('.avi'):
                if 'book 1' in text or 'book1' in href.lower() or 'b1' in href.lower():
                    return urljoin(base_url, href)
                    
        # Fallback to a placeholder or assumed link if not found
        return "https://lqtoronto.com/videos/Book1/B1-D1-Part-A.mp4"
    except Exception as e:
        print(f"Error fetching video link: {e}")
        return "https://lqtoronto.com/videos/Book1/B1-D1-Part-A.mp4"

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    pdf_dir = os.path.join(base_dir, "data", "raw", "pdf")
    video_dir = os.path.join(base_dir, "data", "raw", "video")
    
    os.makedirs(pdf_dir, exist_ok=True)
    os.makedirs(video_dir, exist_ok=True)
    
    # 1. Scrape and download Book 1 PDF
    print("Scraping for Madinah Book 1 PDF...")
    pdf_url = get_madinah_book_1_pdf()
    pdf_dest = os.path.join(pdf_dir, "Madinah_Book_1.pdf")
    if pdf_url:
        download_file(pdf_url, pdf_dest)
    else:
        print("Could not find PDF URL.")
        
    # 2. Scrape and download Lesson 1 Video
    print("Scraping for Book 1 Lesson 1 Video...")
    video_url = get_lesson_1_video()
    video_dest = os.path.join(video_dir, "Book_1_Lesson_1.mp4")
    if video_url:
        download_file(video_url, video_dest)
    else:
        print("Could not find Video URL.")

if __name__ == "__main__":
    main()
