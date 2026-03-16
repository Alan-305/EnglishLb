import streamlit as st
import google.generativeai as genai
import pandas as pd
import random
from gtts import gTTS
import io
from PIL import Image

# ==========================================
# 1. ページ設定とデザイン（ここが最重要！）
# ==========================================
st.set_page_config(page_title="基礎S_英語表現T_重要文例Lab", layout="centered")

# この下の st.markdown(""" から """, unsafe_allow_html=True) までがセットです
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&family=Roboto+Slab:wght@400;700&display=swap" rel="stylesheet">
    <style>
    /* -------------------------------------- */
    /* 全体のデザインルール */
    /* -------------------------------------- */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    .main-title {
        font-family: 'Noto Sans JP', sans-serif;
        color: #1B4F72;
        text-align: center;
        font-weight: 700;
        padding-bottom: 20px;
        border-bottom: 2px solid #1B4F72;
    }
    
    /* カード風のコンテナ */
    div[data-testid="stVerticalBlock"] > div:has(div.stTabs) {
        background-color: white !important;
        padding: 30px !important;
        border-radius: 20px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
    }
    
    /* ボタンのカスタマイズ */
    div.stButton > button {
        background-color: #1B4F72 !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        height: 3.5em !important;
        font-weight: bold !important;
    }
    
    /* 英語・日本語フォント */
    .english-text {
        font-family: 'Roboto Slab', serif;
        font-size: 1.4em;
        color: #2C3E50;
    }
    .japanese-text {
        font-family: 'Noto Sans JP', sans-serif;
        font-size: 1.1em;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 変数の初期化（ここから下はプログラムの続き）
# ==========================================
for key in ['finished', 'score', 'current_idx', 'show_feedback', 'current_list']:
    if key not in st.session_state:
        st.session_state[key] = False if key in ['finished', 'show_feedback'] else (0 if key != 'current_list' else None)

# （以下、以前のコードと同じため省略しますが、Alanさんのファイルには続きを貼ってください）
