# app.py (Stable Unified Version with Professional URL Reader)
# This version uses a third-party service (Jina AI Reader) to robustly
# handle URLs, avoiding blocks from sites like Amazon.

import os
import random
import json
import requests
import google.generativeai as genai
from flask import Flask, request, render_template, jsonify
from dotenv import load_dotenv
from googleapiclient.discovery import build

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

def call_gemini_for_cocktail(book_title, summary_snippet, comp_snippet, cont_snippet):
    print("🧠 Calling Gemini API for the entire cocktail...")
    if not GEMINI_API_KEY: return None

    json_schema = {
        "type": "object",
        "properties": {
            "summary": {"type": "string", "description": "書籍や記事の核心的なテーマやあらすじを3〜4文でまとめた要約。"},
            "complementary_commentary": {"type": "string", "description": "相補的な情報源（論文など）がどう関連するかの1〜2文の解説。"},
            "contrasting_commentary": {"type": "string", "description": "対照的な情報源（批判など）がどう関連するかの1〜2文の解説。"},
            "tangent_theme": {"type": "string", "description": "内容に対する意外な接線的テーマ（例：「経営者の自叙伝」に対する「サイコパスの特性」）。テーマ名のみを簡潔に返すこと。"},
            "twist": {"type": "string", "description": "内容のテーマを踏まえ、皮肉で知的な一言。"}
        },
        "required": ["summary", "complementary_commentary", "contrasting_commentary", "tangent_theme", "twist"]
    }

    prompt = f"""
    書籍または記事『{book_title}』に関する以下の情報を元に、BookCocktailを生成してください。

    # 情報源
    - **要約用**: {summary_snippet}
    - **ベース（相補的）用**: {comp_snippet}
    - **スパイス（対照的）用**: {cont_snippet}

    # 指示
    提供された情報とタイトルから、以下の項目を考察し、指定されたJSON形式で出力してください。
    """

    try:
        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            generation_config={"response_mime_type": "application/json", "response_schema": json_schema}
        )
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        print(f"❌ An error occurred during Gemini API call: {e}")
        return None

# --- [新規] Professional URL Reader Function ---
def read_url_content(url):
    """Uses Jina AI Reader to reliably get content from any URL."""
    print(f"🔗 Reading URL with professional tool: {url}")
    try:
        # Prepend the Jina AI Reader URL
        reader_url = f"https://r.jina.ai/{url}"
        response = requests.get(reader_url, timeout=60)
        response.raise_for_status()
        # The response is clean text, perfect for summarization
        return response.text
    except requests.RequestException as e:
        print(f"❌ Professional reader failed: {e}")
        return None

def generate_cocktail_data(user_input):
    book_title = user_input
    summary_text = ""
    is_url = user_input.strip().startswith('http')

    if is_url:
        # Try the professional reader first
        content = read_url_content(user_input)
        if content:
            # If successful, ask Gemini to get the title and summary from the content
            prompt = f"以下のテキストから、この記事の適切なタイトルと、内容の核心を突く3〜4文の要約を生成してください。テキスト: {content[:15000]}"
            # We don't need a strict JSON response here, just the text
            summary_response = call_gemini_for_cocktail(user_input, content, "", "")
            if summary_response:
                book_title = summary_response.get("summary").splitlines()[0] # Heuristic to get a title
                summary_text = summary_response.get("summary")
            else:
                 return {"error": "URLの内容から要約を生成できませんでした。"}
        else:
            # Fallback to Google Search if the professional reader fails
            print("↪️ Falling back to Google Search for URL.")
            url_summary_source = google_search(f'"{user_input}" 要約 OR 解説 OR レビュー')
            if not url_summary_source:
                return {"error": "入力されたURLに関する要約やレビューが見つかりませんでした。"}
            book_title = url_summary_source.get("title", "無題の記事")
            summary_text = url_summary_source.get("snippet", "")
    else:
        # For titles, use the standard method
        summary_source = google_search(f'"{book_title}" 要約 OR あらすじ')
        if summary_source:
            summary_text = summary_source['snippet']

    # --- The rest of the logic is common for both inputs ---
    comp_source = google_search(f'"{book_title}" 論文 OR 学術的考察')
    cont_source = google_search(f'"{book_title}" 批判 OR 問題点')

    gemini_result = call_gemini_for_cocktail(
        book_title,
        summary_text,
        comp_source['snippet'] if comp_source else "情報なし",
        cont_source['snippet'] if cont_source else "情報なし"
    )

    if not gemini_result:
        return {"error": "Failed to generate cocktail data from Gemini."}

    tangent_theme = gemini_result.get("tangent_theme", "")
    tangent_source = None
    if tangent_theme:
        tangent_query = f'"{book_title}" {tangent_theme}'
        tangent_source = google_search(tangent_query)
        if tangent_source:
             tangent_source['commentary'] = f"テーマ「{tangent_theme}」に関して新たな視点を提供します。"

    if comp_source:
        comp_source['commentary'] = gemini_result.get("complementary_commentary")
    if cont_source:
        cont_source['commentary'] = gemini_result.get("contrasting_commentary")

    return {
        "book_title": book_title,
        "summary": gemini_result.get("summary"),
        "complementary": comp_source,
        "contrasting": cont_source,
        "tangent": tangent_source,
        "twist": gemini_result.get("twist")
    }

# --- Web Interface and API Routes (No changes) ---
@app.route('/')
def home():
    return render_template('index.html')

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
