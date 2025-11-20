import streamlit as st
from openai import OpenAI
import requests
import folium
from streamlit_folium import folium_static

# --- ページ設定 ---
st.set_page_config(page_title="AI海外旅行コンシェルジュ Premium", page_icon="✈️", layout="wide")

# --- デザイン設定（CSS） ---
custom_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;700&display=swap');

/* 全体のフォント設定 */
html, body, [class*="st-"] {
    font-family: 'Noto Sans JP', sans-serif;
    color: #1a1a1a;
}

/* 背景画像設定 */
.stApp {
    background-image: url("https://images.unsplash.com/photo-1436491865332-7a61a109cc05?q=80&w=2074&auto=format&fit=crop");
    background-size: cover;
    background-attachment: fixed;
    background-position: center;
}

/* オーバーレイ（文字を見やすくするためのフィルター） */
.stApp::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(255, 255, 255, 0.2);
    pointer-events: none;
    z-index: 0;
}

/* タイトルまわりのデザイン */
h1 {
    color: #0d47a1;
    text-shadow: 1px 1px 2px rgba(255,255,255,0.8);
    font-weight: 700;
    padding: 20px;
    background: rgba(255, 255, 255, 0.6);
    border-radius: 15px;
    display: inline-block;
    backdrop-filter: blur(5px);
}

/* 入力フォームのデザイン */
div[data-testid="stForm"] {
    background: rgba(255, 255, 255, 0.75);
    padding: 30px;
    border-radius: 20px;
    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.3);
    backdrop-filter: blur(10px);
}

/* 結果表示エリアのデザイン */
.result-container {
    background: rgba(255, 255, 255, 0.75);
    padding: 40px;
    border-radius: 20px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    margin-top: 30px;
    margin-bottom: 50px;
    backdrop-filter: blur(10px);
    
    /* テキストの折り返し設定 */
    word-wrap: break-word;
    overflow-wrap: break-word;
    white-space: normal; 
}

/* 結果内の
