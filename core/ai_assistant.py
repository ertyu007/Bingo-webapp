import os
from groq import Groq
from typing import List
import time 
import re
from dotenv import load_dotenv 

# โหลด .env สำหรับการรันบนเครื่องตัวเอง
load_dotenv()

class AIAssistant:
    def __init__(self):
        # ดึง API Key จาก Environment Variable
        self.api_key = os.environ.get("GROQ_API_KEY")
        print(f"DEBUG: API Key loaded status: {'Success' if self.api_key else 'Failed'}")
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set in environment variables or .env file.")
        
        # ตั้งค่า Groq Client
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.1-8b-instant" # โมเดลเร็วที่เราเลือก
        
        # System Prompt เพื่อให้ AI รู้หน้าที่
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
        """
        เรียกใช้ AI เพื่อสร้างคำศัพท์ตามหัวข้อที่กำหนด

        Args:
            topic: หัวข้อสำหรับสร้างคำศัพท์
            count: จำนวนคำศัพท์ที่ต้องการ (ค่าเริ่มต้น 25)

        Returns:
            List[str]: รายการคำศัพท์ที่สะอาดแล้ว
        """
        user_prompt = f"Generate {count} words/phrases for the topic: '{topic}'"
        
        try:
            start_time = time.time()
            
            # เรียกใช้ Groq API
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

            # FINAL FIX LOGIC: ทำความสะอาดข้อความแบบเข้มงวด
            cleaned_response = raw_response.strip()
            
            # 1. แทนที่ Newline (\n) ด้วยคอมม่า (,) และลบเลขนำหน้า (e.g., 1., 2.)
            cleaned_response = cleaned_response.replace('\n', ',')
            cleaned_response = re.sub(r'\s*\d+\.\s*', '', cleaned_response)
            
            # 2. **สำคัญ:** แทนที่ช่องว่างแปลกปลอม (รวม \t, \xa0, \ufeff) ด้วยช่องว่างเดี่ยว ' '
            cleaned_response = re.sub(r'[\s\t\r\xa0\ufeff]+', ' ', cleaned_response).strip()
            
            # 3. จัดการช่องว่างรอบคอมม่าและคอมม่าซ้ำซ้อน
            # A. ลบช่องว่างรอบคอมม่าทั้งหมด (เช่น 'คำ , คำ' -> 'คำ,คำ')
            cleaned_response = cleaned_response.replace(' ,', ',').replace(', ', ',')
            # B. ลบจุลภาคซ้ำซ้อน
            cleaned_response = re.sub(r',+', ',', cleaned_response)
            
            # 4. ประมวลผลข้อความ: แยกด้วยจุลภาค (,)
            words = [word.strip() for word in cleaned_response.split(',') if word.strip()]
            
            # 5. [สำคัญ] ลบช่องว่างภายในคำทั้งหมด (เพราะในภาษาไทยถือเป็น noise ที่ทำให้คำขาด)
            words = [w.replace(' ', '').strip() for w in words]
            
            # 6. ตัดให้เหลือแค่ 25 คำแรก
            if len(words) > count:
                words = words[:count]
            
            print(f"DEBUG: Final words list count: {len(words)}")
            print(f"DEBUG: Final words list: {words}")
            
            return words
            
        except Exception as e:
            print(f"ERROR: AI Assistant failed: {e}")
            return []