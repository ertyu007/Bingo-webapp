import random
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black, white, lightgrey, HexColor 
from reportlab.lib.utils import ImageReader 
from typing import List, Tuple, Any

class BingoEngine:
    def __init__(self, font_path="assets/fonts/TH Niramit AS.ttf"):
        self.font_path = font_path
        self.font_name = "CustomFont"
        self.register_font()

    def register_font(self):
        """ลงทะเบียนฟอนต์ภาษาไทยเพื่อให้ PDF อ่านออก"""
        try:
            pdfmetrics.registerFont(TTFont(self.font_name, self.font_path))
        except:
            self.font_name = "Helvetica" # Fallback

    # 💡 UPDATED: รับรายการ Q&A (List[str]) และดึงเฉพาะ "คำถาม" 25 คู่แรก สำหรับการ์ดผู้เล่น
    def generate_cards_data(self, qa_pairs: List[str], num_cards: int = 1, grid_size: int = 5) -> List[List[str]]:
        """
        สุ่มคำถามลงตารางสำหรับผู้เล่น โดยใช้เพียง 25 คู่แรกจากรายการ Q&A
        """
        cards = []
        total_cells = grid_size * grid_size
        center_index = total_cells // 2
        
        # 1. ใช้คำถามสำหรับทำตารางแค่ 25 คำแรกเท่านั้น
        qa_for_cards = qa_pairs[:25]
        
        # 2. ดึงเฉพาะ 'คำถาม' (ส่วนแรกก่อนเครื่องหมาย ':') มาใช้ในการ์ด
        questions = []
        for pair in qa_for_cards: # ใช้เฉพาะ 25 คู่แรก
            q, _, _ = pair.partition(':')
            questions.append(q.strip())
        
        # ... (ส่วน Logic การสร้างตารางและสุ่มเหมือนเดิม) ...
        # เติมช่องว่างถ้าคำถามไม่พอ
        words_for_card = questions + [""] * max(0, total_cells - len(questions))

        for _ in range(num_cards):
            # สุ่มคำถาม
            card = random.sample(words_for_card, total_cells)
            
            # ใส่ FREE SPACE ถ้าขนาดเป็นเลขคี่
            if grid_size % 2 != 0:
                card[center_index] = "FREE"
                
            cards.append(card)
        return cards
    
    # ... (ส่วน create_pdf_bytes เหมือนเดิม) ...
    def create_pdf_bytes(self, cards_data: List[List[str]], title: str, grid_size: int, bg_color: str, text_color: str, free_space_color: str, logo_file: Any = None) -> bytes:
        # โค้ดส่วนนี้เหมือนเดิม 
        # ... 
        # (ตัดออกเพื่อความกระชับ)
        # ... 
        
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        margin = 30
        
        canvas_bg_color = HexColor(bg_color)
        canvas_text_color = HexColor(text_color)
        canvas_free_color = HexColor(free_space_color)
        
        card_width = (width - margin * 2) 
        cell_size = card_width / grid_size
        
        for card_index, card in enumerate(cards_data):
            # วาด Title และ Logo
            c.setFillColor(canvas_text_color)
            c.setFont(self.font_name, 30)
            c.drawCentredString(width / 2, height - 40, title)
            
            if logo_file is not None:
                try:
                    logo_image = ImageReader(logo_file)
                    logo_size = 50
                    c.drawImage(logo_image, margin, height - 60, width=logo_size, height=logo_size)
                except Exception as e:
                    print(f"Error drawing logo: {e}")
            
            # วาด "Card X of Y"
            c.setFont(self.font_name, 12)
            c.drawString(width - margin - 50, height - 55, f"Card {card_index + 1}")

            # เริ่มวาดตาราง
            start_y = height - 100
            c.setFont(self.font_name, 16)
            
            for row in range(grid_size):
                for col in range(grid_size):
                    x = margin + (col * cell_size)
                    y = start_y - (row * cell_size)
                    
                    word_idx = (row * grid_size) + col
                    word = card[word_idx]
                    
                    # 1. วาดช่องพื้นหลัง
                    cell_fill_color = canvas_bg_color
                    if word == "FREE":
                        cell_fill_color = canvas_free_color
                        
                    c.setFillColor(cell_fill_color)
                    c.rect(x, y - cell_size, cell_size, cell_size, fill=1)
                    
                    # 2. วาดกรอบสี่เหลี่ยม
                    c.setStrokeColor(canvas_text_color) 
                    c.rect(x, y - cell_size, cell_size, cell_size, fill=0) 
                    
                    # 3. วาดข้อความ (คำถาม)
                    c.setFillColor(canvas_text_color)
                    text_y = y - (cell_size / 2) - 5 
                    c.drawCentredString(x + (cell_size / 2), text_y, str(word))
            
            c.showPage()
            
        c.save()
        buffer.seek(0)
        return buffer.read()


    # 💡 UPDATED: Caller Sheet ใช้ Q&A ทั้งหมด (35 คู่)
    def create_caller_sheet_pdf_bytes(self, qa_pairs: List[str], title: str) -> bytes:
        """
        สร้าง PDF ที่มีรายการคำถามและคำตอบทั้งหมด (จัดเรียงแบบสุ่ม) สำหรับผู้ดำเนินเกม 
        """
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        margin = 72
        
        # คัดลอกและสลับคู่ Q&A ทั้งหมด (35 คู่) เพื่อใช้ขาน
        caller_qa_pairs = qa_pairs.copy()
        random.shuffle(caller_qa_pairs)
        
        # ... (ส่วน Logic การสร้าง PDF เหมือนเดิม) ...

        # --- ตั้งค่า Title ---
        c.setFillColor(black)
        c.setFont(self.font_name, 30)
        c.drawCentredString(width / 2, height - 80, f"ชุดดำเนินเกม (คำถามและคำตอบ): {title}")
        c.setFont(self.font_name, 14)
        # 💡 เพิ่ม Note เกี่ยวกับคำถามสำรอง
        c.setFillColor(HexColor("#FF4500")) # Orange Red
        c.drawString(margin, height - 100, f"รายการที่ 1-25 คือคำถามหลัก | รายการที่ 26-35 คือคำถามสำรอง (สำหรับเกมยืดเยื้อ)")
        c.setFillColor(black) # รีเซ็ตสี

        line_height = 40 
        start_y_content = height - 130 # ปรับตำแหน่ง Y ลงมาเล็กน้อย
        
        # จัดคอลัมน์
        cols = 2  
        col_width = (width - 2 * margin) / cols
        
        # คำนวณจำนวนคำต่อคอลัมน์ต่อหน้าเพื่อจัดการหน้ากระดาษ
        max_items_per_col = int((start_y_content - margin) / line_height)
        items_per_page = max_items_per_col * cols
        
        for i, pair in enumerate(caller_qa_pairs):
            
            # ตรวจสอบว่าต้องขึ้นหน้าใหม่หรือไม่
            if i > 0 and i % items_per_page == 0:
                 c.showPage()
                 c.setFillColor(black)
                 c.setFont(self.font_name, 20)
                 c.drawCentredString(width / 2, height - 50, f"ชุดดำเนินเกม (ต่อ)")
                 c.setFont(self.font_name, 14)
                 start_y_content = height - 100
                 
            # คำนวณตำแหน่งคอลัมน์และบรรทัด
            item_on_page_index = i % items_per_page
            col_index = item_on_page_index // max_items_per_col
            row_index = item_on_page_index % max_items_per_col
            
            current_x = margin + (col_index * col_width)
            current_y = start_y_content - (row_index * line_height)
            
            # แยกคำถามและคำตอบ
            question, _, answer = pair.partition(':')
            question = question.strip()
            answer = answer.strip() if answer else "[ไม่มีคำตอบ]"
            
            # 💡 เพิ่มสีเตือนสำหรับคำถามสำรอง (รายการที่ 26 ขึ้นไป)
            item_number = i + 1
            if item_number > 25:
                 c.setFillColor(HexColor("#FF4500")) # สีส้มแดง
            else:
                 c.setFillColor(black) # สีดำ

            # วาดหมายเลขนำหน้าและคำถาม
            c.setFont(self.font_name, 14)
            c.drawString(current_x, current_y, f"{item_number}. คำถาม: {question}")
            
            # วาดคำตอบ (เยื้องลงมาเล็กน้อย)
            c.setFillColor(HexColor("#32CD32")) # สีเขียว (Lime Green) สำหรับคำตอบ
            c.setFont(self.font_name, 12)
            c.drawString(current_x + 10, current_y - 15, f"   คำตอบ: {answer}")
            
            c.setFillColor(black) # รีเซ็ตสีสำหรับรายการถัดไป
            
        c.save()
        buffer.seek(0)
        return buffer.read()