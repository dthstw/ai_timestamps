from pytube import YouTube
import os
import certifi
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.urllib3 import AuthorizedHttp
import json
import re


SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']

def get_authenticated_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=8080)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

url_chapters = {}

url_chapters["pFssgtp1ckQ"] = "\n0:00 Why Use A Vest?\n2:18 Day 1: Finding Projects\n3:50 Day 2: Showing Crew & Projects\n10:40 Day 3: An Unexpected Turn Of Events\n13:13 Day 4: Volume Session\n13:52 Day 5: Getting Tired\n15:10 Day 6: Exhausted\n17:05 The Problems With Training Too Much\n18:06 Pros & Cons"
url_chapters["PvRbGuSeI3o"] = "\n00:00- intro \n00:20- turkey salad with poppyseed dressing\n04:08- beef meatloaf\n07:49- chicken and fried rice\n12:19- spaghetti squash (vegetarian option)\n17:23- taste testing\n20:34- let me know\n21:03- the end"

os.environ['SSL_CERT_FILE'] = certifi.where()

creds = get_authenticated_service()
authorized_http = AuthorizedHttp(creds)


def parse_timestamps(timestamps_str):
    """Parse the timestamps from a string into a list of dictionaries."""
    timestamps = []
    lines = timestamps_str.strip().split('\n')
    timestamp_regex = re.compile(r'(\d{1,2}:\d{2}(?::\d{2})?)\s*[-–]?\s*(.*)')
    
    for line in lines:
        match = timestamp_regex.match(line)
        if match:
            time_str, description = match.groups()
            timestamps.append({
                "time": time_str.strip(),
                "description": description.strip()
            })
            
    return timestamps

def download_audio(video_id, output_dir):
    """Download the audio stream of a YouTube video using OAuth."""
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    yt = YouTube(url=video_url,
        proxies=None,
        use_oauth=True,
        allow_oauth_cache=True
    )
    audio_stream = yt.streams.filter(only_audio=True).first()
    audio_path = audio_stream.download(output_path=output_dir, filename=f'{video_id}.mp3')
    
    return audio_path


def save_metadata(video_id, timestamps, output_dir):
    """Save the timestamps metadata to a JSON file."""
    metadata = {
        "video_id": video_id,
        "timestamps": timestamps
    }
    metadata_path = os.path.join(output_dir, f'{video_id}_metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=4)
        
    return metadata_path
    
if __name__ == "__main__":
    # Directory to save the audio files and metadata
    output_dir = "/Users/ruslankireev/Documents/vscode/ai_timestamps/scraped_data" 

    os.makedirs(output_dir, exist_ok=True)

    # Process each video in the url_chapters dictionary
    for video_id, chapters_str in url_chapters.items():
        print(f"Processing video ID: {video_id}")
        
        timestamps = parse_timestamps(chapters_str)
        
        audio_path = download_audio(video_id, output_dir)
        print(f"Audio downloaded and saved to: {audio_path}")
        
        metadata_path = save_metadata(video_id, timestamps, output_dir)
        print(f"Metadata saved to: {metadata_path}")
