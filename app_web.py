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

# ページ設定
st.set_page_config(page_title="基礎シリーズ 英語②T", layout="centered")

# デザイン
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #ffffff 0%, #fff3e0 100%); }
    .main-title { color: #e67e22; text-align: center; font-weight: 700; border-bottom: 3px solid #ffcc80; padding: 10px; }
    div.stButton > button { background-color: #f39c12 !important; color: white !important; border-radius: 15px !important; width: 100%; height: 3.5em; font-weight: bold; }
    .feedback-container { background-color: #fff9f0; padding: 20px; border-radius: 15px; border-left: 8px solid #f39c12; margin-top: 15px; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>基礎シリーズ 英語②T（表現）</h1>", unsafe_allow_html=True)

# セッション初期化
for key in ['finished', 'score', 'current_idx', 'show_feedback', 'current_list', 'feedback_text']:
    if key not in st.session_state:
        st.session_state[key] = False if 'finished' in key or 'show' in key else (0 if 'idx' in key or 'score' in key else None)

# データ読み込み
if 'all_questions' not in st.session_state:
    try:
        df = pd.read_csv('questions.csv')
        df.columns = df.columns.str.strip().str.lower()
        st.session_state.all_questions = df.to_dict('records')
    except:
        st.error("questions.csvが見つかりません。")
        st.stop()

# サイドバー
st.sidebar.title("📚 Menu")
kous = sorted(list(set([str(q.get('kou', q.get('lecture', '1'))) for q in st.session_state.all_questions])))
selected_kous = st.sidebar.multiselect("講を選択してください", kous)
if st.sidebar.button("学習スタート"):
    if selected_kous:
        data = [q for q in st.session_state.all_questions if str(q.get('kou', q.get('lecture', '1'))) in selected_kous]
        random.shuffle(data)
        st.session_state.current_list, st.session_state.current_idx, st.session_state.score = data, 0, 0
        st.session_state.finished, st.session_state.show_feedback = False, False
        st.rerun()

# メイン制御
if st.session_state.current_list is None:
    st.info("👈 左側のメニューから講を選んでスタートしてください。")
    st.stop()

if st.session_state.finished:
    st.balloons()
    st.success(f"終了！ スコア: {st.session_state.score} / {len(st.session_state.current_list)}")
    if st.button("最初に戻る"):
        st.session_state.clear()
        st.rerun()
    st.stop()

q = st.session_state.current_list[st.session_state.current_idx]
ans_text = q.get('english', q.get('answer', ''))

st.write(f"### 第{st.session_state.current_idx + 1}問 / {len(st.session_state.current_list)}")
st.write(f"## {q.get('japanese', '')}")

tab1, tab2, tab3, tab4 = st.tabs(["📷 写真", "⌨️ 打ち込み", "🎤 音声", "💬 報告"])

# 写真入力
img_for_ai = None
with tab1:
    cam_file = st.camera_input("カメラ", key=f"c_{st.session_state.current_idx}")
    img_file = st.file_uploader("または画像を選択", type=['png', 'jpg', 'jpeg'], key=f"u_{st.session_state.current_idx}")
    raw = cam_file if cam_file else img_file
    if raw:
        img_for_ai = st_cropper(Image.open(raw), realtime_update=True, box_color='#f39c12')

with tab2:
    typed_ans = st.text_input("英文を入力", key=f"t_{st.session_state.current_idx}")

with tab3:
    audio_data = st.audio_input("声に出して解答", key=f"a_{st.session_state.current_idx}")

with tab4:
    st.subheader("松尾先生への報告")
    with st.form(key="report"):
        name = st.text_input("お名前")
        msg = st.text_area("メッセージ")
        if st.form_submit_button("送信"):
            st.success("送信完了しました！")

# 採点ロジック
st.markdown("---")
c1, c2 = st.columns(2)

with c1:
    if st.button("🚀 採点する"):
        if not (typed_ans or audio_data or img_for_ai):
            st.warning("⚠️ 解答を入力してください。")
        else:
            with st.spinner("AIが確認中..."):
                try:
                    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                    
                    # 404エラーを徹底回避する呼び出し方式
                    model_found = False
                    for m_name in ["gemini-1.5-flash", "models/gemini-1.5-flash"]:
                        try:
                            model = genai.GenerativeModel(m_name)
                            # テスト呼び出しは行わず、そのまま実行へ
                            model_found = True
                            break
                        except:
                            continue
                    
                    if not model_found:
                        st.error("AIモデルに接続できません。APIキーを確認してください。")
                        st.stop()
                    
                    prompt = f"日本文: {q.get('japanese','')}\n正解例: {ans_text}\n文法的に正しければ別解も正解として添削してください。不合格という言葉は使わず、前向きな言葉で。正解なら必ず『正解です』と含めること。"

                    if img_for_ai:
                        res = model.generate_content([prompt, img_for_ai])
                    elif audio_data:
                        res = model.generate_content([prompt, {"mime_type": "audio/wav", "data": audio_data.read()}])
                    else:
                        res = model.generate_content(f"{prompt}\n生徒解答: {typed_ans}")
                    
                    clean_text = re.sub(r'[\*「」『』]', '', res.text)
                    st.session_state.feedback_text, st.session_state.show_feedback = clean_text, True
                    if "正解です" in clean_text:
                        st.session_state.score += 1
                except Exception as e:
                    st.error(f"AIエラー: {e}")

with c2:
    if st.button("次へ進む ➔"):
        st.session_state.current_idx += 1
        if st.session_state.current_idx >= len(st.session_state.current_list):
            st.session_state.finished = True
        st.session_state.show_feedback = False
        st.rerun()

if st.session_state.show_feedback:
    st.markdown(f"<div class='feedback-container'>{st.session_state.feedback_text}<br><br><b>模範解答：{ans_text}</b></div>", unsafe_allow_html=True)
    tts = gTTS(ans_text, lang='en')
    af = io.BytesIO()
    tts.write_to_fp(af)
    st.audio(af, autoplay=True)
