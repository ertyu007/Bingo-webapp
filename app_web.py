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

# 💡 CONSTANT: กำหนดจำนวน Q&A ที่ต้องการทั้งหมด (หลัก 25 + สำรอง 10 = 35)
TOTAL_QA_COUNT = 35

# --- Initialize session state ---
if 'words_area_key' not in st.session_state:
    st.session_state.words_area_key = ""

# 💡 HELPER FUNCTION: สร้าง ZIP File ในหน่วยความจำ (Unchanged)
def create_zip_of_pdfs(pdf1_bytes: bytes, pdf1_name: str, pdf2_bytes: bytes, pdf2_name: str) -> bytes:
    """สร้าง ZIP File ในหน่วยความจำที่มี 2 ไฟล์ PDF อยู่ภายใน"""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(pdf1_name, pdf1_bytes)
        zip_file.writestr(pdf2_name, pdf2_name)
    zip_buffer.seek(0)
    return zip_buffer.read()

# 💡 FIX: ฟังก์ชัน Callback สำหรับปุ่ม AI (ปรับการแสดงสถานะ)
def generate_ai_words_callback(topic):
    """
    Callback function เพื่อสร้างคู่คำถาม:คำตอบ และอัปเดต Session State
    *** ใช้ st.spinner เพื่อแสดงสถานะแบบมีอนิเมชันระหว่างรัน ***
    """
    try:
        status_message = f"กำลังให้ AI คิดคำถาม-คำตอบ {TOTAL_QA_COUNT} คู่สำหรับหัวข้อ '{topic}'..."
        
        # 💡 ใช้ st.spinner แทน st.session_state.ai_status ในระหว่างการทำงาน
        with st.spinner(status_message):
            assistant = AIAssistant() 
            qa_pairs_list = assistant.generate_bingo_qa_pairs(topic, TOTAL_QA_COUNT)
        
        if qa_pairs_list:
            st.session_state.words_area_key = "\n".join(qa_pairs_list) 
            # 💡 Clean Status
            st.session_state.ai_status = f"สร้างคำถาม-คำตอบสำเร็จ ({len(qa_pairs_list)} คู่)"
            st.session_state.ai_status_type = "success"
        else:
            st.session_state.ai_status = "AI ไม่สามารถสร้างคำถาม-คำตอบได้ กรุณาตรวจสอบ API Key หรือลองใหม่อีกครั้ง"
            st.session_state.ai_status_type = "error"
            
    except Exception as e:
        st.session_state.ai_status = f"เกิดข้อผิดพลาดจาก AI: {e}"
        st.session_state.ai_status_type = "error"


# --- ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Bingo Q&A Creator AI by MK (Q&A Mode)", page_icon="🎲", layout="wide")

# --- Sidebar (เมนูซ้ายมือ) ---
with st.sidebar:
    st.header("⚙️ ตั้งค่า")
    
    # Grid Settings
    grid_size = st.selectbox("ขนาดตาราง (Grid Size)", [3, 4, 5], index=2)
    min_words_required_for_card_data = grid_size * grid_size
    num_cards = st.number_input("จำนวนใบที่ต้องการ (Cards)", min_value=1, max_value=50, value=5)
    
    st.markdown("---")
    st.header("🎨 การปรับแต่งสี")
    bg_color = st.color_picker("สีพื้นหลังการ์ด", "#FFFFFF")
    text_color = st.color_picker("สีตัวอักษร", "#000000")
    free_space_color = st.color_picker("สีช่อง FREE (ถ้ามี)", "#F0F8FF")
    
    st.markdown("---")
    st.header("🖼️ โลโก้")
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
st.markdown(f"สร้างการ์ดบิงโกด้วย **คำตอบ** และสร้าง **ชุดดำเนินเกม** ที่มีทั้งคำถามและคำตอบสำรอง **({TOTAL_QA_COUNT} คู่)**")

bingo_title = st.text_input("ชื่อหัวข้อ/ชื่อบิงโก (Title)", value="บิงโก: ความรู้ทั่วไป")

# 💡 REDESIGN: ใช้ Colummns สำหรับ Input และ AI
col_input, col_ai = st.columns([0.65, 0.35])

with col_input:
    st.subheader("1. รายการคำถาม-คำตอบ (Q:A)")
    st.text_area(
        "ป้อน Q:A ที่นี่ (คั่นด้วย : เช่น 'คำถาม:คำตอบ' และขึ้นบรรทัดใหม่)",
        height=300,
        placeholder=f"ป้อนคู่คำถาม:คำตอบ ที่นี่ (ต้องการอย่างน้อย {min_words_required_for_card_data} คู่สำหรับการ์ด 5x5 และแนะนำ {TOTAL_QA_COUNT} คู่สำหรับเกมที่ยืดเยื้อ)",
        key="words_area_key",
        label_visibility="collapsed"
    )
    st.markdown(f"> **คำเตือน:** การ์ดผู้เล่นจะแสดงเฉพาะ **คำตอบ** เท่านั้น")

