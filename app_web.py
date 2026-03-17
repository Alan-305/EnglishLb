import streamlit as st
import google.generativeai as genai
import pandas as pd
import random
from gtts import gTTS
import io
from PIL import Image
from streamlit_cropper import st_cropper
import datetime
import requests
import re

# 1. ページ設定
st.set_page_config(page_title="基礎シリーズ_英語②_T_重要文例", layout="centered")

# 2. デザイン設定（CSS）
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #ffffff 0%, #fff3e0 100%); }
    .main-title { 
        color: #e67e22; text-align: center; font-weight: 700; 
        font-size: 1.5em; padding: 10px 0; border-bottom: 3px solid #ffcc80; 
        font-family: 'serif'; margin-bottom: 15px;
    }
    [data-testid="stCameraInput"] { width: 100% !important; }
    [data-testid="stCameraInput"] video { border-radius: 10px !important; width: 100% !important; height: auto !important; aspect-ratio: 4/3 !important; }
    
    div.stButton > button { 
        background-color: #f39c12 !important; color: white !important; 
        border-radius: 15px !important; height: 3.5em !important; 
        font-size: 1.1em !important; font-weight: bold !important; 
        border: none !important; width: 100%; margin-bottom: 8px;
    }
    div[data-testid="stVerticalBlock"] > div:has(div.stTabs) { 
        background-color: white !important; padding: 15px !important; 
        border-radius: 15px !important; border: 1px solid #ffe0b2 !important; 
    }
    .feedback-container { background-color: #fff9f0; padding: 15px; border-radius: 10px; border-left: 6px solid #f39c12; font-size: 1.1em; color: #5d4037; }
    
    .feedback-container b, .feedback-container strong { 
        font-family: 'serif'; font-size: 1.35em; color: #784212; 
        background-color: #fff3e0; padding: 0 4px; font-weight: bold;
    }
    .model-answer-text { font-family: 'serif'; font-size: 1.4em; font-weight: bold; margin-top: 15px; color: #784212; border-top: 1px dashed #ffcc80; padding-top: 10px; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>基礎シリーズ_英語②_T_重要文例</h1>", unsafe_allow_html=True)

# 3. 変数の初期化
for key in ['finished', 'score', 'current_idx', 'show_feedback', 'current_list', 'feedback_text']:
    if key not in st.session_state:
        st.session_state[key] = False if key in ['finished', 'show_feedback'] else (0 if key not in ['current_list', 'feedback_text'] else None)

# 4. AI設定（Proモデルを使用）
if 'target_model' not in st.session_state or st.session_state.target_model is None:
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        st.session_state.target_model = "models/gemini-1.5-pro" # Pro版に固定
    except:
        st.session_state.target_model = "models/gemini-1.5-pro"

# 5. データの読み込み
if 'all_questions' not in st.session_state:
    try:
        df = pd.read_csv('questions.csv')
        df.columns = df.columns.str.strip().str.lower()
        st.session_state.all_questions = df.to_dict('records')
    except:
        st.error("問題データ(questions.csv)を読み込めません。")
        st.stop()

# --- サイドバー：設定 ---
st.sidebar.title("📚 Menu")
with st.sidebar.expander("⚠️ スマホで動かない場合"):
    st.write("1. URLが https で始まっているか確認。")
    st.write("2. ブラウザの設定でカメラとマイクを許可してください。")

if st.sidebar.button("最初からリセット"):
    st.session_state.clear()
    st.rerun()

kous = sorted(list(set([str(q['kou']) for q in st.session_state.all_questions])))
selected_kous = st.sidebar.multiselect("講を選択してください", kous)

# 改善点1：出題順の選択
order_type = st.sidebar.radio("出題順を選択", ["順番通り", "ランダム"])

if st.sidebar.button("学習スタート"):
    if selected_kous:
        selected_data = [q for q in st.session_state.all_questions if str(q['kou']) in selected_kous]
        if selected_data:
            # ランダムならここでシャッフル
            if order_type == "ランダム":
                random.shuffle(selected_data)
            st.session_state.current_list, st.session_state.current_idx, st.session_state.score = selected_data, 0, 0
            st.session_state.finished, st.session_state.show_feedback = False, False
            st.rerun()

# --- メイン画面 ---
if st.session_state.current_list is None:
    st.info("左側のメニューから「講」を選んで「学習スタート」を押してください。")
    st.stop()

if st.session_state.finished:
    st.markdown(f"<div style='text-align:center;'><h2>最終スコア</h2><p style='font-size:3em;color:#e67e22;font-weight:bold;'>{st.session_state.score} / {len(st.session_state.current_list)}</p></div>", unsafe_allow_html=True)
    if st.button("もう一度挑戦"):
        st.session_state.finished, st.session_state.current_idx, st.session_state.current_list = False, 0, None
        st.rerun()
    st.stop()

q = st.session_state.current_list[st.session_state.current_idx]
st.markdown(f"<p style='color:#784212; margin-bottom:5px;'>第{q['no']}問 ({st.session_state.current_idx + 1}/{len(st.session_state.current_list)})</p><h3 style='color:#784212; margin-top:0;'>{q['japanese']}</h3>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📷 写真", "⌨️ 打ち込み", "🎤 音声", "💬 報告"])

cropped_image = None
with tab1:
    st.write("👇 撮影または画像を選択してください。")
    cam_file = st.camera_input("カメラ", key=f"c_{st.session_state.current_idx}")
    img_file = st.file_uploader("画像を選択", type=['png', 'jpg', 'jpeg'], key=f"u_{st.session_state.current_idx}")
    raw = cam_file if cam_file else img_file
    if raw:
        try: cropped_image = st_cropper(Image.open(raw), realtime_update=True, box_color='#f39c12', aspect_ratio=None)
        except: st.info("画像を表示中...")

with tab2: user_text = st.text_input("回答をタイピング", key=f"t_{st.session_state.current_idx}")
with tab3: audio_file = st.audio_input("録音して解答", key=f"a_{st.session_state.current_idx}")

with tab4:
    st.subheader("松尾先生への報告")
    WEB_APP_URL = "https://script.google.com/macros/s/XXXXX/exec" 
    with st.form(key="support_form", clear_on_submit=True):
        sender = st.text_input("お名前")
        msg = st.text_area("メッセージ内容")
        if st.form_submit_button("送信"):
            if WEB_APP_URL.startswith("http"):
                requests.post(WEB_APP_URL, json={"name": sender, "message": msg})
                st.success("送信完了しました！")

st.markdown("---")

# 改善点2：採点ボタンと「次へ（スキップ）」ボタンを並列に
col1, col2 = st.columns(2)

with col1:
    if st.button("🚀 採点する"):
        if not (cropped_image or user_text or audio_file):
            st.warning("⚠️ 解答を入力してください。")
        else:
            with st.spinner("添削中..."):
                try:
                    model = genai.GenerativeModel(st.session_state.target_model)
                    inst = f"""
                    あなたは情熱的な英語講師です。正解例『{q['english']}』と比較してください。
                    
                    【ルール】
                    - 1行目は： あなたの英語：<b>[聞き取った英文]</b> （※記号**や「」は禁止）
                    - 文法的に正しく意味が通じれば別解も正解(Perfect!)とすること。
                    - 解説中の英文引用は <b>英文</b> とタグで囲み、記号 ** や「」『』は絶対に使わない。
                    - 厳格だが前向きに添削し、「不合格」という言葉は絶対に使わないこと。
                    - 正解・妥当な別解なら必ず『正解です』と含める。
                    """
                    if audio_file: res = model.generate_content([inst, {"mime_type": "audio/wav", "data": audio_file.read()}])
                    elif cropped_image: res = model.generate_content([inst, cropped_image])
                    else: res = model.generate_content(f"{inst}\n生徒：{user_text}")
                    
                    f_text = res.text.replace("**", "").replace("「", "").replace("」", "").replace("『", "").replace("』", "")
                    st.session_state.feedback_text, st.session_state.show_feedback = f_text, True
                    if "正解です" in f_text: st.session_state.score += 1; st.balloons()
                except Exception as e: st.error(f"Error: {e}")

with col2:
    if st.button("次へ進む ➔"):
        st.session_state.current_idx += 1
        if st.session_state.current_idx >= len(st.session_state.current_list):
            st.session_state.finished = True
        st.session_state.show_feedback = False
        st.rerun()

# 採点後のみヒントと解説を表示
if st.session_state.show_feedback:
    st.markdown(f"<div class='feedback-container'><div>{st.session_state.feedback_text}</div><div class='model-answer-text'>模範解答：{q['english']}</div></div>", unsafe_allow_html=True)
    tts = gTTS(q['english'], lang='en')
    audio_fp = io.BytesIO()
    tts.write_to_fp(audio_fp)
    st.audio(audio_fp, autoplay=True)
