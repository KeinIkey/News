import os
import json
import feedparser
import requests
from bs4 import BeautifulSoup
from google import genai  # 最新のライブラリを使用
from github import Github
from datetime import datetime

# --- 1. 環境変数と設定の読み込み ---
# 必ず最初に行う
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GITHUB_TOKEN = os.environ.get("MY_GITHUB_TOKEN")
REPO_NAME = "KeinIkey/News"

def summarize_with_gemini(text, topic):
    if not GEMINI_API_KEY:
        return "API Key is missing."
    
    # 最新ライブラリ (google-genai) のクライアント作成
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    トピック「{topic}」に関連する情報を以下のテキストから日本語で要約してください。関連がなければ 'None' とだけ出力してください。以下のテキストを読み、このトピックに関連する重要な情報を抽出してください。
    トピックと無関係であれば "None" とだけ出力してください。関連がある場合、学術的な文脈を保ったまま日本語で要約してください。背景、本文の大まかな構成ごとの要約、注意点を含むようにしてまとめてください。
    
    Text: {text[:5000]}
    """
    
    try:
        # 最新のメソッド名 (models.generate_content)
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Execution Error: {str(e)}"

def main():
    # config.json の読み込み
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    topic = config.get('topic', 'Mathematics')
    urls = config.get('urls', [])
    
    new_reports = []
    
    for url in urls:
        # RSSフィードの解析
        feed = feedparser.parse(url)
        entries = feed.entries if feed.entries else []
        
        for entry in entries[:3]: # 各サイト最新3件
            title = entry.title
            link = entry.link
            
            # 本文の簡易取得
            try:
                res = requests.get(link, timeout=10)
                soup = BeautifulSoup(res.text, 'html.parser')
                text = soup.get_text()
            except:
                text = title
            
            summary = summarize_with_gemini(text, topic)
            
            if summary and "None" not in summary:
                new_reports.append({
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "title": title,
                    "summary": summary,
                    "url": link
                })

    if new_reports:
        # GitHubへの保存処理
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        
        try:
            # 既存データの取得
            contents = repo.get_contents("data.json")
            old_data = json.loads(contents.decoded_content.decode('utf-8'))
            updated_data = new_reports + old_data
        except:
            updated_data = new_reports
            contents = None

        final_json = json.dumps(updated_data[:50], indent=2, ensure_ascii=False) # 直近50件保持
        
        if contents:
            repo.update_file(contents.path, "Daily update", final_json, contents.sha)
        else:
            repo.create_file("data.json", "Initial data", final_json)

if __name__ == "__main__":
    main()
