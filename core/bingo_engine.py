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

    # 💡 FIX 1: ดึง 'คำตอบ' มาใช้ในการ์ดแทน 'คำถาม' 
    def generate_cards_data(self, qa_pairs: List[str], num_cards: int = 1, grid_size: int = 5) -> List[List[str]]:
        """
        สุ่มคำตอบลงตารางสำหรับผู้เล่น โดยใช้เพียง 25 คู่แรกจากรายการ Q&A
        """
        cards = []
        total_cells = grid_size * grid_size
        center_index = total_cells // 2
        
        # 1. ใช้ Q&A สำหรับทำตารางแค่ 25 คู่แรกเท่านั้น
        qa_for_cards = qa_pairs[:25]
        
        # 2. ดึงเฉพาะ 'คำตอบ' (ส่วนหลังเครื่องหมาย ':') มาใช้ในการ์ด
        answers = []
        for pair in qa_for_cards: 
            _, _, a = pair.partition(':')
            
            # ใช้คำตอบ แต่ถ้าไม่มีคำตอบ (Input ผิดพลาด) ให้ใช้คำถามแทน
            answer_to_use = a.strip()
            if not answer_to_use:
                q, _, _ = pair.partition(':')
                answer_to_use = q.strip()

            answers.append(answer_to_use)

        # 3. เตรียมคำศัพท์สำหรับการ์ด
        words_for_card = answers + [""] * max(0, total_cells - len(answers))

        for _ in range(num_cards):
            card = random.sample(words_for_card, total_cells)
            
            if grid_size % 2 != 0:
                card[center_index] = "FREE"
                
            cards.append(card)
        return cards
    
    # 💡 FIX 2.1: Text Wrapping Helper สำหรับช่องบิงโก
    def _wrap_text_to_lines_fixed(self, c, text, font_name, max_width, font_size=12, min_font_size=8):
        """Helper function สำหรับตัดข้อความในช่องบิงโก (ใช้ขนาด 12pt คงที่)"""
        
        # ต้องลงทะเบียนฟอนต์ทุกครั้ง (ป้องกันปัญหาของ reportlab)
        pdfmetrics.registerFont(TTFont(font_name, self.font_path))
        
        words = text.split()
        lines = []
        current_line = ""
        
        # ลองใช้ Font Size 12pt ก่อน
        c.setFont(font_name, font_size)
        
        for word in words:
            test_line = (current_line + " " + word).strip()
            
            # ตรวจสอบความยาวของบรรทัด
            if pdfmetrics.stringWidth(test_line, font_name, font_size) < max_width - 10: # -10 คือ padding
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
            
        # ถ้าข้อความยาวเกินไป (เกิน 4 บรรทัด) อาจต้องลดขนาดฟอนต์
        if len(lines) > 4 and font_size > min_font_size:
            # 💡 FIX: แก้ไขการเรียกตัวเองซ้ำ (Recursive Call) โดยเพิ่ม 'c' (canvas)
            # ใช้ขนาดเล็กสุด (8pt) แล้วลองตัดใหม่
            return self._wrap_text_to_lines_fixed(c, text, font_name, max_width, min_font_size, min_font_size)
            
        return lines, font_size 


    # 💡 MODIFIED: ใช้ Text Wrapping ในช่อง
    def create_pdf_bytes(self, cards_data: List[List[str]], title: str, grid_size: int, bg_color: str, text_color: str, free_space_color: str, logo_file: Any = None) -> bytes:
        
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
            # ... (Title, Logo, Card Index Drawing Unchanged) ...
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
            
            c.setFont(self.font_name, 12)
            c.drawString(width - margin - 50, height - 55, f"Card {card_index + 1}")

            # เริ่มวาดตาราง
            start_y = height - 100
            
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
                    
                    # 3. วาดข้อความ (พร้อม Text Wrapping)
                    c.setFillColor(canvas_text_color)

                    if str(word) != "FREE":
                        # 💡 FIX: แก้ไขการเรียกฟังก์ชัน โดยเพิ่ม 'c' (canvas) เป็น Argument ตัวที่ 1
                        lines, font_size = self._wrap_text_to_lines_fixed(c, str(word), self.font_name, cell_size)
                        
                        line_spacing = font_size + 2 
                        total_text_height = len(lines) * line_spacing
                        
                        # คำนวณตำแหน่ง Y เพื่อจัดกึ่งกลางแนวตั้ง
                        start_text_y = y - (cell_size / 2) + (total_text_height / 2) - font_size
                        
                        c.setFont(self.font_name, font_size)
                        for line in lines:
                            # drawCentredString สำหรับจัดกึ่งกลางแนวนอน
                            c.drawCentredString(x + (cell_size / 2), start_text_y, line)
                            start_text_y -= line_spacing # เลื่อนลงสำหรับบรรทัดถัดไป
                    else:
                        # Draw FREE space text (fixed size)
                        c.setFont(self.font_name, 16)
                        text_y = y - (cell_size / 2) - 5 
                        c.setFillColor(canvas_text_color)
                        c.drawCentredString(x + (cell_size / 2), text_y, str(word))
            
            c.showPage()
            
        c.save()
        buffer.seek(0)
        return buffer.read()


    # 💡 FIX 3: Text Wrapping Helper และปรับ spacing สำหรับ Caller Sheet
    def _draw_wrapped_line(self, c, text, x, y, max_width, font_size, font_name):
        """Helper function สำหรับตัดข้อความใน Caller Sheet"""
        c.setFont(font_name, font_size)
        
        words = text.split()
        lines = []
        current_line = ""
        
        # ต้องลงทะเบียนฟอนต์ทุกครั้ง (ป้องกันปัญหาของ reportlab)
        pdfmetrics.registerFont(TTFont(font_name, self.font_path)) 
        
        for word in words:
            test_line = (current_line + " " + word).strip()
            if pdfmetrics.stringWidth(test_line, font_name, font_size) < max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
            
        line_spacing = font_size + 2
        current_y = y
        
        for line in lines:
            c.drawString(x, current_y, line)
            current_y -= line_spacing 
        
        return len(lines) * line_spacing # Return total height used

    # 💡 MODIFIED: ปรับปรุง Caller Sheet เพื่อป้องกันข้อความซ้อนทับและเพิ่ม Text Wrapping
    def create_caller_sheet_pdf_bytes(self, qa_pairs: List[str], title: str) -> bytes:
        """
        สร้าง PDF ที่มีรายการคำถามและคำตอบทั้งหมด (จัดเรียงแบบสุ่ม) สำหรับผู้ดำเนินเกม 
        """
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        margin = 72
        
        caller_qa_pairs = qa_pairs.copy()
        random.shuffle(caller_qa_pairs)

        # --- ตั้งค่า Title ---
        c.setFillColor(black)
        c.setFont(self.font_name, 30)
        c.drawCentredString(width / 2, height - 80, f"ชุดดำเนินเกม (คำถามและคำตอบ): {title}")
        c.setFont(self.font_name, 14)
        
        # เพิ่ม Note
        c.setFillColor(HexColor("#FF4500")) # Orange Red
        c.drawString(margin, height - 100, f"รายการที่ 1-25 คือคำถามหลัก | รายการที่ 26-{len(qa_pairs)} คือคำถามสำรอง (สำหรับเกมยืดเยื้อ)")
        c.setFillColor(black) # รีเซ็ตสี

        # 💡 FIX: กำหนดความสูงที่ใช้สำหรับ 1 รายการ (item block) ให้มากขึ้น
        item_block_height = 80 
        start_y_content = height - 130 
        
        # จัดคอลัมน์
        cols = 2  
        col_width = (width - 2 * margin) / cols
        
        # คำนวณจำนวนคำต่อคอลัมน์ต่อหน้าเพื่อจัดการหน้ากระดาษ
        max_items_per_col = int((start_y_content - margin) / item_block_height)
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
            current_y = start_y_content - (row_index * item_block_height)
            
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

            # วาดหมายเลขนำหน้าและคำถาม (พร้อม Text Wrapping)
            q_line = f"{item_number}. คำถาม: {question}"
            # ใช้พื้นที่ col_width - 10pt
            q_used_height = self._draw_wrapped_line(c, q_line, current_x, current_y, col_width - 10, 14, self.font_name)
            
            # วาดคำตอบ (เยื้องลงมาเล็กน้อย พร้อม Text Wrapping)
            c.setFillColor(HexColor("#32CD32")) # สีเขียว (Lime Green) สำหรับคำตอบ
            a_line = f"   คำตอบ: {answer}"
            # ตำแหน่ง Y สำหรับคำตอบ: current_y (บนสุดของบรรทัด Q) - q_used_height - 5pt padding
            a_start_y = current_y - q_used_height - 5 
            # ใช้พื้นที่ col_width - 20pt
            self._draw_wrapped_line(c, a_line, current_x + 10, a_start_y, col_width - 20, 12, self.font_name)
            
            c.setFillColor(black) # รีเซ็ตสีสำหรับรายการถัดไป
            
        c.save()
        buffer.seek(0)
        return buffer.read()