import streamlit as st
from openai import OpenAI
import requests
import folium
from streamlit_folium import folium_static 

# --- ページ設定とスタイル ---
st.set_page_config(page_title="AI海外旅行コンシェルジュ", page_icon="✈️", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;700&display=swap');
    html, body, [class*="st-"] {
        font-family: 'Noto Sans JP', sans-serif;
        color: #333;
    }
    .stApp {
        background-color: #f0f2f6; 
    }
    h1 {
        color: #004d40; 
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
    .result-container {
        background-color: white;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        margin-top: 30px;
    }
    .map-container {
        border-radius: 12px;
        overflow: hidden; 
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
    """SerpAPIを使って場所の緯度経度を取得する（修正版）"""
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
        
        # デバッグ用にエラー詳細を確認したい場合は以下を有効化
        # st.write(data) 

        # ケース1: place_results が辞書形式（単一結果）で返ってきた場合
        if "place_results" in data and isinstance(data["place_results"], dict):
            gps = data["place_results"].get("gps_coordinates", {})
            return gps.get("latitude"), gps.get("longitude")

        # ケース2: local_results がリスト形式（複数結果）で返ってきた場合
        elif "local_results" in data and isinstance(data["local_results"], list):
            if len(data["local_results"]) > 0:
                gps = data["local_results"][0].get("gps_coordinates", {})
                return gps.get("latitude"), gps.get("longitude")
        
        return None, None

    except Exception as e:
        st.error(f"座標取得エラー: {e}")
        return None, None

def get_images(query, serpapi_key,
