import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import streamlit as st
import google.generativeai as genai
import pandas as pd
import random
from gtts import gTTS
import io
from PIL import Image
from streamlit_cropper import st_cropper
import requests
import re

# 1. ページ設定
st.set_page_config(page_title="基礎シリーズ_英語②_T_重要文例", layout="centered")

# デザイン設定
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #ffffff 0%, #fff3e0 100%); }
    .main-title { 
        color: #e67e22; text-align: center; font-weight: 700; 
        font-size: 1.5em; padding: 10px 0; border-bottom: 3px solid #ffcc80; 
        font-family: 'serif'; margin-bottom: 15px;
    }
    div.stButton > button { 
        background-color: #f39c12 !important; color: white !important; 
        border-radius: 15px !important; height: 3.5em !important; 
        font-size: 1.1em !important; font-weight: bold !important; 
        width: 100%;
    }
    .feedback-container { background-color: #fff9f0; padding: 20px; border-radius: 15px; border-left: 8px solid #f39c12; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>基礎シリーズ_英語②_T_重要文例</h1>", unsafe_allow_html=True)

# 2. 変数の初期化
for key in ['finished', 'score', 'current_idx', 'show_feedback', 'current_list', 'feedback_text']:
    if key not in st.session_state:
        st.session_state[key] = False if 'finished' in key or 'show' in key else (0 if 'idx' in key or 'score' in key else None)

# 3. データの読み込み
if 'all_questions' not in st.session_state:
    try:
        df = pd.read_csv('questions.csv')
        df.columns = df.columns.str.strip().str.lower()
        st.session_state.all_questions = df.to_dict('records')
    except:
        st.error("questions.csvが見つかりません。")
        st.stop()

# --- サイドバー ---
st.sidebar.title("📚 Menu")
if st.sidebar.button("最初からリセット"):
    st.session_state.clear()
    st.rerun()

all_kous = sorted(list(set([str(q.get('kou', q.get('lecture', '1'))) for q in st.session_state.all_questions])))
selected_kous = st.sidebar.multiselect("講を選択してください", all_kous)
order_type = st.sidebar.radio("出題順を選択", ["順番通り", "ランダム"])

if st.sidebar.button("学習スタート"):
    if selected_kous:
        data = [q for q in st.session_state.all_questions if str(q.get('kou', q.get('lecture', '1'))) in selected_kous]
        if data:
            if order_type == "ランダム":
                random.shuffle(data)
            st.session_state.current_list, st.session_state.current_idx, st.session_state.score = data, 0, 0
            st.session_state.finished, st.session_state.show_feedback = False, False
            st.rerun()

# --- メイン画面 ---
if st.session_state.current_list is None:
    st.info("👈 左のメニューから講を選んでスタートしてください。")
    st.stop()

if st.session_state.finished:
    st.balloons()
    st.success(f"終了！ スコア: {st.session_state.score} / {len(st.session_state.current_list)}")
    if st.button("もう一度挑戦"):
        st.session_state.clear()
        st.rerun()
    st.stop()

q = st.session_state.current_list[st.session_state.current_idx]
st.write(f"### 第{q.get('no', st.session_state.current_idx + 1)}問 ({st.session_state.current_idx + 1}/{len(st.session_state.current_list)})")
st.write(f"## {q.get('japanese', '')}")

tab1, tab2, tab3, tab4 = st.tabs(["📷 写真", "⌨️ 打ち込み", "🎤 音声", "💬 報告"])

with tab2:
    user_text = st.text_input("回答を入力", key=f"t_{st.session_state.current_idx}")

# --- 採点とNextボタン ---
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.button("🚀 採点する"):
        if user_text:
            with st.spinner("AIが添削中..."):
                try:
                    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                    # 404エラー回避のための指定
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"日本文:{q.get('japanese','')}\n正解例:{q.get('english','')}\n生徒解答:{user_text}\nルール:文法的に正しければ別解も正解(Perfect)として。不合格、記号**、カギカッコは一切使わず、厳格かつ前向きに添削して。"
                    res = model.generate_content(prompt)
                    f_text = re.sub(r'[\*「」『』]', '', res.text)
                    st.session_state.feedback_text, st.session_state.show_feedback = f_text, True
                    if "正解" in f_text or "Perfect" in f_text:
                        st.session_state.score += 1
                except Exception as e:
                    st.error(f"AIエラー: {e}")
        else:
            st.warning("回答を入力してください。")

with col2:
    if st.button("次へ進む ➔"):
        st.session_state.current_idx += 1
        if st.session_state.current_idx >= len(st.session_state.current_list): st.session_state.finished = True
        st.session_state.show_feedback = False
        st.rerun()

if st.session_state.show_feedback:
    st.markdown(f"<div class='feedback-container'>{st.session_state.feedback_text}<br><br><b>模範解答：{q.get('english','')}</b></div>", unsafe_allow_html=True)
    tts = gTTS(q.get('english',''), lang='en')
    af = io.BytesIO()
    tts.write_to_fp(af)
    st.audio(af, autoplay=True)
