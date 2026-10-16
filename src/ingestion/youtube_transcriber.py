import os
import json
import logging
import argparse
import pathlib
import time
import random
from typing import List, Dict, Any
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import http.cookiejar
import requests

def get_playlist_video_ids(playlist_url: str, cookies_file: str = None) -> List[Dict[str, str]]:
    """
    Extracts video IDs and titles from a YouTube playlist.
    """
    ydl_opts = {
        'extract_flat': 'in_playlist',
        'quiet': True,
        'no_warnings': True,
    }
    if cookies_file and os.path.exists(cookies_file):
        ydl_opts['cookiefile'] = cookies_file
        
    videos = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(playlist_url, download=False)
            if 'entries' in info:
                for entry in info['entries']:
                    if entry and entry.get('id'):
                        videos.append({
                            'id': entry['id'],
                            'title': entry.get('title', 'Unknown Title')
                        })
            elif info.get('id'):
                 videos.append({
                     'id': info['id'],
                     'title': info.get('title', 'Unknown Title')
                 })
        except Exception as e:
            logger.error(f"Failed to fetch playlist info: {e}")
            
    return videos

def fetch_and_save_transcripts(playlist_url: str, output_dir: str, cookies_file: str = None):
    """
    Fetches transcripts for all videos in a playlist and saves them as JSON.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Fetching video IDs from playlist: {playlist_url}")
    videos = get_playlist_video_ids(playlist_url, cookies_file)
    
    if not videos:
        logger.warning("No videos found in the playlist.")
        return
        
    logger.info(f"Found {len(videos)} videos. Fetching transcripts...")
    
    # Setup HTTP client for cookies if provided
    http_client = None
    if cookies_file and os.path.exists(cookies_file):
        cookie_jar = http.cookiejar.MozillaCookieJar(cookies_file)
        cookie_jar.load(ignore_discard=True, ignore_expires=True)
        http_client = requests.Session()
        http_client.cookies = cookie_jar
    
    for idx, video in enumerate(videos, start=1):
        video_id = video['id']
        # Sanitize title for filename
        safe_title = "".join([c for c in video['title'] if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        safe_title = safe_title.replace(" ", "_")
        filename = f"{idx:03d}_{video_id}_{safe_title}.json"
        filepath = os.path.join(output_dir, filename)
        
        if os.path.exists(filepath):
            logger.info(f"Transcript already exists for {video['title']} ({video_id}), skipping.")
            continue
            
        try:
            # Get the transcript
            langs = ['en', 'en-US', 'en-GB', 'es', 'es-419', 'fr', 'fr-CA', 'de', 'it', 'pt', 'pt-BR', 'ru', 'zh-Hans', 'zh-Hant', 'ja', 'ko', 'hi', 'ar', 'id', 'tr', 'nl', 'pl', 'sv', 'vi', 'th']
            ytt_api = YouTubeTranscriptApi(http_client=http_client)
            transcript = ytt_api.fetch(video_id, languages=langs)
            
            # Format to match Whisper output expected by chunker.py
            # Whisper segment has: 'text', 'start', 'end'
            formatted_transcript = []
            for segment in transcript:
                # In youtube-transcript-api 1.2.4, segment is an object not a dict
                start = getattr(segment, 'start', 0.0)
                duration = getattr(segment, 'duration', 0.0)
                end = start + duration
                
                text = getattr(segment, 'text', '').replace('\n', ' ')
                formatted_transcript.append({
                    'text': text,
                    'start': start,
                    'end': end
                })
                
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(formatted_transcript, f, indent=4, ensure_ascii=False)
                
            logger.info(f"Successfully saved transcript for {video['title']} ({video_id})")
            
        except Exception as e:
            logger.error(f"Could not fetch transcript for {video['title']} ({video_id}): {e}")
            
        # Add a random delay between 4 to 8 seconds to avoid YouTube IP rate limiting
        delay = random.uniform(4, 8)
        logger.info(f"Sleeping for {delay:.2f}s to avoid rate limiting...")
        time.sleep(delay)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download YouTube transcripts from a playlist.")
    parser.add_argument("--playlist", type=str, default="https://youtube.com/playlist?list=PL2C51DED07020185B", help="YouTube playlist URL")
    parser.add_argument("--cookies", type=str, default=None, help="Path to a Netscape cookies.txt file to bypass YouTube IP blocks")
    args = parser.parse_args()

    base_dir = pathlib.Path(__file__).parent.parent.parent
    OUTPUT_DIR = str(base_dir / "data" / "processed" / "video_transcripts")
    
    fetch_and_save_transcripts(args.playlist, OUTPUT_DIR, args.cookies)
