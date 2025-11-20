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
        return None, None
    except Exception as e:
        st.error(f"座標取得エラー: {e}")
        return None, None

def get_images(query, serpapi_key, num_images=5):
    """SerpAPIを使ってGoogle Imagesから画像を検索する"""
    if not serpapi_key:
        return []

    url = "https://serpapi.com/search"
    params = {
        "engine": "google_images",
        "q": query,
        "tbm": "isch", # 画像検索
        "api_key": serpapi_key
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        image_urls = []
        if "images_results" in data:
            for item in data["images_results"][:num_images]:
                image_urls.append(item.get("original"))
        return image_urls
    except Exception as e:
        st.error(f"画像検索エラー: {e}")
        return []

# --- サイドバー ---
with st.sidebar:
    st.header("このアプリについて")
    st.write("AIがあなたの好みを分析して、おすすめの国を提案します。")
    st.write("Created by Gemini User")
    st.markdown("---")
    st.write("🌐 Powered by OpenAI & SerpAPI")

# --- メインコンテンツ ---
st.header("AIがあなたにぴったりの旅行先を提案！")

with st.form("travel_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        purpose = st.selectbox(
            "Q1. 今回の旅の目的は？",
            ["とにかく癒やされたい（ビーチ・スパ）", "美味しいものを食べまくりたい", "歴史や世界遺産を見たい", "ショッピングを楽しみたい", "日本ではできない冒険がしたい"]
        )
        
        budget = st.select_slider(
            "Q2. 予算の感覚は？",
            options=["超節約", "そこそこ", "普通", "ちょっと贅沢", "富豪レベル"]
        )

    with col2:
        duration = st.radio(
            "Q3. フライト時間は？",
            ["近場（アジア・グアムなど）", "中距離（ハワイ・オーストラリアなど）", "遠くてもOK（ヨーロッパ・アメリカなど）", "どこでもOK"]
        )
        
        companion = st.radio(
            "Q4. 誰と行きますか？",
            ["一人旅", "恋人・パートナー", "友人グループ", "家族（子供連れ）"]
        )

    submitted = st.form_submit_button("旅行先を診断する！ 🚀")

if submitted:
    # SecretsからAPIキーを読み込む
    try:
        openai_api_key = st.secrets["OPENAI_API_KEY"]
        serpapi_api_key = st.secrets["SERPAPI_API_KEY"]
    except KeyError as e:
        st.error(f"管理者設定エラー: 必要なAPIキーが設定されていません。Secretsを確認してください: {e}")
        st.stop()

    prompt = f"""
    あなたはプロの旅行代理店です。以下の条件のお客様に最適な「海外旅行先（国名または都市名）」を1つだけ提案してください。
    提案する国・都市名以外は出力に含めないでください。
    
    【条件】
    - 目的: {purpose}
    - 予算感: {budget}
    - 距離希望: {duration}
    - 同行者: {companion}
    
    【出力フォーマット】
    提案する国・都市名のみを、厳密に以下の形式で出力してください。他の文字は一切含めないでください。
    例: 日本（東京）
    例: フランス
    """

    client = OpenAI(api_key=openai_api_key)
    
    st.markdown("<div class='result-container'>", unsafe_allow_html=True)
    st.subheader("診断結果")
    
    ai_country_name = ""
    with st.spinner('AIが最高の旅行先を考えています...🌍'):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            ai_country_name = response.choices[0].message.content.strip()
            if not ai_country_name:
                raise ValueError("AIが有効な国名を生成できませんでした。")
            
            st.success(f"あなたにおすすめの国・都市は **{ai_country_name}** です！")

            # 詳細情報取得プロンプト
            detail_prompt = f"""
            あなたはプロの旅行代理店です。提案された「{ai_country_name}」について、以下の項目で魅力的に紹介してください。
            
            【出力フォーマット】
            以下のMarkdown形式で出力してください。
            
            ### 🌟 おすすめポイント
            （なぜこの場所が良いのか、魅力的な理由を3つ箇条書きで。感情豊かに。）
            
            ### 🍽️ 絶対食べるべきグルメ
            （具体的な料理名を1つ挙げて解説）
            
            ### 📸 映えスポット
            （写真撮影におすすめの場所を1つ）
            
            ### 💡 アドバイス
            （{companion}で行く場合の注意点や楽しみ方）
            """
            detail_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": detail_prompt}]
            )
            st.markdown(detail_response.choices[0].message.content)

        except Exception as e:
            st.error(f"AI提案または詳細情報取得中にエラーが発生しました: {e}")
            ai_country_name = "" # エラー時は画像や地図を表示しない

    if ai_country_name:
        # 地図表示
        st.markdown("---")
        st.subheader(f"🌏 {ai_country_name} の場所")
        lat, lng = get_coordinates(ai_country_name, serpapi_key)
        if lat is not None and lng is not None:
            m = folium.Map(location=[lat, lng], zoom_start=8)
            folium.Marker([lat, lng], tooltip=ai_country_name).add_to(m)
            st.markdown("<div class='map-container'>", unsafe_allow_html=True)
            folium_static(m, width=700, height=450) # Streamlitでfoliumを表示
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning(f"{ai_country_name} の場所を地図に表示できませんでした。")

        # 関連画像表示
        st.markdown("---")
        st.subheader(f"🖼️ {ai_country_name} のイメージ")
        image_urls = get_images(ai_country_name, serpapi_key, num_images=5)
        if image_urls:
            st.markdown("<div class='image-grid'>", unsafe_allow_html=True)
            cols = st.columns(len(image_urls))
            for i, url in enumerate(image_urls):
                with cols[i]:
                    st.image(url, use_column_width=True, caption=f"Image {i+1}")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning(f"{ai_country_name} の関連画像を検索できませんでした。")
    
    st.markdown("</div>", unsafe_allow_html=True) # result-container 閉じタグ
