import streamlit as st
import json
import os
from github import Github

st.set_page_config(page_title="Math Info Collector", layout="wide")

# GitHub連携設定
GITHUB_TOKEN = st.secrets["MY_GITHUB_TOKEN"] 
REPO_NAME = "KeinIkey/News" # 前回の修正通り書き換えてください

def save_config_to_github(topic, urls):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    
    # 新しい設定の集合を定義
    new_config = {
        "topic": topic,
        "urls": [u.strip() for u in urls.split('\n') if u.strip()]
    }
    content = json.dumps(new_config, indent=2, ensure_ascii=False)
    
    try:
        contents = repo.get_contents("config.json")
        repo.update_file(contents.path, "Update config via UI", content, contents.sha)
        st.success("GitHub上の設定を更新しました。次の一時間の収集から反映されます。")
    except Exception as e:
        st.error(f"保存エラー: {e}")

# --- UI構築 ---
st.title("∫ Information Integrator")

tab1, tab2 = st.tabs(["収集レポート", "設定画面"])

with tab1:
    # 既存の表示ロジック（省略：前回のコードと同じ）
    if os.path.exists('data.json'):
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                with st.expander(f"[{item['date']}] {item['title']}"):
                    st.markdown(item['summary'])
                    st.caption(f"Source: {item['url']}")

with tab2:
    st.header("収集パラメータの設定")
    st.info("ここで設定したトピックに基づき、AIが各サイトをフィルタリングして要約します。")
    
    # 現在の設定を読み込み
    with open('config.json', 'r', encoding='utf-8') as f:
        current_config = json.load(f)
        
    # トピックの編集
    new_topic = st.text_input(
        "ターゲット・トピック", 
        value=current_config.get('topic', ''),
        help="例: 'Derived Category' や 'Iwasawa Theory' など。具体的であるほどAIの精度が上がります。"
    )
    
    # URLリストの編集
    st.subheader("参照サイト (URLリスト)")
    st.markdown("情報を抽出したい**RSSフィード**または**WebサイトのURL**を1行ずつ入力してください。")
    new_urls = st.text_area(
        "URLリスト", 
        value='\n'.join(current_config.get('urls', [])),
        height=200
    )
    
    if st.button("設定を保存してGitHubに同期"):
        if new_topic and new_urls:
            save_config_to_github(new_topic, new_urls)
        else:
            st.warning("トピックとURLの両方を入力してください。")
