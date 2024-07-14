import json
import os
from data_filtering import LlamaValidator
from tqdm import tqdm

output_dir = "/Users/ruslankireev/Documents/vscode/ai_timestamps/youtube_captions/"

with open(os.path.join(output_dir, 'metadata_copy_2.json'), 'r') as file:
    data = json.load(file)
    
counter = 0

progress_bar = tqdm(total=len(data), desc='Processing items')

for item in data:
    if item.get("not valid") in [0, 1]:
        continue
    counter += 1
    transcription_path = item["transcription"]
    target_path = item["target"]

    try:
        with open(transcription_path) as f:
            transcription_lines = [next(f) for _ in range(25)]
        transcription_content = ''.join(transcription_lines)
    except StopIteration:
        print(f"Not enough lines in transcription file: {transcription_path}")
        item['not valid'] = 1
        continue  # Skip to the next item

    transcription_content = transcription_content.replace('"', '\\"')
    validator = LlamaValidator(transcription_content=transcription_content)
    transcription_result = validator.validate_transcription().strip()
    
    if int(transcription_result) == 0:
        try:
            with open(target_path) as f:
                target_lines = [next(f) for _ in range(3)]
            target_content = ''.join(target_lines)
            target_content = target_content.replace('"', '\\"')

            validator.target_content = target_content
            target_result = validator.validate_target().strip()

            # Check for the word "invalid" in the target result
            if "invalid" in target_result.lower():
                item['not valid'] = 1
            else:
                item['not valid'] = 0
        except StopIteration:
            print(f"Not enough lines in target file: {target_path}")
            item['not valid'] = 1
    else:
        item['not valid'] = 1

    if counter % 10 == 0:
        with open(os.path.join(output_dir, 'metadata_copy_2.json'), 'w') as file:
            json.dump(data, file, indent=4)
        print(f" {counter} items out of {len(data)} has being updated in the metadata file")
    
    tqdm.write(f"Processed {counter} items out of {len(data)}")
    progress_bar.update(1)

# Ensure the last remaining items are saved
with open(os.path.join(output_dir, 'metadata_copy_2.json'), 'w') as file:
    json.dump(data, file, indent=4)

progress_bar.close()

print("Script completed.")

        

  

