import os
from pytube import YouTube
import certifi
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.urllib3 import AuthorizedHttp
import json
import re
import subprocess

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

url_chapters = {
    "pFssgtp1ckQ": "\n0:00 Why Use A Vest?\n2:18 Day 1: Finding Projects\n3:50 Day 2: Showing Crew & Projects\n10:40 Day 3: An Unexpected Turn Of Events\n13:13 Day 4: Volume Session\n13:52 Day 5: Getting Tired\n15:10 Day 6: Exhausted\n17:05 The Problems With Training Too Much\n18:06 Pros & Cons",
    "PvRbGuSeI3o": "\n00:00- intro \n00:20- turkey salad with poppyseed dressing\n04:08- beef meatloaf\n07:49- chicken and fried rice\n12:19- spaghetti squash (vegetarian option)\n17:23- taste testing\n20:34- let me know\n21:03- the end",
    "zduSFxRajkE": "\n00:00:00 intro: Tokenization, GPT-2 paper, tokenization-related issues\n00:05:50 tokenization by example in a Web UI (tiktokenizer)\n00:14:56 strings in Python, Unicode code points\n00:18:15 Unicode byte encodings, ASCII, UTF-8, UTF-16, UTF-32\n00:22:47 daydreaming: deleting tokenization\n00:23:50 Byte Pair Encoding (BPE) algorithm walkthrough\n00:27:02 starting the implementation\n00:28:35 counting consecutive pairs, finding most common pair\n00:30:36 merging the most common pair\n00:34:58 training the tokenizer: adding the while loop, compression ratio\n00:39:20 tokenizer/LLM diagram: it is a completely separate stage\n00:42:47 decoding tokens to strings\n00:48:21 encoding strings to tokens\n00:57:36 regex patterns to force splits across categories\n01:11:38 tiktoken library intro, differences between GPT-2/GPT-4 regex\n01:14:59 GPT-2 encoder.py released by OpenAI walkthrough\n01:18:26 special tokens, tiktoken handling of, GPT-2/GPT-4 differences\n01:25:28 minbpe exercise time! write your own GPT-4 tokenizer\n01:28:42 sentencepiece library intro, used to train Llama 2 vocabulary\n01:43:27 how to set vocabulary set? revisiting gpt.py transformer\n01:48:11 training new tokens, example of prompt compression\n01:49:58 multimodal [image, video, audio] tokenization with vector quantization\n01:51:41 revisiting and explaining the quirks of LLM tokenization\n02:10:20 final recommendations\n02:12:50 ??? :)",
    "kCc8FmEb1nY": "\n00:00:00 intro: ChatGPT, Transformers, nanoGPT, Shakespeare baseline language modeling, code setup\n00:07:52 reading and exploring the data\n00:09:28 tokenization, train/val split\n00:14:27 data loader: batches of chunks of data\n00:22:11 simplest baseline: bigram language model, loss, generation\n00:34:53 training the bigram model\n00:38:00 port our code to a script\n00:42:13 version 1: averaging past context with for loops, the weakest form of aggregation\n00:47:11 the trick in self-attention: matrix multiply as weighted aggregation\n00:51:54 version 2: using matrix multiply\n00:54:42 version 3: adding softmax\n00:58:26 minor code cleanup\n01:00:18 positional encoding\n01:02:00 THE CRUX OF THE VIDEO: version 4: self-attention\n01:11:38 note 1: attention as communication\n01:12:46 note 2: attention has no notion of space, operates over sets\n01:13:40 note 3: there is no communication across batch dimension\n01:14:14 note 4: encoder blocks vs. decoder blocks\n01:15:39 note 5: attention vs. self-attention vs. cross-attention\n01:16:56 note 6: 'scaled' self-attention. why divide by sqrt(head_size)\n01:19:11 inserting a single self-attention block to our network\n01:21:59 multi-headed self-attention\n01:24:25 feedforward layers of transformer block\n01:26:48 residual connections\n01:32:51 layernorm (and its relationship to our previous batchnorm)\n01:37:49 scaling up the model! creating a few variables. adding dropout\n01:42:39 encoder vs. decoder vs. both (?) Transformers\n01:46:22 super quick walkthrough of nanoGPT, batched multi-headed self-attention\n01:48:53 back to ChatGPT, GPT-3, pretraining vs. finetuning, RLHF\n01:54:32 conclusions"
}

os.environ['SSL_CERT_FILE'] = certifi.where()

creds = get_authenticated_service()


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

    # Convert MP3 to WAV with 16000 Hz sampling rate using ffmpeg
    wav_path = os.path.join(output_dir, f'{video_id}.wav')
    command = f"ffmpeg -i {audio_path} -ar 16000 -ac 1 {wav_path}"
    subprocess.run(command, shell=True, check=True)
    os.remove(audio_path)  # Remove the original MP3 file

    return wav_path

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
        wav_file_name = f"{video_id}.wav"
        wav_file_path = os.path.join(output_dir, wav_file_name)

        if os.path.exists(wav_file_path):
            print(f"Audio for video ID {video_id} already exists. Skipping...")
            continue

        print(f"Processing video ID: {video_id}")

        timestamps = parse_timestamps(chapters_str)

        wav_path = download_audio(video_id, output_dir)
        print(f"Audio downloaded and saved to: {wav_path}")

        metadata_path = save_metadata(video_id, timestamps, output_dir)
        print(f"Metadata saved to: {metadata_path}")
