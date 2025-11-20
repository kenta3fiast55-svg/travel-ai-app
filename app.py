import streamlit as st
from openai import OpenAI
import requests
import folium
from streamlit_folium import folium_static

# --- ページ設定 ---
st.set_page_config(
    page_title="海外旅行コンシェルジュ Premium",
    page_icon="✈️",
    layout="wide"
)

# --- デザイン設定（CSS） ---
# CSSも見やすく改行して短くしました
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
.result-container p, 
.result-container li, 
.result-container h1, 
.result-container h2 {
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

# --- 関数定義（ここを短く改行しました） ---
def get_coordinates(location_name, serpapi_key):
    if not serpapi_key:
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
        
        # Google Mapsの結果判定（短く分割）
        if "place_results" in data:
            if isinstance(data["place_results"], dict):
                gps = data["place_results"].get("gps_coordinates", {})
                return gps.get("latitude"), gps.get("longitude")
        
        # ローカル結果の判定（ここがエラー原因だったので分割）
        if "local_results" in data:
            local = data["local_results"]
            if isinstance(local, list) and len(local) > 0:
                gps = local[0].get("gps_coordinates", {})
                return gps.get("latitude"), gps.get("longitude")
                
        return None, None
    except:
        return None, None

def get_images(query, serpapi_key, num_images=4):
    if not serpapi_key:
        return []
        
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_images", 
        "q": query, 
        "tbm": "isch", 
        "api_key": serpapi_key
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        image_urls = []
        
        if "images_results" in data:
            # 画像リストの取得を短く記述
            results = data["images_results"][:num_images]
            for item in results:
                image_urls.append(item.get("original"))
                
        return image_urls
    except:
        return []

# --- サイドバー ---
with st.sidebar:
    st.header("✈️ Travel Concierge")
    st.write("AIがあなたの専属コンシェルジュとなって、最高の旅行プランを提案します。")
    st.info("Created by Gemini User")

# --- メインコンテンツ ---
col_main, = st.columns(1)
with col_main:
    st.markdown("""
        <h1 style='text-align: center;'>✈️ AI海外旅行コンシェルジュ Premium</h1>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <p style='text-align: center; font-size: 1.1em; background: rgba(255,255,255,0.6); padding: 10px; border-radius: 10px;'>
        あなたの気分や予算に合わせて、世界中からベストな旅先を厳選提案します。
        </p>
    """, unsafe_allow_html=True)

    with st.form("travel_form"):
        col1, col2 = st.columns(2)
        with col1:
            purpose = st.selectbox(
                "Q1. 今回の旅のテーマは？", 
                ["心と体を癒やす究極のリラックス", "現地の美食を食べ尽くすグルメ旅", "歴史とロマンを感じる世界遺産巡り", "最新トレンドとショッピング", "大自然に飛び込む冒険・アクティビティ"]
            )
            budget = st.select_slider(
                "Q2. 予算のイメージは？", 
                options=["なるべく節約", "平均的", "少し贅沢に", "ハイエンド・ラグジュアリー"]
            )
        with col2:
            duration = st.radio(
                "Q3. 移動時間はどれくらい？", 
                ["近場でサクッと（アジア・リゾート）", "中距離（ハワイ・オーストラリア等）", "遠くてもOK（ヨーロッパ・アメリカ等）", "地球の裏側でもどこでも"]
            )
            companion = st.radio(
                "Q4. どなたと行きますか？", 
                ["気ままな一人旅", "大切なパートナーと", "気心の知れた友人と", "家族みんなで"]
            )
        
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("✨ 最高の旅先を見つける")

if submitted:
    try:
        openai_api_key = st.secrets["OPENAI_API_KEY"]
        serpapi_api_key = st.secrets["SERPAPI_API_KEY"]
    except KeyError:
        st.error("システムエラー: APIキーが設定されていません。")
        st.stop()

    client = OpenAI(api_key=openai_api_key)
    
    # プロンプト（長いので分割）
    prompt = (
        f"旅行代理店の超ベテランコンシェルジュとして振る舞ってください。"
        f"目的:{purpose}, 予算:{budget}, 距離:{duration}, 同行者:{companion} に"
        f"最も適した「国名または都市名」を1つだけ決めてください。"
        f"出力は国名のみ（例: イタリア）にしてください。"
    )
    
    st.markdown("<div class='result-container'>", unsafe_allow_html=True)
    
    ai_country_name = ""
    with st.spinner('AIコンシェルジュが世界地図を広げています... 🌍'):
        try:
            # 国名を決定
            response = client.chat.completions.create(
                model="gpt-4o-mini", 
                messages=[{"role": "user", "content": prompt}]
            )
            ai_country_name = response.choices[0].message.content.strip()
            ai_country_name = ai_country_name.replace("おすすめの国・都市：", "")
            
            st.markdown(
                f"<h1 style='color: #1565c0; text-align: center;'>"
                f"あなたへのおすすめ：{ai_country_name}</h1>", 
                unsafe_allow_html=True
            )
            
            # 詳細情報の生成（長いので改行）
            detail_prompt = f"""
            あなたは高級旅行雑誌の編集長です。提案された「{ai_country_name}」について、
            読者が今すぐチケットを予約したくなるような魅力的な記事を書いてください。
            
            【必須要件】
            1. **非常に重要**: 文章は必ず適切な位置で改行し、読みやすくしてください。
            2. 以下の構成でMarkdown形式で出力してください。

            ### 🌟 なぜ {ai_country_name} なのか？
            （この場所の魅力を3つのポイントに分けて、それぞれ200文字程度で熱く語ってください）

            ### ✈️ 日本からのアクセス
            （直行便の有無、平均フライト時間、主要エアライン、市内へのアクセス）

            ### 🍽️ 五感で味わう絶品グルメ
            （必ず食べるべき料理を2つ挙げ、味の描写を含めて紹介）

            ### 📸 一生に残るフォトスポット
            （時間帯や撮影のコツを含めて1箇所紹介）

            ### 💡 旅のコンシェルジュ・メモ
            （{companion}で行く場合に知っておくべきマナーやヒント）
            """
            
            detail_res = client.chat.completions.create(
                model="gpt-4o-mini", 
                messages=[{"role": "user", "content": detail_prompt}]
            )
            st.markdown(detail_res.choices[0].message.content)
            
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

    if ai_country_name:
        st.markdown("---")
        st.header(f"📍 {ai_country_name} の場所")
        lat, lng = get_coordinates(ai_country_name, serpapi_api_key)
        
        if lat:
            m = folium.Map(location=[lat, lng], zoom_start=5)
            folium.Marker(
                [lat, lng], 
                tooltip=ai_country_name, 
                icon=folium.Icon(color="blue", icon="plane", prefix="fa")
            ).add_to(m)
            
            st.markdown("<div class='map-container'>", unsafe_allow_html=True)
            folium_static(m, width=800, height=500)
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.header(f"📷 {ai_country_name} のギャラリー")
        imgs = get_images(ai_country_name + " 観光", serpapi_api_key)
        
        if imgs:
            cols = st.columns(2)
            for i, url in enumerate(imgs):
                with cols[i % 2]:
                    st.image(url, use_container_width=True)
                    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
