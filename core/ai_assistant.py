import os
from groq import Groq
from typing import List
import time 
import re
from dotenv import load_dotenv 

load_dotenv()

class AIAssistant:
    def __init__(self):
        self.api_key = os.environ.get("GROQ_API_KEY")
        print(f"DEBUG: API Key loaded status: {'Success' if self.api_key else 'Failed'}") 
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set in environment variables or .env file.")
        
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.1-8b-instant" 
        
        self.system_prompt = (
            "You are an expert word list generator for a Bingo game. "
            "Your task is to generate a comma-separated list of EXACTLY 25 words or phrases "
            "based on the user's topic. "
            "**CRITICAL:** ONLY return the list of words/phrases. DO NOT include any conversation, "
            "titles (e.g., 'Here is the list:'), explanations, numbering (e.g., 1., 2.), or newlines. "
            "The output MUST be in the same language as the user's request. "
            "Example of correct output: 'apple, banana, cherry, durian, mango, ...' (25 items)"
        )

    def generate_bingo_words(self, topic: str, count: int = 25) -> List[str]:
        user_prompt = f"Topic: '{topic}'. Generate EXACTLY {count} words or phrases."
        print(f"DEBUG: Sending prompt to Groq: '{user_prompt}'") 
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                model=self.model,
                temperature=0.7,
            )
            
            raw_response = chat_completion.choices[0].message.content
            
            # FINAL FIX LOGIC: ทำความสะอาดข้อความแบบเข้มงวด
            cleaned_response = raw_response.strip()
            cleaned_response = cleaned_response.replace('\n', ',')
            cleaned_response = re.sub(r'\s*\d+\.\s*', '', cleaned_response)
            cleaned_response = re.sub(r'[\s\t\r\xa0\ufeff]+', ' ', cleaned_response).strip() 
            cleaned_response = cleaned_response.replace(' ,', ',').replace(', ', ',')
            cleaned_response = re.sub(r',+', ',', cleaned_response)
            
            words = [word.strip() for word in cleaned_response.split(',') if word.strip()]
            words = [w.replace(' ', '').strip() for w in words] # ลบช่องว่างภายในคำไทย
            
            if len(words) > count:
                words = words[:count]
            
            print(f"DEBUG: Final words list count: {len(words)}")
            print(f"DEBUG: Final words list: {words}")
            
            return words
        
        except Exception as e:
            print(f"ERROR: Groq API call failed: {e}") 
            return []