with col_ai:
    st.subheader("2. สร้างด้วย AI (แนะนำ)")
    ai_topic = st.text_input("หัวข้อสำหรับ AI (เช่น ภูมิศาสตร์, ภาษาไทย ม.3)", value="ภูมิศาสตร์โลก")
    
    st.button(
        f"✨ ให้ AI สร้าง Q&A ({TOTAL_QA_COUNT} คู่)",
        on_click=generate_ai_words_callback, 
        args=(ai_topic,),
        disabled=(not os.environ.get("GROQ_API_KEY")),
        use_container_width=True
    )
    
    # 💡 CLEAN DEBUG: แสดงสถานะ AI ล่าสุด
    if 'ai_status' in st.session_state:
        status_type = st.session_state.get('ai_status_type', 'info')
        if status_type == "success":
            st.success(st.session_state.ai_status)
        elif status_type == "error":
            st.error(st.session_state.ai_status)
        else:
            st.info(st.session_state.ai_status)


# --- ปุ่มสร้าง ---
st.markdown("---")
if st.button("🚀 สร้างชุดบิงโกทั้งหมด (Generate)", type="primary", use_container_width=True):
    
    words_input = st.session_state.get("words_area_key", "") 
    # กรอง Q:A ที่ถูกต้อง
    qa_pairs_list = [pair.strip() for pair in words_input.split('\n') if pair.strip() and ':' in pair]
    
    if len(qa_pairs_list) < min_words_required_for_card_data:
        st.error(f"❌ คู่คำถาม-คำตอบไม่พอครับ! ต้องการอย่างน้อย {min_words_required_for_card_data} คู่ (ตอนนี้มี {len(qa_pairs_list)} คู่) และต้องมีเครื่องหมาย ':'")
    else:
        try:
            # 💡 NEW DEBUG/ANIMATION: ใช้ st.status เพื่อแสดงสถานะแบบรวม
            with st.status("กำลังสร้างชุดบิงโกและไฟล์ ZIP...", expanded=True) as status:
                
                status.update(label="1/3: กำลังเตรียมข้อมูลการ์ด (ดึงคำตอบ)...", state="running")
                engine = BingoEngine() 
                cards_data = engine.generate_cards_data(qa_pairs_list, num_cards, grid_size)
                
                status.update(label="2/3: กำลังสร้างไฟล์ PDF สำหรับผู้เล่น...", state="running")
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
                
                status.update(label="2/3: กำลังสร้างไฟล์ PDF สำหรับชุดดำเนินเกม (Caller Sheet)...", state="running")
                # 3. สร้าง PDF ชุดดำเนินเกม (Caller Sheet)
                pdf_caller_bytes = engine.create_caller_sheet_pdf_bytes(qa_pairs_list, bingo_title)

                status.update(label="3/3: กำลังรวมไฟล์เป็น ZIP...", state="running")
                # 4. สร้าง ZIP File รวม 2 ไฟล์
                zip_file_name = f"{bingo_title.replace(' ', '_')}_Bingo_Set.zip"
                player_pdf_name = f"Player_Cards_{num_cards}p.pdf"
                caller_pdf_name = "Caller_Sheet_QnA.pdf"

                # 💡 Note: ถ้าไม่พบไฟล์ zipfile.writestr ต้องใช้ .writestr(filename, data)
                zip_bytes = create_zip_of_pdfs(
                    pdf_cards_bytes, player_pdf_name, 
                    pdf_caller_bytes, caller_pdf_name
                )
                
                # 💡 FINAL STATUS: แสดงสถานะสุดท้ายที่สำเร็จ
                status.update(label=f"✅ สร้างชุดบิงโกสำเร็จ! จำนวน {num_cards} ใบ พร้อมชุดดำเนินเกม", state="complete")

            # 5. ปุ่มดาวน์โหลด ZIP File ปุ่มเดียว (ดีไซน์สะอาดตา)
            st.download_button(
                label=f"ดาวน์โหลดชุดบิงโกทั้งหมด (.ZIP)",
                data=zip_bytes,
                file_name=zip_file_name,
                mime="application/zip",
                key='dl_bingo_set_zip',
                type="secondary",
                use_container_width=True
            )
            
            # แสดงตัวอย่าง
            with st.expander("👀 ดูตัวอย่างคำตอบในการ์ดใบที่ 1 (Answers Only)"):
                df = pd.DataFrame([cards_data[0][i:i + grid_size] for i in range(0, len(cards_data[0]), grid_size)])
                st.table(df)
                
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")
            st.warning("คำแนะนำ: อย่าลืมเอาไฟล์ฟอนต์ TH Niramit AS.ttf ไปใส่ในโฟลเดอร์ assets/fonts/ นะครับ")