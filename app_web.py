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

# デザイン
st.markdown("<h1 style='color: #e67e22; text-align: center;'>基礎シリーズ_英語②_T_重要文例</h1>", unsafe_allow_html=True)

# 2. 変数の初期化
for key in ['finished', 'score', 'current_idx', 'show_feedback', 'current_list', 'feedback_text']:
    if key not in st.session_state:
        st.session_state[key] = False if key in ['finished', 'show_feedback'] else (0 if key not in ['current_list', 'feedback_text'] else None)

# 3. データの読み込み
if 'all_questions' not in st.session_state:
    try:
        df = pd.read_csv('questions.csv')
        df.columns = df.columns.str.strip().str.lower()
        st.session_state.all_questions = df.to_dict('records')
    except:
        st.error("questions.csvが読み込めません。")
        st.stop()

# --- サイドバー ---
st.sidebar.title("📚 Menu")
kous = sorted(list(set([str(q['kou']) for q in st.session_state.all_questions])))
selected_kous = st.sidebar.multiselect("講を選択してください", kous)
order_type = st.sidebar.radio("出題順を選択", ["順番通り", "ランダム"])

if st.sidebar.button("学習スタート"):
    if selected_kous:
        data = [q for q in st.session_state.all_questions if str(q['kou']) in selected_kous]
        if order_type == "ランダム": random.shuffle(data)
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
st.write(f"### 第{q['no']}問 ({st.session_state.current_idx + 1}/{len(st.session_state.current_list)})")
st.write(f"## {q['japanese']}")

tab1, tab2, tab3 = st.tabs(["📷 写真", "⌨️ 打ち込み", "🎤 音声"])
with tab2:
    user_text = st.text_input("回答を入力", key=f"t_{st.session_state.current_idx}")

# 採点とNext
st.markdown("---")
c1, c2 = st.columns(2)

with c1:
    if st.button("🚀 採点する"):
        if user_text:
            with st.spinner("AIが添削中..."):
                try:
                    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                    # Pro版を試すが、ダメならFlashに自動で逃げる設定
                    try:
                        model = genai.GenerativeModel('gemini-1.5-pro')
                        res = model.generate_content(f"日本文:{q['japanese']}\n正解例:{q['english']}\n生徒解答:{user_text}\n文法的に正しければ正解。不合格、記号**、カギカッコは禁止。前向きに。")
                    except:
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        res = model.generate_content(f"日本文:{q['japanese']}\n正解例:{q['english']}\n生徒解答:{user_text}\n文法的に正しければ正解。不合格、記号**、カギカッコは禁止。前向きに。")
                    
                    f_text = re.sub(r'[\*「」『』]', '', res.text)
                    st.session_state.feedback_text, st.session_state.show_feedback = f_text, True
                    if "正解" in f_text: st.session_state.score += 1
                except Exception as e:
                    st.error("AIエラーが発生しました。設定を確認してください。")
        else:
            st.warning("回答を入力してください。")

with c2:
    if st.button("次へ進む ➔"):
        st.session_state.current_idx += 1
        if st.session_state.current_idx >= len(st.session_state.current_list): st.session_state.finished = True
        st.session_state.show_feedback = False
        st.rerun()

if st.session_state.show_feedback:
    st.info(st.session_state.feedback_text)
    st.write(f"**模範解答：{q['english']}**")
    tts = gTTS(q['english'], lang='en')
    af = io.BytesIO()
    tts.write_to_fp(af)
    st.audio(af, autoplay=True)
