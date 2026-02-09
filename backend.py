import os
import json
import feedparser
import requests
from bs4 import BeautifulSoup
from github import Github
from datetime import datetime

# --- 設定 ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GITHUB_TOKEN = os.environ.get("MY_GITHUB_TOKEN")
REPO_NAME = "KeinIkey/News"

def summarize_with_gemini(text, topic):
    if not GEMINI_API_KEY:
        return "API Key is missing."

    # ライブラリを通さず、直接 v1 エンドポイントを叩く
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{
                "text": f"""
                トピック「{topic}」に関連する情報を以下のテキストから日本語で要約してください。関連がなければ 'None' とだけ出力してください。\n\nText: {text[:5000]}
                関連がある場合、学術的な文脈を保ったまま日本語で要約してください。
                背景、本文の大まかな構成ごとの要約、注意点を含むようにしてまとめてください。
                """
            }]
        }]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        res_json = response.json()
        
        # 404エラーが出た場合のデバッグ情報をリターン
        if response.status_code != 200:
            return f"API Error {response.status_code}: {res_json.get('error', {}).get('message', 'Unknown error')}"
            
        return res_json['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"Request Error: {str(e)}"

def main():
    # config.json の読み込み
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {"topic": "Mathematics", "urls": []}
    
    topic = config.get('topic', 'Mathematics')
    urls = config.get('urls', [])
    
    new_reports = []
    for url in urls:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            try:
                res = requests.get(entry.link, timeout=10)
                soup = BeautifulSoup(res.text, 'html.parser')
                text = soup.get_text()
            except:
                text = entry.title
            
            summary = summarize_with_gemini(text, topic)
            
            if summary and "None" not in summary and "API Error" not in summary:
                new_reports.append({
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "title": entry.title,
                    "summary": summary,
                    "url": entry.link
                })

    # GitHubへの保存 (前回と同様)
    if new_reports:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        try:
            contents = repo.get_contents("data.json")
            old_data = json.loads(contents.decoded_content.decode('utf-8'))
            updated_data = new_reports + old_data
        except:
            updated_data = new_reports
            contents = None

        final_json = json.dumps(updated_data[:50], indent=2, ensure_ascii=False)
        if contents:
            repo.update_file(contents.path, "Daily update", final_json, contents.sha)
        else:
            repo.create_file("data.json", "Initial data", final_json)

if __name__ == "__main__":
    main()
