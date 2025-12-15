import streamlit as st
from core.bingo_engine import BingoEngine
from core.ai_assistant import AIAssistant 
from dotenv import load_dotenv 
import os 
import pandas as pd
from typing import List, Tuple, Any

# --- สำคัญมาก: โหลด .env ก่อนรันโค้ดส่วนอื่น ---
load_dotenv() 

# --- Initialize session state ---
if 'words_area_key' not in st.session_state:
    st.session_state.words_area_key = ""

# 💡 NEW CONSTANT: กำหนดจำนวน Q&A ที่ต้องการทั้งหมด (หลัก 25 + สำรอง 10 = 35)
TOTAL_QA_COUNT = 35

# 💡 FIX: ฟังก์ชัน Callback สำหรับปุ่ม AI (เปลี่ยนไปใช้ TOTAL_QA_COUNT)
def generate_ai_words_callback(topic):
    """
    Callback function เพื่อสร้างคู่คำถาม:คำตอบ และอัปเดต Session State
    """
    try:
        # ใช้ TOTAL_QA_COUNT = 35 ในการเรียก AI
        st.session_state.ai_status = f"กำลังให้ AI คิดคำถาม-คำตอบ {TOTAL_QA_COUNT} คู่สำหรับหัวข้อ '{topic}'..."
        
        with st.spinner("AI กำลังสร้าง Q&A..."):
            assistant = AIAssistant() 
            qa_pairs_list = assistant.generate_bingo_qa_pairs(topic, TOTAL_QA_COUNT)
        
        if qa_pairs_list:
            st.session_state.words_area_key = "\n".join(qa_pairs_list) # ใช้ Newline เพื่อให้อ่านง่ายขึ้น
            st.session_state.ai_status = f"✅ AI สร้างคำถาม-คำตอบสำเร็จ! ({len(qa_pairs_list)} คู่)"
        else:
            st.session_state.ai_status = "❌ AI ไม่สามารถสร้างคำถาม-คำตอบได้ กรุณาตรวจสอบ API Key หรือลองใหม่อีกครั้ง"
            
    except Exception as e:
        st.session_state.ai_status = f"เกิดข้อผิดพลาดจาก AI: {e}"


# --- ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Bingo Creator AI by MK (Q&A Mode)", page_icon="🎲", layout="wide")

# --- Sidebar (เมนูซ้ายมือ) ---
with st.sidebar:
    st.header("⚙️ ตั้งค่า (Settings)")
    # ขนาดตาราง 5x5 ต้องมี 25 คำหลัก
    grid_size = st.selectbox("ขนาดตาราง (Grid Size)", [3, 4, 5], index=2)
    # 💡 min_words_required_for_card_data คือ 25 (5x5) หรือ 16 (4x4)
    min_words_required_for_card_data = grid_size * grid_size 
    num_cards = st.number_input("จำนวนใบที่ต้องการ (Cards)", min_value=1, max_value=50, value=5)
    
    st.markdown("---")
    st.header("🎨 การปรับแต่งสี")
    bg_color = st.color_picker("สีพื้นหลังการ์ด", "#FFFFFF")
    text_color = st.color_picker("สีตัวอักษร", "#000000")
    free_space_color = st.color_picker("สีช่อง FREE (ถ้ามี)", "#F0F8FF")
    
    st.markdown("---")
    st.header("🖼️ เพิ่มโลโก้/รูปภาพ")
    uploaded_file = st.file_uploader(
        "อัปโหลดโลโก้ (.png, .jpg)", 
        type=['png', 'jpg', 'jpeg']
    )
    
    st.markdown("---")
    if os.environ.get("GROQ_API_KEY"):
        st.success("🤖 Groq API Key โหลดสำเร็จ!")
    else:
        st.error("⚠️ กรุณาใส่ GROQ_API_KEY ในไฟล์ .env")
        
# --- Main Content (หน้าหลัก) ---
st.title("❓ Bingo Q&A Creator AI by MK")
st.markdown(f"สร้างการ์ดบิงโกด้วย **คำถาม** ที่กำหนด และสร้าง **ชุดดำเนินเกม** ที่มีทั้งคำถามและคำตอบสำรอง **({TOTAL_QA_COUNT} คู่)**")

bingo_title = st.text_input("ชื่อหัวข้อ/ชื่อบิงโก (Title)", value="บิงโก: ความรู้ทั่วไป")

col1, col2 = st.columns([0.7, 0.3])

