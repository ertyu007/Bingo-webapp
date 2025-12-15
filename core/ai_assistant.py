import os
from groq import Groq
from typing import List, Tuple
import time 
import re
from dotenv import load_dotenv 

# โหลด .env สำหรับการรันบนเครื่องตัวเอง
load_dotenv()

class AIAssistant:
    def __init__(self):
        self.api_key = os.environ.get("GROQ_API_KEY")
        print(f"DEBUG: API Key loaded status: {'Success' if self.api_key else 'Failed'}")
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set in environment variables or .env file.")
        
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.1-8b-instant" 
        
        # 💡 UPDATED SYSTEM PROMPT: เน้นย้ำว่าต้องสร้าง 35 คู่ 
        self.system_prompt = (
            "You are an expert Q&A generator for a Bingo game. "
            "Your task is to generate a comma-separated list of EXACTLY 35 pairs of 'Question:Answer' " # <<< จำนวน 35
            "based on the user's topic. The Question should be used on the Bingo card, and the Answer is for the host. "
            "**CRITICAL:** ONLY return the list of pairs separated by a colon, then by a comma. "
            "DO NOT include any conversation, titles, numbering, or newlines. "
            "Example of correct output: 'Who painted the Mona Lisa?:Leonardo da Vinci, What is the capital of France?:Paris, ...' (35 items)"
        )

    # 💡 ปรับให้รับค่า Count ที่ต้องการ (ตอนนี้จะใช้ 35)
    def generate_bingo_qa_pairs(self, topic: str, count: int = 35) -> List[str]: 
        """
        เรียกใช้ AI เพื่อสร้างคู่คำถาม:คำตอบ ตามหัวข้อที่กำหนด (ค่าเริ่มต้น 35 คู่)
        """
        user_prompt = f"Generate {count} Question:Answer pairs for the topic: '{topic}'"
        
        try:
            start_time = time.time()
            
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                model=self.model,
                temperature=0.7,
            )
            
            raw_response = chat_completion.choices[0].message.content
            
            print(f"DEBUG: AI Response Time: {time.time() - start_time:.2f}s")

            # --- Q&A Cleaning Logic (เหมือนเดิม) ---
            cleaned_response = raw_response.strip()
            
            # 1. แทนที่ Newline ด้วยคอมม่า และลบเลขนำหน้า
            cleaned_response = cleaned_response.replace('\n', ',')
            cleaned_response = re.sub(r'\s*\d+\.\s*', '', cleaned_response)
            
            # 2. จัดการช่องว่างแปลกปลอม
            cleaned_response = re.sub(r'[\s\t\r\xa0\ufeff]+', ' ', cleaned_response).strip()
            
            # 3. จัดการช่องว่างรอบคอมม่าและคอมม่าซ้ำซ้อน
            cleaned_response = cleaned_response.replace(' ,', ',').replace(', ', ',')
            cleaned_response = re.sub(r',+', ',', cleaned_response)
            
            # 4. ประมวลผลข้อความ: แยกด้วยจุลภาค (,)
            qa_pairs = [pair.strip() for pair in cleaned_response.split(',') if pair.strip()]
            
            # 5. [สำคัญ] ตรวจสอบความถูกต้องและตัดให้เหลือแค่ 'count' คู่แรก
            final_qa_pairs = []
            for pair in qa_pairs:
                if ':' in pair:
                    final_qa_pairs.append(pair.strip())
            
            if len(final_qa_pairs) > count:
                final_qa_pairs = final_qa_pairs[:count]
            
            print(f"DEBUG: Final Q&A pairs count: {len(final_qa_pairs)}")
            print(f"DEBUG: Final Q&A pairs (Sample): {final_qa_pairs[:5]}")
            
            return final_qa_pairs
            
        except Exception as e:
            print(f"ERROR: AI Assistant failed: {e}")
            return []