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

    def generate_cards_data(self, words: List[str], num_cards: int = 1, grid_size: int = 5) -> List[List[str]]:
        """สุ่มคำศัพท์ลงตาราง"""
        cards = []
        total_cells = grid_size * grid_size
        center_index = total_cells // 2
        
        # เติมช่องว่างถ้าคำศัพท์ไม่พอ
        words_for_card = words + [""] * max(0, total_cells - len(words))

        for _ in range(num_cards):
            # สุ่มคำศัพท์
            card = random.sample(words_for_card, total_cells)
            
            # ใส่ FREE SPACE ถ้าขนาดเป็นเลขคี่
            if grid_size % 2 != 0:
                card[center_index] = "FREE"
                
            cards.append(card)
        return cards

    def create_pdf_bytes(self, cards_data: List[List[str]], title: str, grid_size: int, bg_color: str, text_color: str, free_space_color: str, logo_file: Any = None) -> bytes:
        """
        สร้างไฟล์ PDF สำหรับการ์ดผู้เล่น
        """
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        margin = 30
        
        # แปลงสี Hex เป็น ReportLab Color Object
        canvas_bg_color = HexColor(bg_color)
        canvas_text_color = HexColor(text_color)
        canvas_free_color = HexColor(free_space_color)
        
        # คำนวณขนาดการ์ดและช่อง
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
                    
                    # 3. วาดข้อความ
                    c.setFillColor(canvas_text_color)
                    text_y = y - (cell_size / 2) - 5 # ปรับแกน Y นิดหน่อยให้กลาง
                    c.drawCentredString(x + (cell_size / 2), text_y, str(word))
            
            # ขึ้นหน้าใหม่สำหรับการ์ดถัดไป
            c.showPage()
            
        c.save()
        buffer.seek(0)
        return buffer.read()

    # 💡 NEW: ฟังก์ชันสำหรับสร้าง PDF ชุดคำศัพท์สำหรับผู้ดำเนินเกม (Caller Sheet)
    def create_caller_sheet_pdf_bytes(self, words: List[str], title: str) -> bytes:
        """
        สร้าง PDF ที่มีรายการคำศัพท์ทั้งหมดสำหรับผู้ดำเนินเกม (Game Caller)
        คำศัพท์จะถูกจัดเรียงแบบสุ่ม
        """
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        margin = 72
        
        # คัดลอกและสลับคำศัพท์เพื่อไม่ให้เรียงตามลำดับเดิม
        caller_words = words.copy()
        random.shuffle(caller_words)
        
        # --- ตั้งค่าหน้าแรก ---
        c.setFillColor(black)
        c.setFont(self.font_name, 30)
        c.drawCentredString(width / 2, height - 80, f"รายการคำศัพท์ (ชุดดำเนินเกม): {title}")

        c.setFont(self.font_name, 14)
        line_height = 20
        start_y_content = height - 100
        
        # จัดคอลัมน์
        cols = 3
        col_width = (width - 2 * margin) / cols
        
        # คำนวณจำนวนคำต่อคอลัมน์ต่อหน้าเพื่อจัดการหน้ากระดาษ
        max_items_per_col = int((start_y_content - margin) / line_height)
        items_per_page = max_items_per_col * cols
        
        for i, word in enumerate(caller_words):
            
            # ตรวจสอบว่าต้องขึ้นหน้าใหม่หรือไม่
            if i > 0 and i % items_per_page == 0:
                 c.showPage()
                 c.setFillColor(black)
                 c.setFont(self.font_name, 20)
                 c.drawCentredString(width / 2, height - 50, f"รายการคำศัพท์ (ต่อ)")
                 c.setFont(self.font_name, 14)
                 
                 # รีเซ็ตตำแหน่ง Y สำหรับหน้าใหม่
                 start_y_content = height - 100
                 
            # คำนวณตำแหน่งคอลัมน์และบรรทัด
            item_on_page_index = i % items_per_page
            col_index = item_on_page_index // max_items_per_col
            row_index = item_on_page_index % max_items_per_col
            
            # ตำแหน่ง X และ Y
            current_x = margin + (col_index * col_width)
            current_y = start_y_content - (row_index * line_height)
            
            # วาดหมายเลขนำหน้า
            c.drawString(current_x, current_y, f"{i+1}. {word}")
            
        c.save()
        buffer.seek(0)
        return buffer.read()