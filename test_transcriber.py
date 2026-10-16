import sys
from unittest.mock import MagicMock

# Mock yt_dlp and youtube_transcript_api
yt_dlp_mock = MagicMock()
yt_dlp_mock.YoutubeDL.return_value.__enter__.return_value.extract_info.return_value = {
    'entries': [
        {'id': 'vid1', 'title': 'Video 1'},
        None, # simulate deleted video
        {'id': 'vid2', 'title': 'Video 2'}
    ]
}
sys.modules['yt_dlp'] = yt_dlp_mock

yta_mock = MagicMock()
sys.modules['youtube_transcript_api'] = yta_mock
sys.modules['youtube_transcript_api.formatters'] = MagicMock()

# Now import the module
from src.ingestion.youtube_transcriber import get_playlist_video_ids, fetch_and_save_transcripts

print("Testing get_playlist_video_ids with None entry...")
try:
    videos = get_playlist_video_ids("http://fake.url")
    print("Videos:", videos)
except Exception as e:
    print("Error:", e)
