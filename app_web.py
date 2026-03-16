import streamlit as st
import google.generativeai as genai
import pandas as pd
import random
from gtts import gTTS
import io
from PIL import Image

# 1. ページ設定とデザイン
st.set_page_config(page_title="基礎S_英語表現T_重要文例Lab", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #D6EAF8; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; font-size: 1.1em; }
    h1, h2, h3 { color: #1B4F72; }
    .score-box { background-color: #fff; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #1B4F72; }
    </style>
    """, unsafe_allow_html=True)

# --- 【重要】変数の初期化（エラー防止） ---
if 'finished' not in st.session_state:
    st.session_state.finished = False
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0
if 'show_feedback' not in st.session_state:
    st.session_state.show_feedback = False

# 2. AIの初期設定
if 'target_model' not in st.session_state:
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        available_models = [m.name for m in genai.list_models()]
        if 'models/gemini-1.5-flash' in available_models:
            st.session_state.target_model = 'models/gemini-1.5-flash'
        else:
            st.session_state.target_model = 'models/gemini-1.5-flash-latest'
    except Exception as e:
        st.error(f"AI設定エラー: {e}")

# 3. データの読み込み
if 'all_questions' not in st.session_state:
    try:
        df = pd.read_csv('questions.csv')
        df.columns = df.columns.str.strip().str.lower()
        st.session_state.all_questions = df.to_dict('records')
    except Exception as e:
        st.error(f"CSV読み込みエラー: {e}")
        st.stop()

# --- サイドバー設定 ---
st.sidebar.title("🛠️ システム管理")
if st.sidebar.button("アプリを強制リセット"):
    st.session_state.clear()
    st.rerun()

st.sidebar.markdown("---")
kous = sorted(list(set([q['kou'] for q in st.session_state.all_questions])))
selected_kous = st.sidebar.multiselect("学習する講を選択", kous, default=[kous[0]] if kous else [])
order_type = st.sidebar.radio("出題順", ["順番通り", "ランダム"])

if st.sidebar.button("この設定で開始"):
    selected_data = [q for q in st.session_state.all_questions if q['kou'] in selected_kous]
    if not selected_data:
        st.sidebar.error("講を選択してください。")
    else:
        if order_type == "ランダム":
            random.shuffle(selected_data)
        st.session_state.current_list = selected_data
        st.session_state.current_idx = 0
        st.session_state.score = 0
        st.session_state.finished = False
        st.session_state.show_feedback = False
        st.rerun()

# --- メイン画面 ---
if 'current_list' not in st.session_state:
    st.title("基礎S_英語表現T_重要文例Lab")
    st.info("左のサイドバーから「講」を選んで「開始」ボタンを押してください。")
    st.stop()

# 終了画面
if st.session_state.finished:
    st.title("🎉 お疲れ様でした！")
    total = len(st.session_state.current_list)
    score = st.session_state.score
    st.balloons()
    st.markdown(f"""
    <div class="score-box">
        <h2>今回の最終成績</h2>
        <p style="font-size: 3em; color: #E74C3C;">{score} / {total}</p>
        <p>素晴らしい挑戦でした！また次も頑張りましょう。</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("もう一度最初から解く"):
        st.session_state.finished = False
        st.session_state.current_idx = 0
        st.session_state.score = 0
        st.rerun()
    st.stop()

# 学習画面
st.title("基礎S_英語表現T_重要文例Lab")
st.sidebar.markdown(f"### 現在のスコア: {st.session_state.score} 点")

q = st.session_state.current_list[st.session_state.current_idx]
st.subheader(f"問 {q['no']}: {q['japanese']}")
st.caption(f"（{q['kou']} - {st.session_state.current_idx + 1} / {len(st.session_state.current_list)} 問目）")

# 解答入力（写真 or テキスト）
tab1, tab2 = st.tabs(["📷 写真で提出", "⌨️ キーボード入力"])
with tab1:
    cam_file = st.camera_input("ノートを撮影", key=f"cam_{st.session_state.current_idx}")
    up_file = st.file_uploader("写真をアップロード", type=['png', 'jpg', 'jpeg'], key=f"up_{st.session_state.current_idx}")
    active_image = cam_file if cam_file else up_file
with tab2:
    user_text = st.text_input("ここに英文を入力", key=f"text_{st.session_state.current_idx}")

# 採点
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("採点する"):
        if not active_image and not user_text:
            st.warning("解答を入力してください。")
        else:
            with st.spinner("AI先生が採点中..."):
                try:
                    model = genai.GenerativeModel(st.session_state.target_model)
                    instruction = f"英語教師として、正解例『{q['english']}』と比較し、日本語で解説してください。正解なら文中に必ず『正解です』と入れてください。"
                    if active_image:
                        img = Image.open(active_image)
                        res = model.generate_content([instruction, img])
                    else:
                        res = model.generate_content(f"{instruction}\n生徒の回答：{user_text}")
                    
                    st.session_state.feedback_text = res.text
                    st.session_state.show_feedback = True
                    if "正解" in res.text:
                        st.session_state.score += 1
                        st.balloons()
                except Exception as e:
                    st.error(f"採点エラー: {e}")

with col2:
    if st.button("正解と音声"):
        st.session_state.show_feedback = True
        st.session_state.feedback_text = "正解例を確認して練習しましょう。"

with col3:
    button_label = "次へ" if st.session_state.current_idx < len(st.session_state.current_list) - 1 else "結果を見る"
    if st.button(button_label):
        if st.session_state.current_idx < len(st.session_state.current_list) - 1:
            st.session_state.current_idx += 1
            st.session_state.show_feedback = False
            st.rerun()
        else:
            st.session_state.finished = True
            st.rerun()

if st.session_state.show_feedback:
    st.info(st.session_state.feedback_text)
    st.write(f"**【正解例】** {q['english']}")
    tts = gTTS(q['english'], lang='en')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    st.audio(fp)