with col1:
    st.text_area(
        "รายการคำถาม-คำตอบ (คั่นด้วยเครื่องหมาย : เช่น 'ไก่สีอะไร:สีขาว')",
        height=300,
        placeholder=f"ป้อนคู่คำถาม:คำตอบ ที่นี่ (ต้องการอย่างน้อย {min_words_required_for_card_data} คู่สำหรับการ์ด, และแนะนำ {TOTAL_QA_COUNT} คู่สำหรับเกมที่ยืดเยื้อ)",
        key="words_area_key" 
    )
    st.markdown(f"> **คำเตือน:** การ์ดผู้เล่นจะแสดงเฉพาะ **คำถาม** เท่านั้น")
    
with col2:
    st.markdown("#### หรือให้ AI ช่วยคิด Q&A")
    ai_topic = st.text_input("หัวข้อสำหรับ AI (เช่น ภูมิศาสตร์)", value="ภูมิศาสตร์โลก")
    
    st.button(
        f"✨ ใช้ AI ช่วยคิด Q&A ({TOTAL_QA_COUNT} คู่)", # 💡 แสดง 35 คู่
        on_click=generate_ai_words_callback, 
        args=(ai_topic,), # ไม่ต้องส่ง count เพราะใช้ค่าคงที่ TOTAL_QA_COUNT
        disabled=(not os.environ.get("GROQ_API_KEY"))
    )
    
    if 'ai_status' in st.session_state:
        if "✅" in st.session_state.ai_status:
            st.success(st.session_state.ai_status)
        elif "❌" in st.session_state.ai_status or "ข้อผิดพลาด" in st.session_state.ai_status:
            st.error(st.session_state.ai_status)
        elif "กำลัง" in st.session_state.ai_status:
            st.info(st.session_state.ai_status)

# --- ปุ่มสร้าง ---
if st.button("🚀 สร้างบิงโก Q&A (Generate)", type="primary"):
    
    words_input = st.session_state.get("words_area_key", "") 
    qa_pairs_list = [pair.strip() for pair in words_input.split('\n') if pair.strip() and ':' in pair]

    
    # 💡 CHECK: ตรวจสอบขั้นต่ำที่ต้องการ (min_words_required_for_card_data)
    if len(qa_pairs_list) < min_words_required_for_card_data:
        st.error(f"❌ คู่คำถาม-คำตอบไม่พอครับ! ต้องการอย่างน้อย {min_words_required_for_card_data} คู่ (ตอนนี้มี {len(qa_pairs_list)} คู่) และต้องมีเครื่องหมาย ':'")
    else:
        try:
            engine = BingoEngine() 
            
            # สร้างการ์ดผู้เล่น (จะดึงแค่ 25 คำถามแรก)
            cards_data = engine.generate_cards_data(qa_pairs_list, num_cards, grid_size)
            
            # 1. สร้าง PDF ชุดผู้เล่น (Player Cards)
            pdf_cards_bytes = engine.create_pdf_bytes(
                cards_data, 
                title=bingo_title, 
                grid_size=grid_size,
                bg_color=bg_color, 
                text_color=text_color,
                free_space_color=free_space_color,
                logo_file=uploaded_file
            )
            
            # 2. สร้าง PDF ชุดดำเนินเกม (Caller Sheet) - ใช้ทั้งหมดที่มี (สูงสุด 35 คู่)
            pdf_caller_bytes = engine.create_caller_sheet_pdf_bytes(qa_pairs_list, bingo_title)

            st.success(f"✅ สร้างชุดบิงโกสำเร็จ {num_cards} ใบ พร้อมชุดดำเนินเกม (Q&A)!")
            
            # --- ปุ่มดาวน์โหลด 2 ปุ่ม ---
            col_dl1, col_dl2 = st.columns(2)
            
            with col_dl1:
                st.download_button(
                    label="📥 ดาวน์โหลด [ชุดผู้เล่น] (Player Cards) PDF",
                    data=pdf_cards_bytes,
                    file_name=f"{bingo_title.replace(' ', '_')}_Player_Cards.pdf",
                    mime="application/pdf",
                    key='dl_player_cards' 
                )
            
            with col_dl2:
                st.download_button(
                    label="📥 ดาวน์โหลด [ชุดดำเนินเกม] (Q&A Caller Sheet) PDF",
                    data=pdf_caller_bytes,
                    file_name=f"{bingo_title.replace(' ', '_')}_Caller_Sheet.pdf",
                    mime="application/pdf",
                    key='dl_caller_sheet' 
                )
            
            # แสดงตัวอย่าง
            with st.expander("👀 ดูตัวอย่างคำถามในการ์ดใบที่ 1 (Questions Only)"):
                df = pd.DataFrame([cards_data[0][i:i + grid_size] for i in range(0, len(cards_data[0]), grid_size)])
                st.table(df)
                
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")
            st.warning("คำแนะนำ: อย่าลืมเอาไฟล์ฟอนต์ TH Niramit AS.ttf ไปใส่ในโฟลเดอร์ assets/fonts/ นะครับ")