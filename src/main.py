from googleapiclient.discovery import build
from dotenv import load_dotenv
import os


load_dotenv()

youtube_api_key = os.getenv('YOUTUBE_API_KEY')
print(f"Your YouTube API key is: {youtube_api_key}")