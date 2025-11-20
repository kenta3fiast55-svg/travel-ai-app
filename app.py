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
    color: #1a1a1a; /* 文字を少し濃くして、透過背景でも読みやすく */
}

/* 背景画像設定 */
.stApp {
    background-image: url("https://images.unsplash.com/photo-1436491865332-7a61a109cc05?q=80&w=2074&auto=format&fit=crop");
    background-size: cover;
    background-attachment: fixed;
    background-position: center;
}

/* オーバーレイ（背景を少し暗くして文字を見やすく） */
.stApp::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(255, 255, 255, 0.2); /* フィルターも薄く */
    pointer-events: none;
    z-index: 0;
}

/* タイトルまわりのデザイン */
h1 {
    color: #0d47a1;
    text-shadow: 1px 1px 2px rgba(255,255,255,0.8);
    font-weight: 700;
    padding: 20px;
    background: rgba(255, 255, 255, 0.6); /* 透明度アップ */
    border-radius: 15px;
    display: inline-block;
    backdrop-filter: blur(5px); /* すりガラス効果 */
}

/* 入力フォームのカード化 */
div[data-testid="stForm"] {
    background: rgba(255, 255, 255, 0.75); /* 【修正】透明度を上げました（0.95 -> 0.75） */
    padding: 30px;
    border-radius: 20px;
    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.3);
    backdrop-filter: blur(10px); /* すりガラス効果 */
}

/* 結果表示エリアのデザイン */
.result-container {
    background: rgba(255, 255, 255, 0.75); /* 【修正】透明度を上げました（0.95 -> 0.75） */
    padding: 40px;
    border-radius: 20px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    margin-top: 30px;
    margin-bottom: 50px;
    backdrop-filter: blur(10px); /* すりガラス効果 */
    
    /* 【修正】テキストの折り返しを強制する設定 */
    word-wrap: break-word;
    overflow-wrap: break-word;
    white-space: normal; 
}

/* 結果内の文章（pタグ）などがはみ出さないようにする */
.result-container p, .result-container li, .result-container h1, .result-container h2, .result-container h3 {
    word-break: break-word;
    max-width: 100%;
}

/* ボタンのデザイン */
.stButton > button {
    background: linear-gradient(45deg, #1e88e5, #1565c0);
    color: white;
    border-radius: 50px;
    border: none;
    padding: 15px 40px;
    font-size: 1.2em;
    font-weight: bold;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    transition: transform 0.2s;
    width: 100%;
}
.stButton > button:hover {
    transform: translateY(-2px);
    background: linear-gradient(45deg, #42a5f5, #1e88e5);
}

h2 { color: #1565c0; border-bottom: 2px solid rgba(21, 101, 192, 0.3); padding-bottom: 10px; margin-top: 30px; }
h3 { color: #0277bd; margin-top: 20px; }

.map-container {
    border-radius: 15px;
    overflow: hidden;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    border: 5px solid rgba(255,255,255,0.8);
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- 関数定義 ---
def get_coordinates(location_name, serpapi_key):
    if not serpapi_key: return None, None
    url = "https://serpapi.com/search"
    params = {"engine": "google_maps", "q": location_name, "api_key": serpapi_key}
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if "place_results" in data and isinstance(data["place_results"], dict):
            gps = data["place_results"].get("gps_coordinates", {})
            return gps.get("latitude"), gps.get("longitude")
        elif "local_results" in data and isinstance(data["local_results"], list) and len(data["local_results"]) > 0:
            gps = data["local_results"][0].get("gps_coordinates", {})
            return gps.get("latitude"), gps.get("longitude")
        return None, None
    except: return None, None

def get_images(query, serpapi_key, num_images=4):
    if not serpapi_key: return []
    url = "https://serpapi.com/search"
    params = {"engine": "google_images", "q": query, "tbm": "isch", "api_key": serpapi_key}
    try:
        response = requests.get(url, params=params)
        data = response.json()
        image_urls = []
        if "images_results" in data:
            for item in data["images_results"][:num_images]:
                image_urls.append(item.get("original"))
        return image_urls
    except: return []

# --- サイドバー ---
with st.sidebar:
    st.header("✈️ Travel Concierge")
    st.write("AIがあなたの専属コンシェルジュとなって、最高の旅行プランを提案します。")
    st.info("Created by Gemini User")

# --- メインコンテンツ ---
col_main, = st.columns(1)
with col_main:
    st.markdown("<h1 style='text-align: center;'>✈️ AI海外旅行コンシェルジュ Premium</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.1em; background: rgba(255,255,255,0.6); padding
