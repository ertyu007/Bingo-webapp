import streamlit as st
from core.bingo_engine import BingoEngine
from core.ai_assistant import AIAssistant 
from dotenv import load_dotenv 
import os 
import pandas as pd

# --- สำคัญมาก: โหลด .env ก่อนรันโค้ดส่วนอื่น ---
load_dotenv() 

# 💡 FIX: ฟังก์ชัน Callback สำหรับปุ่ม AI (ปรับปรุง)
def generate_ai_words_callback(topic, count):
    """
    Callback function เพื่อสร้างคำศัพท์และอัปเดต Session State
    *** FIX: อัปเดตค่าโดยตรงผ่าน key ของ Text Area ***
    """
    try:
        # แสดงสถานะการทำงานทันที
        st.session_state.ai_status = f"กำลังให้ AI คิดคำศัพท์ 25 คำสำหรับหัวข้อ '{topic}'..."
        
        with st.spinner("AI กำลังสร้างคำศัพท์..."):
            assistant = AIAssistant() 
            words_list_from_ai = assistant.generate_bingo_words(topic, count)
        
        if words_list_from_ai:
            # 💡 FIX สำคัญที่สุด: ตั้งค่าโดยตรงไปที่ KEY ของ widget (words_area_key)
            st.session_state.words_area_key = ", ".join(words_list_from_ai)
            st.session_state.ai_status = "✅ AI สร้างคำศัพท์สำเร็จ!"
        else:
            st.session_state.ai_status = "❌ AI ไม่สามารถสร้างคำศัพท์ได้ กรุณาตรวจสอบ API Key หรือลองใหม่อีกครั้ง"
            
    except Exception as e:
        st.session_state.ai_status = f"เกิดข้อผิดพลาดจาก AI: {e}"


# --- ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Bingo Creator AI by MK", page_icon="🎲", layout="wide")

# --- Sidebar (เมนูซ้ายมือ) ---
with st.sidebar:
    st.header("⚙️ ตั้งค่า (Settings)")
    grid_size = st.selectbox("ขนาดตาราง (Grid Size)", [3, 4, 5], index=2)
    min_words = grid_size * grid_size
    num_cards = st.number_input("จำนวนใบที่ต้องการ (Cards)", min_value=1, max_value=50, value=5)
    
    st.markdown("---")
    st.header("🎨 การปรับแต่งสี (Phase 3)")
    bg_color = st.color_picker("สีพื้นหลังการ์ด", "#FFFFFF")
    text_color = st.color_picker("สีตัวอักษร", "#000000")
    free_space_color = st.color_picker("สีช่อง FREE (ถ้ามี)", "#F0F8FF")
    
    st.markdown("---")
    st.header("🖼️ เพิ่มโลโก้/รูปภาพ (Phase 4)")
    uploaded_file = st.file_uploader(
        "อัปโหลดโลโก้ (.png, .jpg)", 
        type=['png', 'jpg', 'jpeg']
    )
    
    st.markdown("---")
    try:
        if os.environ.get("GROQ_API_KEY"):
            st.success("🤖 Groq API Key โหลดสำเร็จ!")
        else:
            st.error("⚠️ กรุณาใส่ GROQ_API_KEY ในไฟล์ .env")
    except:
         st.warning("กำลังตรวจสอบสถานะ API Key...")
        
# --- Main Content (หน้าหลัก) ---
st.title("🎲 Bingo Creator AI by MK")
st.markdown("สร้างการ์ดบิงโกด้วยคำศัพท์ภาษาไทยที่คุณกำหนดเอง หรือให้ AI ช่วยคิด!")

bingo_title = st.text_input("ชื่อหัวข้อ/ชื่อบิงโก (Title)", value="บิงโก: หัวข้อสุดฮิต")

col1, col2 = st.columns([0.7, 0.3])

with col1:
    words_input_widget = st.text_area( # เปลี่ยนชื่อตัวแปรเพื่อไม่ให้สับสน
        "คำศัพท์ (คั่นด้วยจุลภาค , )",
        height=300,
        placeholder="ป้อนคำศัพท์ที่นี่ (ต้องการอย่างน้อย 25 คำสำหรับ 5x5)",
        value="", # ตั้งค่าเริ่มต้นเป็นว่างเปล่า
        key="words_area_key" # *** ใช้ key นี้เป็นตัวควบคุมหลัก ***
    )
    
with col2:
    st.markdown("#### หรือให้ AI ช่วยคิดคำ")
    ai_topic = st.text_input("หัวข้อสำหรับ AI", value="ผลไม้ไทย")
    
    # ใช้ on_click callback
    st.button(
        "✨ ใช้ AI ช่วยคิดคำ (Llama-3)", 
        on_click=generate_ai_words_callback, 
        args=(ai_topic, 25),
        disabled=(not os.environ.get("GROQ_API_KEY"))
    )
    
    # แสดงสถานะ AI
    if 'ai_status' in st.session_state:
        if "✅" in st.session_state.ai_status:
            st.success(st.session_state.ai_status)
        elif "❌" in st.session_state.ai_status or "ข้อผิดพลาด" in st.session_state.ai_status:
            st.error(st.session_state.ai_status)
        elif "กำลัง" in st.session_state.ai_status:
            st.info(st.session_state.ai_status)

# --- ปุ่มสร้าง ---
if st.button("🚀 สร้างบิงโก (Generate)", type="primary"):
    
    # 💡 FIX: ดึงค่าล่าสุดจาก Session State โดยตรงผ่าน KEY
    words_input = st.session_state.get("words_area_key", "") # ดึงค่าจาก key
    words_list = [w.strip() for w in words_input.split(',') if w.strip()]
    
    if len(words_list) < min_words:
        st.error(f"❌ คำศัพท์ไม่พอครับ! ต้องการอย่างน้อย {min_words} คำ (ตอนนี้มี {len(words_list)} คำ)")
    else:
        try:
            engine = BingoEngine() 
            cards_data = engine.generate_cards_data(words_list, num_cards, grid_size)
            
            pdf_bytes = engine.create_pdf_bytes(
                cards_data, 
                title=bingo_title, 
                grid_size=grid_size,
                bg_color=bg_color, 
                text_color=text_color,
                free_space_color=free_space_color,
                logo_file=uploaded_file
            )
            
            st.success(f"✅ สร้างบิงโกสำเร็จ {num_cards} ใบ! พร้อมสีและโลโก้ที่คุณกำหนด")
            
            st.download_button(
                label="📥 ดาวน์โหลดไฟล์ PDF",
                data=pdf_bytes,
                file_name="bingo-cards.pdf",
                mime="application/pdf"
            )
            
            with st.expander("👀 ดูตัวอย่างข้อมูลในการ์ดใบที่ 1"):
                df = pd.DataFrame([cards_data[0][i:i + grid_size] for i in range(0, len(cards_data[0]), grid_size)])
                st.table(df)
                
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")
            st.warning("คำแนะนำ: อย่าลืมเอาไฟล์ฟอนต์ TH Niramit AS.ttf ไปใส่ในโฟลเดอร์ assets/fonts/ นะครับ")