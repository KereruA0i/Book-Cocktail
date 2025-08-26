# app.py (URL-aware Unified Version)
# This version can accept either a book title or a URL as input.

import os
import random
import json
import re
import requests
import google.generativeai as genai
from flask import Flask, request, render_template, jsonify
from dotenv import load_dotenv
from googleapiclient.discovery import build
from bs4 import BeautifulSoup

# Load .env for local development
load_dotenv()

app = Flask(__name__)

# --- API Configuration ---
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SEARCH_ENGINE_ID = os.getenv('SEARCH_ENGINE_ID')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# --- Core Logic ---

def google_search(query, num=1):
    print(f"🔎 Searching for: '{query}'")
    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        result = service.cse().list(q=query, cx=SEARCH_ENGINE_ID, num=num).execute()
        items = result.get('items', [])
        if not items: return None
        return {"title": items[0].get('title'), "url": items[0].get('link'), "snippet": items[0].get('snippet', '')}
    except Exception as e:
        print(f"An error occurred during Google Search: {e}")
        return None

def call_gemini(prompt, expect_json=False):
    print("🧠 Calling Gemini API...")
    if not GEMINI_API_KEY: return None
    try:
        config = {}
        if expect_json:
            # For JSON mode, we need a specific model version and config
            model_name = 'gemini-1.5-flash' # JSON mode is well-supported on 1.5
            config = {"response_mime_type": "application/json"}
        else:
            model_name = 'gemini-2.5-flash'

        model = genai.GenerativeModel(model_name, generation_config=config)
        response = model.generate_content(prompt)
        
        return json.loads(response.text) if expect_json else response.text
    except Exception as e:
        print(f"❌ An error occurred during Gemini API call: {e}")
        return None

def scrape_and_summarize_url(url):
    print(f"🔗 Scraping URL: {url}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')
        
        text_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'article'])
        full_text = ' '.join([elem.get_text() for elem in text_elements])
        cleaned_text = re.sub(r'\s+', ' ', full_text).strip()
        truncated_text = cleaned_text[:15000] # Limit text to avoid overly long prompts

        if not truncated_text: return None

        prompt = f"""以下のウェブページのテキストを分析し、2つの項目をJSON形式で返してください。1. "title": この内容にふさわしい簡潔なタイトル。2. "summary": このテキストの核心的なテーマを3〜4文でまとめた要約。テキスト: {truncated_text}"""
        return call_gemini(prompt, expect_json=True)
    except Exception as e:
        print(f"❌ An error occurred during URL scraping: {e}")
        return None

def generate_cocktail_data(user_input):
    book_title = user_input
    summary_text = ""
    is_url = user_input.strip().startswith('http')

    if is_url:
        scraped_data = scrape_and_summarize_url(user_input)
        if not scraped_data: return {"error": "URLの読み取りまたは要約に失敗しました。"}
        book_title = scraped_data.get("title", "無題の記事")
        summary_text = scraped_data.get("summary", "")
    else:
        # For titles, we still do a quick search for a summary snippet
        summary_source = google_search(f'"{book_title}" 要約 OR あらすじ')
        if summary_source:
            summary_text = summary_source['snippet']

    comp_source = google_search(f'"{book_title}" 論文 OR 学術的考察')
    cont_source = google_search(f'"{book_title}" 批判 OR 問題点')

    gemini_result = call_gemini_for_cocktail_main(book_title, summary_text, comp_source, cont_source)
    if not gemini_result: return {"error": "Geminiからのデータ生成に失敗しました。"}

    tangent_theme = gemini_result.get("tangent_theme", "")
    tangent_source = None
    if tangent_theme:
        tangent_source = google_search(f'"{book_title}" {tangent_theme}')
        if tangent_source:
             tangent_source['commentary'] = f"テーマ「{tangent_theme}」に関して新たな視点を提供します。"

    if comp_source:
        comp_source['commentary'] = gemini_result.get("complementary_commentary")
    if cont_source:
        cont_source['commentary'] = gemini_result.get("contrasting_commentary")

    # If the input was a URL, the summary was already generated. Otherwise, use Gemini's summary.
    final_summary = summary_text if is_url else gemini_result.get("summary")

    return {
        "book_title": book_title, "summary": final_summary,
        "complementary": comp_source, "contrasting": cont_source,
        "tangent": tangent_source, "twist": gemini_result.get("twist")
    }
    
def call_gemini_for_cocktail_main(book_title, summary_snippet, comp_source, cont_source):
    comp_snippet = comp_source['snippet'] if comp_source else "情報なし"
    cont_snippet = cont_source['snippet'] if cont_source else "情報なし"
    
    prompt = f"""書籍または記事『{book_title}』に関する以下の情報を元に、BookCocktailを生成してください。# 情報源- **要約用**: {summary_snippet}- **ベース（相補的）用**: {comp_snippet}- **スパイス（対照的）用**: {cont_snippet}# 指示提供された情報とタイトルから、以下の項目を考察し、JSON形式で出力してください。1.  **summary**: 「要約用」の情報を元に、自然な3〜4文の要約を生成。2.  **complementary_commentary**: 「ベース」の情報源がどう関連するか解説。3.  **contrasting_commentary**: 「スパイス」の情報源がどう関連するか解説。4.  **tangent_theme**: 内容に対する、本質を突くような「隠し味」となる意外なテーマを考案。5.  **twist**: 全体を締めくくる、気の利いた「最後の一ひねり」を生成。"""
    return call_gemini(prompt, expect_json=True)

# --- Web Interface and API Routes ---
@app.route('/')
def home(): return render_template('index.html')

@app.route('/generate-for-web', methods=['POST'])
def generate_for_web():
    data = request.get_json()
    user_input = data.get('user_input')
    if not user_input: return jsonify({"error": "input is required"}), 400
    try:
        cocktail_data = generate_cocktail_data(user_input)
        return jsonify(cocktail_data)
    except Exception as e:
        print(f"Error for web: {e}")
        return jsonify({"error": "カクテルの生成中にエラーが発生しました。"}), 500

@app.route('/api/cocktail', methods=['POST'])
def api_for_bot():
    data = request.get_json()
    user_input = data.get('user_input')
    if not user_input: return jsonify({"error": "input is required"}), 400
    try:
        cocktail_data = generate_cocktail_data(user_input)
        return jsonify(cocktail_data)
    except Exception as e:
        print(f"Error for bot: {e}")
        return jsonify({"error": "Failed to generate cocktail data"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
