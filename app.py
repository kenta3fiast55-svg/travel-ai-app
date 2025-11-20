import streamlit as st
from openai import OpenAI
import requests
import folium
from streamlit_folium import folium_static

# --- ページ設定 ---
st.set_page_config(
    page_title="AI海外旅行コンシェルジュ Premium",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed" # サイドバーを最初から閉じておく
)

# --- デザイン設定（CSS） ---
css_code = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;700&display=swap');

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

/* サイドバーの開閉ボタン（矢印）を完全に隠す */
[data-testid="stSidebarCollapsedControl"] {
    display: none;
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

/* 結果表示エリア */
.result-box {
    background: rgba(255, 255, 255, 0.8);
    padding: 40px;
    border-radius: 20px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    margin-top: 30px;
    margin-bottom: 50px;
    backdrop-filter: blur(10px);
    width: 100%;
    box-sizing: border-box;
}

/* 全テキスト強制折り返し設定 */
.result-box *, 
.result-box p, 
.result-box li, 
.result-box h1, 
.result-box h2, 
.result-box h3 {
    overflow-wrap: anywhere !important;
    word-break: break-word !important;
    white-space: normal !important;
    max-width: 100% !important;
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

# --- サイドバーは削除しました ---

# --- メインコンテンツ ---
col_main, = st.columns(1)
with col_main:
    st.markdown("<h1 style='text-align: center;'>海外旅行コンシェルジュ</h1>", unsafe_allow_html=True)
    st.markdown("""
        <p style='text-align: center; font-size: 1.1em; background: rgba(255,255,255,0.6); padding: 10px; border-radius: 10px;'>
        あなたの気分や予算に合わせて、世界中からベストな旅先を厳選提案します。
        </p>
    """, unsafe_allow_html=True)

    with st.form("travel_form"):
        col1, col2 = st.columns(2)
        with col1:
            purpose = st.selectbox("Q1. 今回の旅のテーマは？", ["心と体を癒やす究極のリラックス", "現地の美食を食べ尽くすグルメ旅", "歴史とロマンを感じる世界遺産巡り", "最新トレンドとショッピング", "大自然に飛び込む冒険・アクティビティ"])
            budget = st.select_slider("Q2. 予算のイメージは？", options=["なるべく節約", "平均的", "少し贅沢に", "ハイエンド・ラグジュアリー"])
        with col2:
            duration = st.radio("Q3. 移動時間はどれくらい？", ["近場でサクッと（アジア・リゾート）", "中距離（ハワイ・オーストラリア等）", "遠くてもOK（ヨーロッパ・アメリカ等）", "地球の裏側でもどこでも"])
            companion = st.radio("Q4. どなたと行きますか？", ["気ままな一人旅", "大切なパートナーと", "気心の知れた友人と", "家族みんなで"])
        
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
    
    # プロンプト
    prompt = f"""
    あなたは高級旅行雑誌の編集長です。以下の条件のお客様に最適な海外旅行先を1つ選び、魅力を紹介してください。
    
    【条件】
    目的:{purpose}, 予算:{budget}, 距離:{duration}, 同行者:{companion}

    【非常に重要な出力ルール】
    1. **1行目には「国名・都市名」のみ**を書いてください（例：イタリア）。余計な記号や「おすすめは〜」などの言葉は不要です。
    2. **2行目以降**に、その国を紹介する記事をMarkdown形式で書いてください。

    【記事の構成】
    ### 🌟 なぜここなのか？
    （魅力を3つのポイントに分けて熱く語ってください）

    ### ✈️ 日本からのアクセス
    （直行便の有無、フライト時間、主要エアライン、市内へのアクセス）

    ### 🍽️ 五感で味わう絶品グルメ
    （必ず食べるべき料理を2つ挙げ、味の描写を含めて紹介）

    ### 📸 一生に残るフォトスポット
    （時間帯や撮影のコツを含めて1箇所紹介）

    ### 💡 旅のコンシェルジュ・メモ
    （{companion}で行く場合に知っておくべきマナーやヒント）
    """
    
    ai_country_name = ""
    article_content = ""

    with st.spinner('AIコンシェルジュが世界地図を広げています... 🌍'):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini", 
                messages=[{"role": "user", "content": prompt}]
            )
            
            full_text = response.choices[0].message.content.strip()
            
            if "\n" in full_text:
                ai_country_name, article_content = full_text.split("\n", 1)
            else:
                ai_country_name = full_text
                article_content = "詳細情報の取得に失敗しました。"

            ai_country_name = ai_country_name.strip().replace("おすすめの国・都市：", "")
            
            # 結果表示
            st.markdown('<div class="result-box">', unsafe_allow_html=True)
            
            st.markdown(
                f"<h1 style='color: #1565c0; text-align: center;'>"
                f"あなたへのおすすめ：{ai_country_name}</h1>", 
                unsafe_allow_html=True
            )
            st.markdown(article_content)
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

    if ai_country_name and len(ai_country_name) < 20:
        st.markdown("---")
        st.header(f"📍 {ai_country_name} の場所")
        lat, lng = get_coordinates(ai_country_name, serpapi_api_key)
        if lat:
            m = folium.Map(location=[lat, lng], zoom_start=5)
            folium.Marker([lat, lng], tooltip=ai_country_name, icon=folium.Icon(color="blue", icon="plane", prefix="fa")).add_to(m)
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

# フッター（ページ最下部）
st.markdown("---")
st.markdown("""
    <p style='text-align: center; color: #333; font-size: 0.8em;'>
    Created by Gemini User | Powered by OpenAI & SerpAPI
    </p>
""", unsafe_allow_html=True)
