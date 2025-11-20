import streamlit as st
from openai import OpenAI
import requests
import folium
from streamlit_folium import folium_static # foliumをStreamlitで表示するためのライブラリ

# --- ページ設定とスタイル ---
st.set_page_config(page_title="AI海外旅行コンシェルジュ", page_icon="✈️", layout="wide")

# カスタムCSSでフォントや色、ボタンのスタイルを調整
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;700&display=swap');
    html, body, [class*="st-"] {
        font-family: 'Noto Sans JP', sans-serif;
        color: #333;
    }
    .stApp {
        background-color: #f0f2f6; /* 全体の背景色 */
    }
    h1 {
        color: #004d40; /* タイトル色 */
        text-align: center;
        margin-bottom: 30px;
    }
    h2 {
        color: #00796b;
    }
    h3 {
        color: #00695c;
    }
    .stRadio > label, .stSelectbox > label, .stSlider > label {
        font-weight: bold;
        color: #263238;
    }
    .stButton > button {
        background-color: #00796b;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-size: 1.1em;
        transition: background-color 0.3s;
    }
    .stButton > button:hover {
        background-color: #004d40;
    }
    .stAlert {
        border-radius: 8px;
    }
    .result-container {
        background-color: white;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        margin-top: 30px;
    }
    .map-container {
        border-radius: 12px;
        overflow: hidden; /* 地図の角を丸める */
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    .image-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 15px;
        margin-top: 20px;
    }
    .image-grid img {
        width: 100%;
        height: 150px;
        object-fit: cover;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# --- 関数定義 ---
def get_coordinates(location_name, serpapi_key):
    """SerpAPIを使って場所の緯度経度を取得する"""
    if not serpapi_key:
        st.error("SerpAPIキーが設定されていません。")
        return None, None
    
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_maps",
        "q": location_name,
        "api_key": serpapi_key
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if "place_results" in data and data["place_results"]:
            lat = data["place_results"][0].get("latitude")
            lng = data["place_results"][0].get("longitude")
            return lat, lng
        elif "local_results" in data and data["local_results"]:
            # より一般的な場所の場合、ローカル結果から取得を試みる
            for result in data["local_results"]:
                if "gps_coordinates" in result:
                    return result["gps_coordinates"].get("latitude"), result["gps_coordinates"].get("longitude")
