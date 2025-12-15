import random
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black, white, lightgrey, HexColor 
from reportlab.lib.utils import ImageReader 

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

    def generate_cards_data(self, words, num_cards=1, grid_size=5):
        """สุ่มคำศัพท์ลงตาราง"""
        cards = []
        total_cells = grid_size * grid_size
        center_index = total_cells // 2
        
        words_for_card = words + [""] * max(0, total_cells - len(words))

        for _ in range(num_cards):
            card = random.sample(words_for_card, total_cells)
            
            if grid_size % 2 != 0:
                card[center_index] = "FREE"
                
            cards.append(card)
            
        return cards

    def create_pdf_bytes(self, cards_data, title="Bingo Game", grid_size=5, 
                         bg_color="#FFFFFF", text_color="#000000", 
                         free_space_color="#F0F8FF", logo_file=None):
        """
        สร้างไฟล์ PDF พร้อมรองรับการปรับแต่งสีและโลโก้
        """
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        canvas_text_color = HexColor(text_color)
        canvas_bg_color = HexColor(bg_color)
        canvas_free_color = HexColor(free_space_color)
        
        margin = 50
        table_width = width - (2 * margin)
        cell_size = table_width / grid_size
        
        logo_size = 60 
        logo_x = margin 
        logo_y = height - 120 
        
        for card in cards_data:
            # วาดพื้นหลังทั้งหน้าด้วยสีพื้นหลัง
            c.setFillColor(canvas_bg_color)
            c.rect(0, 0, width, height, fill=1)
            
            # วาดโลโก้/รูปภาพ
            if logo_file is not None:
                try:
                    # ต้อง reset pointer ของไฟล์ที่ถูกอัปโหลดทุกครั้งที่วาด
                    logo_file.seek(0) 
                    image_reader = ImageReader(logo_file)
                    c.drawImage(image_reader, logo_x, logo_y, width=logo_size, height=logo_size)
                except Exception as e:
                    print(f"Error drawing image: {e}")
                    pass
            
            # วาดหัวข้อ
            c.setFillColor(canvas_text_color)
            c.setFont(self.font_name, 30)
            c.drawCentredString(width / 2, height - 80, title)
            
            # เริ่มวาดตาราง
            start_y = height - 150
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
                    text_y = y - (cell_size / 2) - 5 
                    c.drawCentredString(x + (cell_size / 2), text_y, str(word))
            
            c.showPage()
            
        c.save()
        buffer.seek(0)
        return buffer