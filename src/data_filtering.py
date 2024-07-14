from mlx_lm import load, generate


#model, tokenizer = load("mlx-community/Meta-Llama-3-8B-Instruct-8bit")
#
#messages = [
#    {
#        "role": "system",
#        "content": "Firstly, retrive every line from my user content prompt and print it. Than work separatly with every line. Check both: 1. In line there should be timestamp in format HH:MM:SS or MM:SS 2. Corresponding description (no JAPANESE, no HINDI, no ISRAEL, no KOREAN, no RUSSIAN, no CHINESE) which should have at least one WORD (only latin characters) or English TEXT (Be careful: combinations of latin letters, numbers and symbols are also a WORD) in it 3. ANY leading symbol (including space) before the single word or multiple words is ALLOWED. 4. Combination of multiple latin characters (i.e. 'seks') is equal to WORD, which is ALLOWED. In every line explain your reasoning, why you think it is empty. If description is combination of word and symbols it is valid. If description only symbol or empty it is invalid. Check this condition for every line. For every line write if line valid or invalid (use these words, but both words can not be in one line, do not write valid/invalid). If at least one line is violated or if there was at least one invalid, in the end print 'invalid' otherwise print 'valid'."
#    },
#    {"role": "user", "content": "00:01:28) - https://geni.us/LexsongProjector\n00:03:30) - TOP SECRET (come back later)\n00:04:49) - https://geni.us/VankyoProjector"
#     }
#]
#
#
#
#input_ids = tokenizer.apply_chat_template(
#    messages,
#    add_generation_prompt=True,
#    return_tensors="pt"
#)
#
#prompt = tokenizer.decode(input_ids[0].tolist())
#response = generate(model, tokenizer, max_tokens=600, prompt=prompt)
#
#print(response)

class LlamaValidator:
    
    def __init__(self, transcription_content=None, target_content=None, system_message=None):
        if system_message is None:
            system_message = ["You are a robot that checks if a YouTube video transcript is in English..\nCheck if the following text is in English (In order to conclude that it is english, it is enough to see that majority of words written in English. Also spoken language is considered to be English. If it is not a standart English, it is also allowed). Your answer will consist of only one number:'0' if you assume that transript is in English, '1' if it is not",
                              "Firstly, retrive every line from my user content prompt and print it. Than work separatly with every line. Check both: 1. In line there should be timestamp in format HH:MM:SS or MM:SS 2. Corresponding description (no JAPANESE, no HINDI, no ISRAEL, no KOREAN, no RUSSIAN, no CHINESE) which should have at least one WORD (only latin characters) or English TEXT (Be careful: combinations of latin letters, numbers and symbols are also a WORD) in it 3. ANY leading symbol (including space) before the single word or multiple words is ALLOWED. 4. Combination of multiple latin characters (i.e. 'seks') is equal to WORD, which is ALLOWED. In every line explain your reasoning, why you think it is empty. If description is combination of word and symbols it is valid. If description only symbol or empty it is invalid. Check this condition for every line. For every line write if line valid or invalid (use these words, but both words can not be in one line, do not write valid/invalid). If at least one line is violated or if there was at least one invalid, in the end print 'invalid' otherwise print 'valid'."
                              ]
        self.transcription_content = transcription_content
        self.target_content = target_content
        self.transcription_system_message = system_message[0]
        self.target_system_message = system_message[1]
        self.model, self.tokenizer = load("mlx-community/Meta-Llama-3-8B-Instruct-8bit")
        self.transcription_messages = [
            {"role": "system", "content": self.transcription_system_message},
            {"role": "user", "content": self.transcription_content},
        ]
        self.target_messages = [
            {"role": "system", "content": self.target_system_message},
            {"role": "user", "content": self.target_content},
        ]
               
    def create_prompt(self, messages):
        input_ids = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt"
        )
        return self.tokenizer.decode(input_ids[0].tolist())
    
    def validate_transcription(self):
        prompt = self.create_prompt(self.transcription_messages)
        response = generate(self.model, self.tokenizer, max_tokens=1, prompt=prompt)
        return response
    
    def validate_target(self):
        self.target_messages[1] = {"role": "user", "content": self.target_content}
        prompt = self.create_prompt(self.target_messages)
        response = generate(self.model, self.tokenizer, max_tokens=600, prompt=prompt)
        return response