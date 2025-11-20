import streamlit as st
from openai import OpenAI
import requests
import folium
from streamlit_folium import folium_static

# --- ページ設定 ---
st.set_page_config(page_title="AI海外旅行コンシェルジュ Premium", page_icon="✈️", layout="wide")

# --- デザイン設定（CSS） ---
# ここでデザインを定義します
css_code = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;700&display=swap');

html, body, [class*="st-"] {
    font-family: 'Noto Sans JP', sans-serif;
    color: #1a1a1a;
}
.stApp {
    background-image: url("https://images.unsplash.com/photo-1436491865332-7a61a109cc05?q=80&w=2074&auto=format&fit=crop");
    background-size: cover;
    background-attachment: fixed;
    background-position: center;
}
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
div[data-testid="stForm"] {
    background: rgba(255, 255, 255, 0.75);
    padding: 30px;
    border-radius: 20px;
    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.3);
    backdrop-filter: blur(10px);
}
.result-container {
    background: rgba(255, 255, 255, 0.75);
    padding: 40px;
    border-radius: 20px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    margin-top: 30px;
    margin-bottom: 50px;
    backdrop-filter: blur(10px);
    word-wrap: break-word;
    overflow-wrap: break-word;
    white-space: normal; 
}
/* 文章の折り返し設定 */
.result-container p, .result-container li, .result-container h1, .result-container h2, .result-container h3 {
    word-break: break-word;
    max-width: 100%;
}
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
# デザインを適用
st.markdown(css_code, unsafe_allow_html=True)

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
        elif "local_results" in data and isinstance(data["local_results"], list) and len(data["local_
