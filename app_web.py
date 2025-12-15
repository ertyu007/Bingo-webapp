import streamlit as st
from core.bingo_engine import BingoEngine
from core.ai_assistant import AIAssistant 
from dotenv import load_dotenv 
import os 
import pandas as pd
from typing import List, Tuple, Any
# 💡 NEW IMPORTS: เพิ่ม io และ zipfile สำหรับการสร้าง ZIP
import io
import zipfile 

# --- สำคัญมาก: โหลด .env ก่อนรันโค้ดส่วนอื่น ---
load_dotenv() 

# 💡 NEW CONSTANT: กำหนดจำนวน Q&A ที่ต้องการทั้งหมด (หลัก 25 + สำรอง 10 = 35)
TOTAL_QA_COUNT = 35

# --- Initialize session state ---
if 'words_area_key' not in st.session_state:
    st.session_state.words_area_key = ""

# 💡 NEW HELPER FUNCTION: สร้าง ZIP File ในหน่วยความจำ
def create_zip_of_pdfs(pdf1_bytes: bytes, pdf1_name: str, pdf2_bytes: bytes, pdf2_name: str) -> bytes:
    """สร้าง ZIP File ในหน่วยความจำที่มี 2 ไฟล์ PDF อยู่ภายใน"""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(pdf1_name, pdf1_bytes)
        zip_file.writestr(pdf2_name, pdf2_bytes)
    zip_buffer.seek(0)
    return zip_buffer.read()

# 💡 FIX: ฟังก์ชัน Callback สำหรับปุ่ม AI 
def generate_ai_words_callback(topic):
    """
    Callback function เพื่อสร้างคู่คำถาม:คำตอบ และอัปเดต Session State
    """
    try:
        st.session_state.ai_status = f"กำลังให้ AI คิดคำถาม-คำตอบ {TOTAL_QA_COUNT} คู่สำหรับหัวข้อ '{topic}'..."
        
        with st.spinner("AI กำลังสร้าง Q&A..."):
            assistant = AIAssistant() 
            qa_pairs_list = assistant.generate_bingo_qa_pairs(topic, TOTAL_QA_COUNT)
        
        if qa_pairs_list:
            st.session_state.words_area_key = "\n".join(qa_pairs_list) 
            st.session_state.ai_status = f"✅ AI สร้างคำถาม-คำตอบสำเร็จ! ({len(qa_pairs_list)} คู่)"
        else:
            st.session_state.ai_status = "❌ AI ไม่สามารถสร้างคำถาม-คำตอบได้ กรุณาตรวจสอบ API Key หรือลองใหม่อีกครั้ง"
            
    except Exception as e:
        st.session_state.ai_status = f"เกิดข้อผิดพลาดจาก AI: {e}"


# --- ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Bingo Q&A Creator AI by MK (Q&A Mode)", page_icon="🎲", layout="wide")

# --- Sidebar (เมนูซ้ายมือ) ---
with st.sidebar:
    st.header("⚙️ ตั้งค่า (Settings)")
    grid_size = st.selectbox("ขนาดตาราง (Grid Size)", [3, 4, 5], index=2)
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
        f"✨ ใช้ AI ช่วยคิด Q&A ({TOTAL_QA_COUNT} คู่)",
        on_click=generate_ai_words_callback, 
        args=(ai_topic,),
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

    
    if len(qa_pairs_list) < min_words_required_for_card_data:
        st.error(f"❌ คู่คำถาม-คำตอบไม่พอครับ! ต้องการอย่างน้อย {min_words_required_for_card_data} คู่ (ตอนนี้มี {len(qa_pairs_list)} คู่) และต้องมีเครื่องหมาย ':'")
    else:
        try:
            engine = BingoEngine() 
            
            # 1. สร้างข้อมูลการ์ด
            cards_data = engine.generate_cards_data(qa_pairs_list, num_cards, grid_size)
            
            # 2. สร้าง PDF ชุดผู้เล่น (Player Cards)
            pdf_cards_bytes = engine.create_pdf_bytes(
                cards_data, 
                title=bingo_title, 
                grid_size=grid_size,
                bg_color=bg_color, 
                text_color=text_color,
                free_space_color=free_space_color,
                logo_file=uploaded_file
            )
            
            # 3. สร้าง PDF ชุดดำเนินเกม (Caller Sheet)
            pdf_caller_bytes = engine.create_caller_sheet_pdf_bytes(qa_pairs_list, bingo_title)

            # 4. สร้าง ZIP File รวม 2 ไฟล์
            zip_file_name = f"{bingo_title.replace(' ', '_')}_Bingo_Set.zip"
            player_pdf_name = f"Player_Cards_{num_cards}p.pdf"
            caller_pdf_name = "Caller_Sheet_QnA.pdf"

            zip_bytes = create_zip_of_pdfs(
                pdf_cards_bytes, player_pdf_name, 
                pdf_caller_bytes, caller_pdf_name
            )

            st.success(f"✅ สร้างชุดบิงโกสำเร็จ {num_cards} ใบ พร้อมชุดดำเนินเกม (Q&A) ในไฟล์ ZIP เดียว!")

            # 5. ปุ่มดาวน์โหลด ZIP File ปุ่มเดียว
            st.download_button(
                label=f"⬇️ ดาวน์โหลดชุดบิงโกทั้งหมด (.ZIP)",
                data=zip_bytes,
                file_name=zip_file_name,
                mime="application/zip",
                key='dl_bingo_set_zip'
            )
            
            # แสดงตัวอย่าง
            with st.expander("👀 ดูตัวอย่างคำถามในการ์ดใบที่ 1 (Questions Only)"):
                df = pd.DataFrame([cards_data[0][i:i + grid_size] for i in range(0, len(cards_data[0]), grid_size)])
                st.table(df)
                
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")
            st.warning("คำแนะนำ: อย่าลืมเอาไฟล์ฟอนต์ TH Niramit AS.ttf ไปใส่ในโฟลเดอร์ assets/fonts/ นะครับ")