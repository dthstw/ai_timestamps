from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import json


load_dotenv()

video_id = "kCc8FmEb1nY"

youtube_api_key = os.getenv('YOUTUBE_API_KEY')
print(f"Your YouTube API key is: {youtube_api_key}")

class YouTube:   
    def __init__(self, api_key):
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        
    def search_videos(self, query, video_duration='long', max_results=20):
        search_request = self.youtube.search().list(
            part='id',
            type='video',
            q=query,
            maxResults=max_results,
            videoDuration=video_duration
        )
        search_response = search_request.execute()
        
        return search_response
    
inf = YouTube(youtube_api_key)

query = "comedy"

video_details = inf.search_videos(query)

print(json.dumps(video_details, indent=4))