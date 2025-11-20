import streamlit as st
from openai import OpenAI

# ページの設定
st.set_page_config(page_title="AI海外旅行コンシェルジュ", page_icon="✈️")

# タイトルと説明
st.title("✈️ AI海外旅行コンシェルジュ")
st.write("いくつかの質問に答えるだけで、あなたにぴったりの海外旅行先をAIが提案します！")
st.markdown("---")

# サイドバー（設定画面は削除し、説明のみ表示）
with st.sidebar:
    st.header("このアプリについて")
    st.write("AIがあなたの好みを分析して、おすすめの国を提案します。")
    st.write("Created by Gemini User")

# 質問フォーム
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

    # 送信ボタン
    submitted = st.form_submit_button("旅行先を診断する！ 🚀")

# 診断ボタンが押されたときの処理
if submitted:
    # SecretsからAPIキーを読み込む（ユーザーによる入力は不要）
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
    except:
        st.error("管理者設定エラー: APIキーが設定されていません。")
        st.stop()

    # AIへの命令文（プロンプト）
    prompt = f"""
    あなたはプロの旅行代理店です。以下の条件のお客様に最適な「海外旅行先（都市名）」を1つだけ提案してください。
    
    【条件】
    - 目的: {purpose}
    - 予算感: {budget}
    - 距離希望: {duration}
    - 同行者: {companion}
    
    【出力フォーマット】
    以下の形式で出力してください。Markdown形式で見やすくしてください。
    
    ## ✈️ おすすめの国・都市：[国名・都市名]
    
    ### 🌟 おすすめポイント
    （なぜこの場所が良いのか、魅力的な理由を3つ箇条書きで。感情豊かに。）
    
    ### 🍽️ 絶対食べるべきグルメ
    （具体的な料理名を1つ挙げて解説）
    
    ### 📸 映えスポット
    （写真撮影におすすめの場所を1つ）
    
    ### 💡 アドバイス
    （{companion}で行く場合の注意点や楽しみ方）
    """

    # AIに問い合わせ
    client = OpenAI(api_key=api_key)
    
    with st.spinner('AIが最高の旅行先を考えています...🌍'):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            result_text = response.choices[0].message.content
            
            # 結果を表示
            st.success("診断完了！")
            st.markdown(result_text)
            
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
