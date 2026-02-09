import os
import json
import feedparser
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai # 確実にインポートできる形に戻す
from github import Github
from datetime import datetime

# --- 1. 環境変数と設定の読み込み ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GITHUB_TOKEN = os.environ.get("MY_GITHUB_TOKEN")
REPO_NAME = "KeinIkey/News"

def summarize_with_gemini(text, topic):
    if not GEMINI_API_KEY:
        return "API Key is missing."
    
    # 404エラー(v1beta)を回避するための重要な設定
    genai.configure(api_key=GEMINI_API_KEY, transport='rest')
    
    # モデルのインスタンス化
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    
    prompt = f"""
    
    トピック「{topic}」に関連する情報を以下のテキストから日本語で要約してください。関連がなければ 'None' とだけ出力してください。
    関連がある場合、学術的な文脈を保ったまま日本語で要約してください。
    背景、本文の大まかな構成ごとの要約、注意点を含むようにしてまとめてください。
    
    Text: {text[:5000]}
    """
    
    try:
        # 安全な生成呼び出し
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Execution Error: {str(e)}"

def main():
    # config.json の読み込み（存在しない場合は初期値を生成）
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
            title = entry.title
            link = entry.link
            
            try:
                res = requests.get(link, timeout=10)
                soup = BeautifulSoup(res.text, 'html.parser')
                text = soup.get_text()
            except:
                text = title
            
            summary = summarize_with_gemini(text, topic)
            
            if summary and "None" not in summary and "Execution Error" not in summary:
                new_reports.append({
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "title": title,
                    "summary": summary,
                    "url": link
                })

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
