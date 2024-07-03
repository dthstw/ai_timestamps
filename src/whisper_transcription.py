import os
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import soundfile as sf
from pydub import AudioSegment
import torch

# Path to the converted audio file
audio_file_path = "/Users/ruslankireev/Documents/vscode/ai_timestamps/scraped_data/zduSFxRajkE.wav"

# Load the Whisper model in Hugging Face format
processor = WhisperProcessor.from_pretrained("openai/whisper-small.en")
model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-small.en")

# Function to split audio into chunks
def split_audio(file_path, chunk_length_s=30):
    audio = AudioSegment.from_wav(file_path)
    chunks = []
    for i in range(0, len(audio), chunk_length_s * 1000):
        chunk = audio[i:i + chunk_length_s * 1000]
        chunk_path = f"chunk_{i//1000}.wav"
        chunk.export(chunk_path, format="wav")
        chunks.append((chunk_path, i // 1000))
    return chunks

# Function to transcribe a batch of audio chunks
def transcribe_batch(chunks):
    waveforms = []
    start_times = []
    for chunk_path, start_time in chunks:
        waveform, sampling_rate = sf.read(chunk_path)
        assert sampling_rate == 16000
        waveforms.append(waveform)
        start_times.append(start_time)
    
    # Pad and create batch
    input_features = processor(waveforms, sampling_rate=16000, return_tensors="pt", padding=True).input_features
    
    predicted_ids = model.generate(input_features)
    transcriptions = processor.batch_decode(predicted_ids, skip_special_tokens=True)
    
    return list(zip(transcriptions, start_times))

# Convert seconds to MM:SS format
def format_timestamp(seconds):
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02}:{seconds:02}"

# Split the audio file into chunks
chunks = split_audio(audio_file_path)

# Transcribe chunks in batches of 16
batch_size = 16
transcriptions = []
for i in range(0, len(chunks), batch_size):
    batch = chunks[i:i + batch_size]
    transcriptions.extend(transcribe_batch(batch))
    # Clean up chunk files after transcription
    for chunk_path, _ in batch:
        os.remove(chunk_path)

# Save the transcription results with timestamps
save_dir = "/Users/ruslankireev/Documents/vscode/ai_timestamps/whisper_outputs"
os.makedirs(save_dir, exist_ok=True)
audio_filename = os.path.splitext(os.path.basename(audio_file_path))[0]
save_path = os.path.join(save_dir, f"{audio_filename}_whisper.txt")

with open(save_path, "w") as f:
    for transcription, start_time in transcriptions:
        start_timestamp = format_timestamp(start_time)
        end_timestamp = format_timestamp(start_time + 30)  # Assuming each chunk is 30 seconds
        f.write(f"{start_timestamp} - {end_timestamp}: {transcription}\n")

print(f"Transcription saved to: {save_path}")
