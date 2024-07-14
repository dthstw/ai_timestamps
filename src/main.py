from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import json
import certifi
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.urllib3 import AuthorizedHttp
import json
import re
from youtube_transcript_api import YouTubeTranscriptApi
import time
from tqdm import tqdm
from googleapiclient.errors import HttpError


load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']

class YT_search:   
    def __init__(self, token_file,  client_secrets_file, query, output_dir, api_key, start_index=0):
        self.token_file = token_file
        self.client_secrets_file = client_secrets_file
        self.query = query
        self.output_dir = output_dir
        self.target_dir = os.path.join(output_dir, 'targets')
        self.captions_dir = os.path.join(output_dir, 'captions')
        self.api_key = api_key
        os.makedirs(self.target_dir, exist_ok=True)
        os.makedirs(self.captions_dir, exist_ok=True)
        self.per_query_counter = 0
        self.metadata = self.load_metadata() # Load metadata if it exists
        self.youtube = self.get_authenticated_service()
        
    def get_authenticated_service(self):
        return build('youtube', 'v3', developerKey=self.api_key)
        
    '''    
    def get_authenticated_service(self):
        creds = None
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.client_secrets_file, SCOPES)
                creds = flow.run_local_server(port=8080)
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        return build('youtube', 'v3', credentials=creds)
    '''
    
    def load_metadata(self):
        try:
            with open(os.path.join(self.output_dir, 'metadata_copy_2.json'), 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return []
        
    def save_metadata(self):
        with open(os.path.join(self.output_dir, 'metadata_copy_2.json'), 'w') as file:
            json.dump(self.metadata, file, indent=4)
        
    def search_videos(self, page_token=None):
        search_request = self.youtube.search().list(
            part='id',
            type='video',
            q=self.query,
            maxResults=50,
            relevanceLanguage = 'en',
            videoDuration='long',
            pageToken=page_token
        )
        while search_request is not None and self.per_query_counter < 45:
            search_response = search_request.execute()
            
            for item in search_response['items']:
                if self.per_query_counter >= 45:
                    break
                video_id = item['id']['videoId']
                if not self.is_video_processed(video_id):
                    description = self.filter_and_get_description(video_id)
                    if description:
                        target = self.extract_and_standardize_timestamps(description)
                        if not target:  # Skip if no timestamps are found
                            continue
                        captions = self.get_captions(video_id)
                        if captions is None:
                            continue  # Skip this video if captions could not be retrieved
                        metadata_entry = {
                                'youtube query': self.query,
                                'video': video_id,
                                'target': os.path.join(self.target_dir, f"{video_id}_target.txt"),
                                'transcription': os.path.join(self.captions_dir, f"{video_id}_captions.txt")
                            }
                        self.metadata.append(metadata_entry)
                        self.save_metadata_entry(video_id, target, captions)
                        self.per_query_counter += 1
                                                        
            # Update the page token for the next request
            if 'nextPageToken' in search_response:
                page_token = search_response['nextPageToken']
                search_request = self.youtube.search().list_next(search_request, search_response)
            else:
                search_request = None

        self.save_metadata()
        return page_token
    
                    
    def is_video_processed(self, video_id):
        for entry in self.metadata:
            if entry['video'] == video_id:
                return True
        return False
    
    def filter_and_get_description(self, video_id):
        response = self.youtube.videos().list(
            part='contentDetails,snippet,status',
            id=video_id
        ).execute()
        if response['items'][0]['status']['privacyStatus'] == 'public':
            if 'duration' in response['items'][0]['contentDetails']:
                duration_minutes = self.parse_duration(response['items'][0]['contentDetails']['duration'])
                if duration_minutes <= 90:
                    description = response['items'][0]['snippet']['description']
                    return description
        return None
    
    def extract_and_standardize_timestamps(self, description):
        # Regular expression pattern for matching various timestamp formats
        timestamp_pattern = re.compile(r'\b(?:(\d+):)?(\d{1,2}):(\d{2})\b')

        # Function to standardize timestamps to HH:MM:SS format
        def standardize_timestamp(match):
            groups = match.groups()
            hours = groups[0] if groups[0] else '00'
            minutes = groups[1].zfill(2)
            seconds = groups[2].zfill(2)
            return f"{hours.zfill(2)}:{minutes}:{seconds}"

        # Extracting and standardizing timestamps from the description
        standardized_lines = []
        for match in timestamp_pattern.finditer(description):
            original_timestamp = match.group(0)
            standardized_timestamp = standardize_timestamp(match)
            start, end = match.span()
            line = description[start:end].replace(original_timestamp, standardized_timestamp)
            line += description[end:].split('\n', 1)[0]  # Get the rest of the line
            standardized_lines.append(line)
        
        return "\n".join(standardized_lines) if standardized_lines else None
        
    def parse_duration(self, duration):
        pattern = re.compile(
            r'P(?:(?P<years>\d+)Y)?(?:(?P<months>\d+)M)?(?:(?P<weeks>\d+)W)?(?:(?P<days>\d+)D)?'
            r'T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?'
        )
        match = pattern.match(duration)
        if not match:
            return None
        duration_dict = match.groupdict()
        hours = int(duration_dict['hours'] or 0)
        minutes = int(duration_dict['minutes'] or 0)
        seconds = int(duration_dict['seconds'] or 0)
        total_minutes = hours * 60 + minutes + seconds / 60
        return total_minutes
    
    #Youtube-transcript-part
    def get_captions(self, video_id):
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return transcript
        except Exception as e:
            print(f"Could not retrieve captions for video ID {video_id}: {e}")
            return None
        
    def format_timestamps(self, stamp):
        return time.strftime('%H:%M:%S', time.gmtime(stamp))
        
    def save_captions_to_file(self, video_id, captions):
        if captions:
            output_file = os.path.join(self.captions_dir, f"{video_id}_captions.txt")
            with open(output_file, "w") as file:
                for entry in captions:
                    start_time = self.format_timestamps(entry['start'])
                    end_time = self.format_timestamps(entry['start'] + entry['duration'])
                    text = entry['text']
                    file.write(f"{start_time} - {end_time}: {text}\n")
                    
    def save_metadata_entry(self, video_id, target, captions):
        # Save the standardized timestamps
        target_file = os.path.join(self.target_dir, f"{video_id}_target.txt")
        with open(target_file, "w") as file:
            file.write(target)
        
        # Save the captions
        self.save_captions_to_file(video_id, captions)
        
with open('/Users/ruslankireev/Documents/vscode/ai_timestamps/api_keys.json', 'r') as file:
    api_keys = json.load(file)['api_keys']
    
queries = [
    "Vlog",
    "Lecture",
    "Fitness vlog",
    "History video",
    "Podcast",
    "Talks"
]

os.environ['SSL_CERT_FILE'] = certifi.where()

token_file = '/Users/ruslankireev/Documents/vscode/ai_timestamps/token.json'
client_secrets_file = '/Users/ruslankireev/Documents/vscode/ai_timestamps/client_secrets.json'
output_dir = '/Users/ruslankireev/Documents/vscode/ai_timestamps/youtube_captions'

for query in tqdm(queries, desc="Scraping YouTube videos"):
    start_index = 0
    page_token = None
    for api_key in api_keys:
        yt_search = YT_search(token_file, client_secrets_file, query, output_dir, api_key, start_index)
        try:
            page_token = yt_search.search_videos(page_token)  # Continue from the last page token
            if yt_search.per_query_counter >= 45:
                break  # If 50 videos have been processed, move to the next query
        except HttpError as e:
            if e.resp.status == 403 and 'quotaExceeded' in e.content.decode():
                print(f"Switching to next API key due to quota exceeded.")
                start_index = yt_search.per_query_counter  # Update start_index to continue from where it left off
                continue  # Switch to the next API key and retry
            else:
                raise e  # Raise the exception if it's not a quota exceeded error

print("Scraping is finished")
