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
    </style>
    """, unsafe_allow_html=True)

# 2. AIの初期設定（安定モデル gemini-1.5-flash を優先）
if 'target_model' not in st.session_state:
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        available_models = [m.name for m in genai.list_models()]
        # 画像認識に最も安定している 1.5-flash をまず探し、なければ最新を探す
        if 'models/gemini-1.5-flash' in available_models:
            st.session_state.target_model = 'models/gemini-1.5-flash'
        else:
            flash_models = [m for m in available_models if 'flash' in m]
            st.session_state.target_model = flash_models[0] if flash_models else 'models/gemini-1.5-flash'
        st.session_state.ai_configured = True
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
st.sidebar.info(f"使用中AI: `{st.session_state.get('target_model')}`")

if st.sidebar.button("アプリを強制リセット"):
    st.session_state.clear()
    st.rerun()

st.sidebar.markdown("---")
kous = sorted(list(set([q['kou'] for q in st.session_state.all_questions])))
selected_kous = st.sidebar.multiselect("学習する講を選択", kous, default=[kous[0]] if kous else [])
order_type = st.sidebar.radio("出題順", ["順番通り", "ランダム"])

if st.sidebar.button("この設定で開始"):
    selected_data = [q for q in st.session_state.all_questions if q['kou'] in selected_kous]
    if order_type == "ランダム":
        random.shuffle(selected_data)
    st.session_state.current_list = selected_data
    st.session_state.current_idx = 0
    st.session_state.show_feedback = False
    st.session_state.feedback_text = ""
    st.rerun()

# --- メイン画面 ---
if 'current_list' not in st.session_state:
    st.info("左のサイドバーから講を選んで「開始」ボタンを押してください。")
    st.stop()

st.title("基礎S_英語表現T_重要文例Lab")

q = st.session_state.current_list[st.session_state.current_idx]
st.subheader(f"問 {q['no']}: {q['japanese']}")
st.caption(f"（{q['kou']} - {st.session_state.current_idx + 1} / {len(st.session_state.current_list)} 問目）")

# --- 解答入力エリア（写真 or テキスト） ---
st.write("### 📝 あなたの解答")
tab1, tab2 = st.tabs(["📷 写真で提出", "⌨️ キーボード入力"])

with tab1:
    cam_file = st.camera_input("ノートを撮影")
    up_file = st.file_uploader("写真をアップロード", type=['png', 'jpg', 'jpeg'])
    active_image = cam_file if cam_file else up_file

with tab2:
    user_text = st.text_input("ここに英文を入力", key=f"text_{st.session_state.current_idx}")

# --- 採点アクション ---
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("採点する"):
        if not active_image and not user_text:
            st.warning("写真かテキストで解答を入力してください。")
        else:
            with st.spinner("AIがあなたの解答を分析中..."):
                try:
                    model = genai.GenerativeModel(st.session_state.target_model)
                    
                    # 共通の指示
                    instruction = f"""
                    あなたは親切な日本人英語教師です。
                    生徒が提出した解答を、正解例『{q['english']}』と比較して採点してください。
                    
                    【ルール】
                    1. 画像が送られた場合、手書き文字を解読して添削してください。
                    2. 日本語のみで解説してください。
                    3. 文法的に正しければ、一と言一句同じでなくても正解とし、大いに褒めてください。
                    4. 改善点があれば優しく指摘してください。
                    """
                    
                    # 画像がある場合とテキストのみの場合で入力を分ける
                    if active_image:
                        img = Image.open(active_image)
                        res = model.generate_content([instruction, img])
                    else:
                        res = model.generate_content(f"{instruction}\n生徒のテキスト回答：{user_text}")
                    
                    st.session_state.feedback_text = res.text
                    st.session_state.show_feedback = True
                    
                    # 正解ならバルーン
                    if "正解" in res.text or "おめでとう" in res.text or "素晴らしい" in res.text:
                        st.balloons()
                except Exception as e:
                    st.error(f"採点エラー: {e}")

with col2:
    if st.button("正解と音声"):
        st.session_state.show_feedback = True
        st.session_state.feedback_text = "正解例を確認して、音読の練習をしましょう！"

with col3:
    if st.button("次の問題へ"):
        if st.session_state.current_idx < len(st.session_state.current_list) - 1:
            st.session_state.current_idx += 1
            st.session_state.show_feedback = False
            st.rerun()
        else:
            st.success("全ての選んだ問題が終わりました！お疲れ様でした！")

# --- フィードバック表示 ---
if st.session_state.show_feedback:
    st.info(st.session_state.feedback_text)
    st.write(f"**【正解例】** {q['english']}")
    
    tts = gTTS(q['english'], lang='en')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    st.audio(fp)
