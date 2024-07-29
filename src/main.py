import re
from googleapiclient.discovery import build
from google.auth.credentials import AnonymousCredentials
from dotenv import load_dotenv
import os
import certifi
import json
from youtube_transcript_api import YouTubeTranscriptApi
import time
from tqdm import tqdm
from googleapiclient.errors import HttpError
import logging

load_dotenv()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']

class YT_search:
    def __init__(self, token_file, client_secrets_file, query, vids_per_query, output_dir, api_key, start_index=0, metadata=None):
        self.token_file = token_file
        self.client_secrets_file = client_secrets_file
        self.query = query
        self.vids_per_query = vids_per_query
        self.max_results_per_request = 50
        self.output_dir = output_dir
        self.target_dir = os.path.join(output_dir, 'targets')
        self.captions_dir = os.path.join(output_dir, 'captions')
        self.api_key = api_key
        os.makedirs(self.target_dir, exist_ok=True)
        os.makedirs(self.captions_dir, exist_ok=True)
        self.per_query_counter = start_index #In case of switching api keys, continue collecting remaining vids per that query.
        self.metadata = metadata if metadata is not None else self.load_metadata()
        self.youtube = self.get_authenticated_service()

    def get_authenticated_service(self):
        return build('youtube', 'v3', developerKey=self.api_key, credentials=AnonymousCredentials())
    
    #Check if a found video already presented in metadata or not
    def is_video_processed(self, video_id):
        for entry in self.metadata:
            if entry['video_id'] == video_id:
                return True
        return False
    
    def parse_duration(self, duration):
        pattern = re.compile(
            r'P(?:(?P<years>\d+)Y)?(?:(?P<months>\d+)M)?(?:(?P<weeks>\d+)W)?(?:(?P<days>\d+)D)?'
            r'T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?'
        )
        match = pattern.match(duration)
        if not match:
            logging.debug(f"Duration parsing failed for duration: {duration}")
            return None
        duration_dict = match.groupdict()
        hours = int(duration_dict['hours'] or 0)
        minutes = int(duration_dict['minutes'] or 0)
        seconds = int(duration_dict['seconds'] or 0)
        total_minutes = hours * 60 + minutes + seconds / 60
        return total_minutes

    def filter_videos_by_length(self, video_id):
        video_details = self.youtube.videos().list(
            part='contentDetails',
            id=video_id
        ).execute()
        
        if 'items' not in video_details or len(video_details['items']) == 0:
            logging.debug(f"No video details found for video ID: {video_id}")
            return None
    
        if 'contentDetails' not in video_details['items'][0]:
            logging.debug(f"No contentDetails found for video ID: {video_id}")
            return None
        
        duration = video_details['items'][0]['contentDetails'].get('duration')
        if not duration:
            logging.debug(f"No duration found for video ID: {video_id}")
            return None
        
        duration_minutes = self.parse_duration(duration)
        logging.debug(f"Video ID: {video_id}, Duration (minutes): {duration_minutes}")
        
        if duration_minutes <= 50:
            return duration_minutes
        return None

    def calculate_minimum_timestamps(self, duration_minutes):
        if duration_minutes <= 30:
            return 5
        elif 30 < duration_minutes <= 40:
            return 7
        elif 40 < duration_minutes <= 50:
            return 9
        return None

    def extract_timestamps_from_description(self, description):
        # Updated pattern to better match the provided description format
        pattern = re.compile(r'^\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*[-–—]?\s*(.*)', re.MULTILINE)
        matches = pattern.findall(description)
        timestamps = [(time, " ".join(text.split()).strip()) for time, text in matches if text.strip()]
        logging.debug(f"Description: {description}")
        logging.debug(f"Extracted timestamps: {timestamps}")
        return timestamps
    
    #Returns TRUE if amount of timestamps is the same of higher than minimum required
    def validate_timestamps(self, timestamps, min_required):
        if min_required is None:
            logging.debug(f"Video is too long, skipping validation. Required: {min_required}")
            return False
        is_valid = len(timestamps) >= min_required
        logging.debug(f"Validating timestamps: {is_valid}, Required: {min_required}, Found: {len(timestamps)}")
        return is_valid

    #Creating empty list if there is no metadatafile, loading metadata file in case it is found
    def load_metadata(self):
        try:
            with open(os.path.join(self.output_dir, 'new_metadata.json'), 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return []
      
    def get_captions(self, video_id):
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return transcript
        except Exception as e:
            print(f"Could not retrieve captions for video ID {video_id}: {e}")
            return None
        
    def format_timestamps(self, stamp):
        return time.strftime('%H:%M:%S', time.gmtime(stamp))
    
    #Transfering captions into the txt files in proper format: HH:MM:SS-HH:MM:SS caption's line
    def save_captions_to_file(self, video_id, captions):
        if captions:
            output_file = os.path.join(self.captions_dir, f"{video_id}_captions.txt")
            #with open(output_file, "w") as file:
            #    for entry in captions:
            #        start_time = self.format_timestamps(entry['start'])
            #        end_time = self.format_timestamps(entry['start'] + entry['duration'])
            #        text = entry['text']
            #        file.write(f"{start_time} - {end_time}: {text}\n")
            with open(output_file, "w") as file:
                window_duration = 120  # 2 minutes window
                current_start_time = captions[0]['start']
                current_text = captions[0]['text']

                for entry in captions[1:]:
                    if entry['start'] - current_start_time < window_duration:
                        current_text += " " + entry['text']
                    else:
                        end_time = self.format_timestamps(current_start_time + window_duration)
                        start_time = self.format_timestamps(current_start_time)
                        file.write(f"{start_time} - {end_time}: {current_text}\n")

                        current_start_time = entry['start']
                        current_text = entry['text']

                # Write the last window
                end_time = self.format_timestamps(current_start_time + window_duration)
                start_time = self.format_timestamps(current_start_time)
                file.write(f"{start_time} - {end_time}: {current_text}\n")
                    
    def save_metadata_entry(self, video_id, timestamps, captions):
        # Save the standardized timestamps
        target_file = os.path.join(self.target_dir, f"{video_id}_target.txt")
        with open(target_file, "w") as file:
            for time_str, text in timestamps:
                parts = time_str.split(':')
                if len(parts) == 2:  # Format is MM:SS
                    minutes = int(parts[0])
                    seconds = int(parts[1])
                    total_seconds = minutes * 60 + seconds
                elif len(parts) == 3:  # Format is HH:MM:SS
                    hours = int(parts[0])
                    minutes = int(parts[1])
                    seconds = int(parts[2])
                    total_seconds = hours * 3600 + minutes * 60 + seconds
                else:
                    raise ValueError(f"Unexpected timestamp format: {time}")
        
                formatted_timestamp = self.format_timestamps(total_seconds)
                file.write(f"{formatted_timestamp} - {text}\n")
        
        # Save the captions
        self.save_captions_to_file(video_id, captions)

    def save_metadata(self):
        with open(os.path.join(self.output_dir, 'new_metadata.json'), 'w') as file:
            json.dump(self.metadata, file, indent=4)

    def search_videos(self, page_token=None):
        logging.debug(f"Starting search loop. Current per_query_counterr: {self.per_query_counter}, vids_per_query: {self.vids_per_query}")
        
        max_page_attempts = 4  # Maximum number of page requests per request
        current_page_attempt = 0
        
        while self.per_query_counter < self.vids_per_query and current_page_attempt < max_page_attempts:         
            request = self.youtube.search().list(
                q=self.query,
                part='id,snippet',
                type='video',
                relevanceLanguage='en',
                #order='viewCount',
                videoDuration='long',
                maxResults=self.max_results_per_request,
                pageToken=page_token
            )

            response = request.execute()
            items = response.get('items', [])

            if not items:
                logging.debug("No items found in the API response.")
                if 'nextPageToken' in response:
                    page_token = response['nextPageToken']
                    current_page_attempt += 1
                    continue
                else:
                    break

            video_ids = [item['id']['videoId'] for item in items]
            
            # Get full video details using videos.list
            video_details_response = self.youtube.videos().list(
                part='snippet,contentDetails',
                id=','.join(video_ids)
            ).execute()
            
            valid_video_found = False

            for video_details in video_details_response.get('items', []):
                video_id = video_details['id']
                #Skipping already retrieved video
                if self.is_video_processed(video_id):
                    continue
                #Continue if it is a new one
                video_description = video_details['snippet']['description']
                logging.debug(f"Video Description in search_videos: {video_description}")
                duration_minutes = self.filter_videos_by_length(video_id)
                if duration_minutes is None:
                    continue

                timestamps = self.extract_timestamps_from_description(video_description)
                min_required = self.calculate_minimum_timestamps(duration_minutes)
                
                if self.validate_timestamps(timestamps, min_required):
                    try:
                        captions = self.get_captions(video_id)
                        if captions is None:
                            logging.error(f"Skipping video {video_id} due to failed caption retrieval.")
                            continue
                        metadata_entry = {
                            'youtube query': self.query,
                            'video_id': video_id,
                            'captions': os.path.join(self.captions_dir, f"{video_id}_captions.txt"),
                            'timestamps': os.path.join(self.target_dir, f"{video_id}_target.txt")
                        }
                        valid_video_found = True
                        self.metadata.append(metadata_entry)
                        self.save_metadata_entry(video_id, timestamps, captions)
                        self.per_query_counter += 1
                        logging.debug(f"Video processed. Incremented per_query_counter: {self.per_query_counter}")
                        self.save_metadata() 
                        
                        if self.per_query_counter >= self.vids_per_query:
                            logging.debug(f"Required number of videos processed: {self.per_query_counter}. Exiting loop.")
                            return None
                    except Exception as e:
                        print(f"An error occurred for video {video_id}: {e}")
                else:
                    continue
                
            if valid_video_found:
                current_page_attempt = 0  # Reset the page attempt counter if a valid video is found
            else:
                current_page_attempt += 1

            if 'nextPageToken' in response:
                page_token = response['nextPageToken']
                request = self.youtube.search().list_next(request, response)
            else:
                request = None
                
            current_page_attempt += 1
            
        if current_page_attempt >= max_page_attempts:
            print(f"Reached maximum page attempts for query '{self.query}'. Collected {self.per_query_counter} videos.")

        return page_token
    
def process_queries(queries, vids_per_query, output_dir, api_keys):
    token_file = '/Users/ruslankireev/Documents/vscode/ai_timestamps/token.json'
    client_secrets_file = '/Users/ruslankireev/Documents/vscode/ai_timestamps/client_secrets.json'

    metadata_path = os.path.join(output_dir, 'new_metadata.json')
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
    else:
        metadata = []

    for query in tqdm(queries, desc="Scraping YouTube videos"):
        start_index = 0
        page_token = None
        for api_key in api_keys:
            yt_search = yt_search = YT_search(token_file, client_secrets_file, query, vids_per_query, output_dir, api_key, start_index, metadata)
            try:
                page_token = yt_search.search_videos(page_token)  # Continue from the last page token
                if yt_search.per_query_counter >= vids_per_query:
                    break  # If required number of videos have been processed, move to the next query
            except HttpError as e:
                if e.resp.status == 403 and 'quotaExceeded' in e.content.decode():
                    print(f"Switching to next API key due to quota exceeded.")
                    start_index = yt_search.per_query_counter  # Update start_index to continue from where it left off
                    continue  # Switch to the next API key and retry
                else:
                    raise e  # Raise the exception if it's not a quota exceeded error

def main(): 

    queries = [
        "gadget review"
    ]
    vids_per_query = 1
    output_dir = '/Users/ruslankireev/Documents/vscode/ai_timestamps/short_vids'
    with open('/Users/ruslankireev/Documents/vscode/ai_timestamps/api_keys.json', 'r') as file:
        api_keys = json.load(file)['api_keys']

    process_queries(queries, vids_per_query, output_dir, api_keys)

if __name__=="__main__":
    main()