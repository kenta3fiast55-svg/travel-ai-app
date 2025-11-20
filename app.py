import streamlit as st
from openai import OpenAI
import requests
import folium
from streamlit_folium import folium_static

# --- ページ設定 ---
st.set_page_config(page_title="AI海外旅行コンシェルジュ", page_icon="✈️", layout="wide")

# --- デザイン設定（CSS） ---
# 以下の """ から """ までがデザインの記述です
custom_css = """
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
.stButton > button {
    background-color: #00796b;
    color: white;
    border-radius: 8px;
    border: none;
    padding: 10px 20px;
    font-size: 1.1em;
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
</style>
"""
# デザインを適用
st.markdown(custom_css, unsafe_allow_html=True)


# --- 関数定義 ---
def get_coordinates(location_name, serpapi_key):
    if not serpapi_key:
        return None, None
    url = "https://serpapi.com/search"
    params = {"engine": "google_maps", "q": location_name, "api_key": serpapi_key}
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if "place_results" in data and isinstance(data["place_results"], dict):
            gps = data["place_results"].get("gps_coordinates", {})
            return gps.get("latitude"), gps.get("longitude")
        elif "local_results" in data and isinstance(data["local_results"], list):
            if len(data["local_results"]) > 0:
                gps = data["local_results"][0].get("gps_coordinates", {})
                return gps.get("latitude"), gps.get("longitude")
        return None, None
    except:
        return None, None

def get_images(query, serpapi_key, num_images=4):
    if not serpapi_key:
        return []
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
    except:
        return []

# --- サイドバー ---
with st.sidebar:
    st.header("このアプリについて")
    st.write("AIがあなたの好みを分析して、おすすめの国を提案します。")
    st.write("Created by Gemini User")

# --- メインコンテンツ ---
st.title("✈️ AI海外旅行コンシェルジュ")
st.write("いくつかの質問に答えるだけで、あなたにぴったりの旅行先を提案します！")

with st.form("travel_form"):
    col1, col2 = st.columns(2)
    with col1:
        purpose = st.selectbox("Q1. 今回の旅の目的は？", ["とにかく癒やされたい", "美味しいものを食べたい", "世界遺産・歴史を見たい", "ショッピング", "冒険したい"])
        budget = st.select_slider("Q2. 予算の感覚は？", options=["節約", "そこそこ", "普通", "贅沢", "富豪"])
    with col2:
        duration = st.radio("Q3. フライト時間は？", ["近場（アジア等）", "中距離（ハワイ等）", "遠くてもOK", "どこでも"])
        companion = st.radio("Q4. 誰と行きますか？", ["一人旅", "恋人・パートナー", "友人", "家族"])
    submitted = st.form_submit_button("旅行先を診断する！ 🚀")

if submitted:
    try:
        openai_api_key = st.secrets["OPENAI_API_KEY"]
        serpapi_api_key = st.secrets["SERPAPI_API_KEY"]
    except KeyError:
        st.error("APIキー設定エラー: Secretsにキーが設定されていません。")
        st.stop()

    client = OpenAI(api_key=openai_api_key)
    
    # プロンプト作成
    prompt = f"あなたは旅行代理店です。目的:{purpose}, 予算:{budget}, 距離:{duration}, 同行者:{companion} に最適な「国名または都市名」を1つだけ提案してください。出力は国名のみ（例: イタリア）にしてください。"
    
    st.markdown("<div class='result-container'>", unsafe_allow_html=True)
    st.subheader("診断結果")
    
    ai_country_name = ""
    with st.spinner('AIが考え中...🌍'):
        try:
            response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
            ai_country_name = response.choices[0].message.content.strip().replace("おすすめの国・都市：", "")
            st.success(f"おすすめは **{ai_country_name}** です！")
            
            # 詳細情報の取得
            detail_prompt = f"旅行先「{ai_country_name}」の魅力を、1.おすすめポイント(3つ)、2.グルメ(1つ)、3.映えスポット(1つ)、4.アドバイス の構成でMarkdown形式で書いてください。"
            detail_res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": detail_prompt}])
            st.markdown(detail_res.choices[0].message.content)
            
        except Exception as e:
            st.error(f"エラー: {e}")

    # 地図と画像
    if ai_country_name:
        st.markdown("---")
        st.subheader(f"📍 {ai_country_name} の場所")
        lat, lng = get_coordinates(ai_country_name, serpapi_api_key)
        if lat:
            m = folium.Map(location=[lat, lng], zoom_start=6)
            folium.Marker([lat, lng], tooltip=ai_country_name).add_to(m)
            st.markdown("<div class='map-container'>", unsafe_allow_html=True)
            folium_static(m, width=700, height=400)
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader(f"📷 {ai_country_name} の風景")
        imgs = get_images(ai_country_name, serpapi_api_key)
        if imgs:
            cols = st.columns(len(imgs))
            for i, url in enumerate(imgs):
                cols[i].image(url, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)
