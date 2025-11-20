import streamlit as st
from openai import OpenAI
import requests
import folium
from streamlit_folium import folium_static

# --- ページ設定 ---
st.set_page_config(
    page_title="AI海外旅行コンシェルジュ Premium",
    page_icon="✈️",
    layout="wide"
)

# --- デザイン設定（CSS） ---
# テキストの折り返しを「最強」の設定にしました
css_code = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;700&display=swap');

html, body, [class*="st-"] {
    font-family: 'Noto Sans JP', sans-serif;
    color: #1a1a1a;
}

/* 背景画像 */
.stApp {
    background-image: url("https://images.unsplash.com/photo-1436491865332-7a61a109cc05?q=80&w=2074&auto=format&fit=crop");
    background-size: cover;
    background-attachment: fixed;
    background-position: center;
}

/* 背景の白フィルター */
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

/* タイトル */
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

/* 入力フォーム */
div[data-testid="stForm"] {
    background: rgba(255, 255, 255, 0.75);
    padding: 30px;
    border-radius: 20px;
    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.3);
    backdrop-filter: blur(10px);
}

/* 結果表示エリア（ここを修正） */
.result-box {
    background: rgba(255, 255, 255, 0.8); /* 読みやすく少し濃く */
    padding: 40px;
    border-radius: 20px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    margin-top: 30px;
    margin-bottom: 50px;
    backdrop-filter: blur(10px);
    
    /* 【重要】枠からはみ出させない設定 */
    width: 100%;
    box-sizing: border-box; /* パディングを幅に含める */
}

/* アプリ内のすべてのテキストに対して強制折り返しを適用 */
div[data-testid="stMarkdownContainer"] p, 
div[data-testid="stMarkdownContainer"] li,
div[data-testid="stMarkdownContainer"] h1,
div[data-testid="stMarkdownContainer"] h2,
div[data-testid="stMarkdownContainer"] h3 {
    overflow-wrap: anywhere !important; /* どんな文字でも端で折り返す */
    word-break: break-word !important;
    white-space: normal !important;
}

/* ボタン */
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

h2 { 
    color: #1565c0; 
    border-bottom: 2px solid rgba(21, 101, 192, 0.3); 
    padding-bottom: 10px; 
    margin-top: 30px; 
}

.map-container {
    border-radius: 15px;
    overflow: hidden;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    border: 5px solid rgba(255,255,255,0.8);
}
</style>
"""
st.markdown(css_code, unsafe_allow_html=True)

# --- 関数定義 ---
def get_coordinates(location_name, serpapi_key):
    if not serpapi_key: return None, None
    url = "https://serpapi.com/search"
    params = {"engine": "google_maps", "q": location_name, "api_key": serpapi_key}
    try:
        response = requests.get(url, params=params)
        data = response.json()
        # Google Mapsの結果判定
        if "place_results" in data:
            if isinstance(data["place_results"], dict):
                gps = data["place_results"].get("gps_coordinates", {})
                return gps.get("latitude"), gps.get("longitude")
        # ローカル結果の判定
        if "local_results" in data:
            local = data["local_results"]
            if isinstance(local, list) and len(local) > 0:
                gps = local[0].get("gps_coordinates", {})
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
            results = data["images_results"][:num_images]
            for item in results:
                image_urls.append(item.get("original"))
        return image_urls
    except: return []

# --- サイドバー ---
with st.sidebar:
