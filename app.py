import streamlit as st
import json
import os
from github import Github

st.set_page_config(page_title="Math Info Collector", layout="wide")

# --- 1. 定数・設定の定義 ---
GITHUB_TOKEN = st.secrets["MY_GITHUB_TOKEN"] 
REPO_NAME = "KeinIkey/News" # ご自身の環境に合わせて調整済み

# --- 2. 補助関数の定義 (写像の定義) ---

def trigger_github_action():
    """GitHub Actionsを手動で起動する"""
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        workflow = repo.get_workflow("daily.yml")
        # 手動実行(workflow_dispatch)を送信
        success = workflow.create_dispatch(ref="main") 
        return success
    except Exception as e:
        st.error(f"GitHub連携エラー: {e}")
        return False

def save_config_to_github(topic, urls):
    """設定をGitHub上のconfig.jsonに保存する"""
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    
    new_config = {
        "topic": topic,
        "urls": [u.strip() for u in urls.split('\n') if u.strip()]
    }
    content = json.dumps(new_config, indent=2, ensure_ascii=False)
    
    try:
        contents = repo.get_contents("config.json")
        repo.update_file(contents.path, "Update config via Web UI", content, contents.sha)
        st.success("GitHub上の設定を更新しました。次回の収集から反映されます。")
    except Exception as e:
        st.error(f"保存エラー: {e}")

# --- 3. UI構築 (表示処理) ---

st.title("∫ Information Integrator")

tab1, tab2 = st.tabs(["収集レポート", "設定画面"])

# --- タブ1: レポート表示 ---
with tab1:
    if os.path.exists('data.json'):
        with open('data.json', 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if not data:
                    st.info("現在、表示できるデータはありません。収集をお待ちください。")
                for item in data:
                    with st.expander(f"[{item['date']}] {item['title']}"):
                        st.markdown(item['summary'])
                        st.caption(f"Source: {item['url']}")
            except Exception as e:
                st.error(f"データの読み込みに失敗しました: {e}")
    else:
        st.info("data.jsonが見つかりません。最初の収集が完了するまでお待ちください。")

# --- タブ2: 設定・手動実行 ---
with tab2:
    st.header("🔍 収集パラメータの設定")
    
    # 現在の設定をファイルから読み込む
    if os.path.exists('config.json'):
        with open('config.json', 'r', encoding='utf-8') as f:
            current_config = json.load(f)
    else:
        current_config = {"topic": "", "urls": []}

    # 入力フォーム
    new_topic = st.text_input(
        "ターゲット・トピック", 
        value=current_config.get('topic', ''),
        help="AIに詳しく読み込ませたい内容を入力してください。"
    )
    
    new_urls = st.text_area(
        "参照サイト (URLリスト)", 
        value='\n'.join(current_config.get('urls', [])),
        height=200,
        help="RSSフィードまたはWebサイトのURLを1行ずつ入力してください。"
    )
    
    # 保存ボタン
    if st.button("設定を保存してGitHubに同期"):
        if new_topic and new_urls:
            save_config_to_github(new_topic, new_urls)
        else:
            st.warning("トピックとURLの両方を入力してください。")

    st.divider()

    # 手動実行セクション
    st.subheader("即時実行")
    st.write("定期実行を待たずに今すぐAI収集を開始します（完了まで数分かかります）。")
    
    if st.button("今すぐ収集プロセスを起動"):
        with st.spinner("GitHub Actionsを呼び出しています..."):
            if trigger_github_action():
                st.success("GitHub Actionsを正常に起動しました！")
                st.info("※データが反映されるまで数分かかります。少し待ってからブラウザを再読み込みしてください。")
            else:
                st.error("起動に失敗しました。GitHub PATの権限やREPO_NAMEを確認してください。")
