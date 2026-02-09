import json
import os
import datetime
import requests
import feedparser
import google.generativeai as genai
from bs4 import BeautifulSoup

# 設定: GitHub Actionsの環境変数からAPIキーを取得
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def get_content_from_url(url):
    """
    URLからテキスト情報を抽出する関数
    RSSフィードまたはHTMLに対応
    """
    # RSSとして解析を試みる
    feed = feedparser.parse(url)
    if feed.entries:
        return [(entry.title, entry.link, entry.description + " " + entry.title) for entry in feed.entries[:5]]
    
    # HTMLとして解析 (簡易実装)
    try:
        headers = {'User-Agent': 'Mozilla/5.0'} # ロボット扱いされないためのおまじない
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.content, 'html.parser')
        # 本文抽出のヒューリスティック (pタグの集合)
        text = " ".join([p.text for p in soup.find_all('p')])
        return [(soup.title.string, url, text[:5000])] # 長すぎるとエラーになるためカット
    except:
        return []

def summarize_with_gemini(text, topic):
    """
    Gemini APIを用いた要約写像 f: Text x Topic -> Summary
    """
    if not GEMINI_API_KEY:
        return "API Key is missing."
        
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash') # 無料かつ高速
    
    prompt = f"""
    Target Topic: {topic}
    
    以下のテキストを読み、このトピックに関連する重要な情報を抽出してください。
    トピックと無関係であれば "None" とだけ出力してください。
    関連がある場合、学術的な文脈を保ったまま日本語で要約してください。
    背景、本文の大まかな構成ごとの要約、注意点を含むようにしてまとめてください。
    
    Text:
    {text}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"

def run_collection():
    """
    バッチ処理のメイン関数
    """
    # 設定の読み込み
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    topic = config.get('topic', '')
    urls = config.get('urls', [])
    
    new_data = []
    
    # 各URLに対して処理を実行
    for url in urls:
        contents = get_content_from_url(url)
        for title, link, text in contents:
            summary = summarize_with_gemini(text, topic)
            
            # "None" でなければ結果集合に追加
            if summary and "None" not in summary:
                new_data.append({
                    "title": title,
                    "url": link,
                    "summary": summary,
                    "date": datetime.datetime.now().strftime('%Y-%m-%d'),
                    "source": url
                })
    
    # データの保存 (既存データとマージ)
    data_file = 'data.json'
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except:
                existing_data = []
    else:
        existing_data = []
        
    # 最新が上に来るように結合
    final_data = new_data + existing_data
    
    # 保存
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run_collection()
