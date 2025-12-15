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
        # ดึง API Key จาก Environment Variable
        self.api_key = os.environ.get("GROQ_API_KEY")
        print(f"DEBUG: API Key loaded status: {'Success' if self.api_key else 'Failed'}")
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set in environment variables or .env file.")
        
        # ตั้งค่า Groq Client
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.1-8b-instant" # โมเดลเร็วที่เราเลือก
        
        # 💡 SYSTEM PROMPT: เน้นย้ำว่าต้องสร้าง 35 คู่ 
        self.system_prompt = (\
            "You are an expert Q&A generator for a Bingo game. "\
            "Your task is to generate a comma-separated list of EXACTLY 35 pairs of 'Question:Answer' "\
            "based on the user's topic. The Question should be used on the Bingo card, and the Answer is for the host. "\
            "**CRITICAL:** ONLY return the list of pairs separated by a colon, then by a comma. "\
            "DO NOT include any conversation, titles, numbering, or newlines. "\
            "Example of correct output: 'Who painted the Mona Lisa?:Leonardo da Vinci, What is the largest planet?:Jupiter, ...' (35 pairs)"\
        )

    def generate_bingo_qa_pairs(self, topic: str, count: int) -> List[str]:
        """
        เรียกใช้ AI เพื่อสร้างคู่คำถาม:คำตอบตามหัวข้อที่กำหนด พร้อมเงื่อนไขการลองใหม่ (Retry)
        """
        MAX_RETRIES = 3 # จำนวนครั้งสูงสุดที่อนุญาตให้ลองใหม่
        MIN_REQUIRED_PAIRS = 25 # ขั้นต่ำที่ยอมรับได้สำหรับตาราง 5x5
        
        # เก็บค่าล่าสุดหากล้มเหลว
        final_qa_pairs = []

        for attempt in range(MAX_RETRIES):
            start_time = time.time()
            user_prompt = f"Generate {count} pairs of 'Question:Answer' about the topic: {topic}. Output in Thai if possible, otherwise use English."
            
            # ต้องรีเซ็ต final_qa_pairs ก่อนเริ่ม attempt ใหม่
            current_qa_pairs = []

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
                
                # FINAL FIX LOGIC: ทำความสะอาดข้อความแบบเข้มงวด (Aggressive Filtering)
                cleaned_response = raw_response.strip()
                
                # 1. แทนที่ Newline ด้วยคอมม่า (,) และลบเลขนำหน้า (e.g., 1., 2.)
                cleaned_response = cleaned_response.replace('\n', ',')
                cleaned_response = re.sub(r'\s*\d+\.\s*', '', cleaned_response)
                
                # 2. 💡 CRITICAL: กรองอักขระที่ไม่ใช่ภาษาไทย/อังกฤษ/ตัวเลข/เครื่องหมายที่จำเป็น
                allowed_chars_regex = r'[^ก-๙a-zA-Z0-9\s:?,.\'"-]' 
                cleaned_response = re.sub(allowed_chars_regex, '', cleaned_response)
                
                # 3. จัดการช่องว่างแปลกปลอม (รวม \t, \xa0, \ufeff และช่องว่างหลายตัว) ด้วยช่องว่างเดี่ยว ' '
                cleaned_response = re.sub(r'[\s\t\r\xa0\ufeff\u2000-\u200A\u202F\u205F\u3000]+', ' ', cleaned_response).strip()
                
                # 4. จัดการช่องว่างรอบคอมม่าและคอมม่าซ้ำซ้อน
                cleaned_response = cleaned_response.replace(' ,', ',').replace(', ', ',')
                cleaned_response = re.sub(r',+', ',', cleaned_response)
                
                # 5. ประมวลผลข้อความ: แยกด้วยจุลภาค (,)
                qa_pairs = [pair.strip() for pair in cleaned_response.split(',') if pair.strip()]
                
                # 6. ตรวจสอบความถูกต้อง (ต้องมีเครื่องหมาย ':') และตัดให้เหลือแค่ 'count' คู่แรก
                for pair in qa_pairs:
                    # นำช่องว่างรอบเครื่องหมาย ':' ออกก่อนเช็ค
                    pair_cleaned = pair.replace(' : ', ':').replace(':', ':', 1)
                    
                    if ':' in pair_cleaned:
                        q, _, a = pair_cleaned.partition(':')
                        
                        # 💡 NEW: เช็คว่าทั้งคำถามและคำตอบไม่เป็นค่าว่าง
                        if q.strip() and a.strip():
                            current_qa_pairs.append(pair_cleaned.strip())
                
                if len(current_qa_pairs) > count:
                    current_qa_pairs = current_qa_pairs[:count]
                
                final_qa_pairs = current_qa_pairs # เก็บผลลัพธ์ที่ดีที่สุด
                current_count = len(final_qa_pairs)
                
                elapsed_time = time.time() - start_time
                print(f"DEBUG: AI Response Time: {elapsed_time:.2f}s (Attempt {attempt + 1}/{MAX_RETRIES})")
                print(f"DEBUG: Final Q&A pairs count: {current_count}")
                print(f"DEBUG: Final Q&A pairs (Sample): {final_qa_pairs[:5]}")
                
                # 💡 NEW: เงื่อนไขการตรวจสอบและลองใหม่ (Retry Check)
                if current_count >= MIN_REQUIRED_PAIRS:
                    # ถ้าจำนวนถึงขั้นต่ำที่จำเป็น (25 คู่) ถือว่าใช้ได้
                    print(f"DEBUG: Pair count ({current_count}) is sufficient (>= {MIN_REQUIRED_PAIRS}). Done.")
                    return final_qa_pairs
                else:
                    print(f"DEBUG: Pair count ({current_count}) is too low (< {MIN_REQUIRED_PAIRS}). Retrying...")
            
            except Exception as e:
                print(f"ERROR: AI generation failed (Attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                # ถ้าเกิดข้อผิดพลาดในการเรียก API
                if attempt < MAX_RETRIES - 1:
                    time.sleep(1) # พัก 1 วิ ก่อนลองใหม่
                else:
                    print("ERROR: Maximum retries reached due to error. Returning best effort result.")
                    # จบการทำงานด้วยการคืนค่าล่าสุดที่มี
                    break 

        # คืนค่าสุดท้ายที่ได้มา (ถึงแม้จะน้อยกว่า 25)
        return final_qa_pairs