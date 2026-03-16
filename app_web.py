import streamlit as st
import google.generativeai as genai
import pandas as pd
import random
from gtts import gTTS
import io
from PIL import Image
from streamlit_cropper import st_cropper
import datetime
import requests # メッセージ送信に必要です

# 1. ページ設定とデザイン
st.set_page_config(page_title="基礎シリーズ 英語②T（表現）", layout="centered")

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #ffffff 0%, #fff3e0 100%); }
    .main-title { color: #e67e22; text-align: center; font-weight: 700; padding-bottom: 10px; border-bottom: 3px solid #ffcc80; font-family: 'serif'; margin-bottom: 30px; }
    div[data-testid="stVerticalBlock"] > div:has(div.stTabs) { background-color: white !important; padding: 25px !important; border-radius: 15px !important; border: 1px solid #ffe0b2 !important; box-shadow: 4px 4px 10px rgba(255,165,0,0.05) !important; }
    div.stButton > button { background-color: #f39c12 !important; color: white !important; border-radius: 10px !important; height: 3.5em !important; font-weight: bold !important; border: none !important; }
    .explanation-label { color: #d35400; font-weight: bold; font-size: 1.2em; margin-top: 25px; margin-bottom: 10px; }
    .feedback-container { background-color: #fff9f0; padding: 25px; border-radius: 10px; border-left: 6px solid #f39c12; line-height: 1.8; font-size: 1.1em; color: #5d4037; }
    .feedback-container b, .feedback-container strong { font-family: 'serif'; font-size: 1.25em; color: #784212; background-color: #fff3e0; padding: 0 4px; border-radius: 4px; }
    .model-answer-text { font-family: 'serif'; font-size: 1.4em; color: #784212; font-weight: bold; margin-top: 20px; padding-top: 15px; border-top: 1px dashed #ffcc80; }
    .inner-label { font-weight: bold; color: #a04000; }
</style>
""", unsafe_allow_html=True)

# 2. 変数の初期化
for key in ['finished', 'score', 'current_idx', 'show_feedback', 'current_list', 'feedback_text']:
    if key not in st.session_state:
        st.session_state[key] = False if key in ['finished', 'show_feedback'] else (0 if key not in ['current_list', 'feedback_text'] else None)

# 3. AIの初期設定
if 'target_model' not in st.session_state or st.session_state.target_model is None:
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        flash_models = [m for m in available_models if 'flash' in m]
        st.session_state.target_model = flash_models[0] if flash_models else available_models[0]
    except:
        st.session_state.target_model = "models/gemini-1.5-flash"

# 4. データの読み込み
if 'all_questions' not in st.session_state:
    try:
        df = pd.read_csv('questions.csv')
        df.columns = df.columns.str.strip().str.lower()
        st.session_state.all_questions = df.to_dict('records')
    except Exception as e:
        st.error(f"CSV読み込みエラー: {e}")
        st.stop()

# --- サイドバー ---
st.sidebar.title("📚 Study Lab Menu")
if st.sidebar.button("リセット"):
    st.session_state.clear()
    st.rerun()

kous = sorted(list(set([q['kou'] for q in st.session_state.all_questions])))
selected_kous = st.sidebar.multiselect("講を選択", kous, default=[kous[0]] if kous else [])
order_type = st.sidebar.radio("出題順", ["順番通り", "ランダム"])

if st.sidebar.button("学習を開始する"):
    selected_data = [q for q in st.session_state.all_questions if q['kou'] in selected_kous]
    if selected_data:
        if order_type == "ランダム": random.shuffle(selected_data)
        st.session_state.current_list = selected_data
        st.session_state.current_idx = 0
        st.session_state.score = 0
        st.session_state.finished = False
        st.session_state.show_feedback = False
        st.rerun()

# --- メイン画面 ---
if st.session_state.current_list is None:
    st.markdown("<h1 class='main-title'>基礎シリーズ 英語②T（表現）</h1>", unsafe_allow_html=True)
    st.info("サイドバーから講を選んで開始してください。")
    st.stop()

if st.session_state.finished:
    st.markdown("<h1 class='main-title'>Result 🎉</h1>", unsafe_allow_html=True)
    st.balloons()
    st.stop()

st.markdown("<h1 class='main-title'>基礎シリーズ 英語②T（表現）</h1>", unsafe_allow_html=True)
progress = (st.session_state.current_idx) / len(st.session_state.current_list)
st.progress(progress)

q = st.session_state.current_list[st.session_state.current_idx]
st.markdown(f"<p style='color:#784212;'>第{q['no']}問（{q['kou']}）</p><h2 style='color:#784212;'>{q['japanese']}</h2>", unsafe_allow_html=True)

# --- タブエリア ---
tab1, tab2, tab3, tab4 = st.tabs(["📷 Photo", "⌨️ Type", "🎤 Voice", "💬 Support"])

with tab1:
    img_file = st.file_uploader("写真をアップ", type=['png', 'jpg', 'jpeg'], key=f"up_{st.session_state.current_idx}")
    cam_file = st.camera_input("撮影", key=f"cam_{st.session_state.current_idx}")
    raw_image = cam_file if cam_file else img_file
    cropped_image = st_cropper(Image.open(raw_image), realtime_update=True, box_color='#f39c12', aspect_ratio=None) if raw_image else None

with tab2: user_text = st.text_input("回答入力", key=f"text_{st.session_state.current_idx}")
with tab3: audio_file = st.audio_input("話して提出", key=f"audio_{st.session_state.current_idx}")

with tab4:
    st.subheader("👨‍🏫 開発者へメッセージ")
    # ★★★ ここにGASのURLを貼り付けてください ★★★
    WEB_APP_URL = "https://script.google.com/macros/s/AKfycbycMBPTDIHDXzExHx5IJOPGssrYshSiWXObhYrtbhLWKkWfjWgmLemgY5lVdCHRtA29pQ/exec" 
    
    with st.form(key="support_form", clear_on_submit=True):
        sender_name = st.text_input("お名前")
        msg_body = st.text_area("メッセージ")
        if st.form_submit_button("送信"):
            if WEB_APP_URL == "ここにコピーしたURLを貼り付けてください":
                st.error("URLが設定されていません。")
            elif msg_body:
                res = requests.post(WEB_APP_URL, json={"name": sender_name, "message": msg_body})
                st.success("先生に届けました！") if res.status_code == 200 else st.error("送信失敗")

# --- 採点ボタン ---
if st.button("採点する"):
    with st.spinner("添削中..."):
        try:
            model = genai.GenerativeModel(st.session_state.target_model)
            inst = f"生徒の回答を正解例『{q['english']}』と比較。1行目に文字起こし、次に日本語で添削。英文は太字。正解なら『正解です』と含める。"
            if audio_file: res = model.generate_content([inst, {"mime_type": "audio/wav", "data": audio_file.read()}])
            elif cropped_image: res = model.generate_content([inst, cropped_image])
            else: res = model.generate_content(f"{inst}\n生徒：{user_text}")
            st.session_state.feedback_text, st.session_state.show_feedback = res.text, True
            if "正解" in res.text: st.session_state.score += 1; st.balloons()
        except Exception as e: st.error(f"Error: {e}")

if st.session_state.show_feedback:
    st.markdown(f"<div class='feedback-container'><div>{st.session_state.feedback_text}</div><div class='model-answer-text'><span class='inner-label'>模範解答：</span>{q['english']}</div></div>", unsafe_allow_html=True)
    st.audio(io.BytesIO(gTTS(q['english'], lang='en')._write_to_fp(io.BytesIO()).getvalue())) if st.button("次の問題へ") else st.empty()
