# app.py (Final Unified Version with Single API Call)
# This version consolidates all Gemini requests into a single, efficient API call
# and uses gemini-2.5-flash for the latest balanced performance.

import os
import random
import json
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

    # Define the desired JSON structure for the output
    json_schema = {
        "type": "object",
        "properties": {
            "summary": {"type": "string", "description": "書籍の核心的なテーマやあらすじを3〜4文でまとめた要約。"},
            "complementary_commentary": {"type": "string", "description": "相補的な情報源（論文など）が書籍にどう関連するかの1〜2文の解説。"},
            "contrasting_commentary": {"type": "string", "description": "対照的な情報源（批判など）が書籍にどう関連するかの1〜2文の解説。"},
            "tangent_theme": {"type": "string", "description": "書籍に対する意外な接線的テーマ（例：「経営者の自叙伝」に対する「サイコパスの特性」）。"},
            "twist": {"type": "string", "description": "書籍のテーマを踏まえた、皮肉で知的な一言。"}
        },
        "required": ["summary", "complementary_commentary", "contrasting_commentary", "tangent_theme", "twist"]
    }

    prompt = f"""
    書籍『{book_title}』に関する以下の断片的な情報を元に、BookCocktailを生成してください。

    # 情報源
    - **要約用**: {summary_snippet}
    - **ベース（相補的）用**: {comp_snippet}
    - **スパイス（対照的）用**: {cont_snippet}

    # 指示
    提供された情報と書籍のタイトルから、以下の項目を考察し、指定されたJSON形式で出力してください。
    1.  **summary**: 書籍の要約を生成。
    2.  **complementary_commentary**: 「ベース」の情報源が書籍をどう補強するか解説。
    3.  **contrasting_commentary**: 「スパイス」の情報源が書籍にどう異議を唱えるか解説。
    4.  **tangent_theme**: 書籍に対する、本質を突くような「隠し味」となる意外なテーマを考案。
    5.  **twist**: 全体を締めくくる、気の利いた「最後の一ひねり」を生成。
    """

    try:
        model = genai.GenerativeModel(
            'gemini-2.5-flash',
            generation_config={"response_mime_type": "application/json", "response_schema": json_schema}
        )
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        print(f"❌ An error occurred during Gemini API call: {e}")
        return None

def generate_cocktail_data(book_title):
    # Step 1: Gather all information from Google Search first.
    summary_source = google_search(f'"{book_title}" 要約 OR あらすじ OR 解説')
    comp_source = google_search(f'"{book_title}" 論文 OR 学術的考察')
    cont_source = google_search(f'"{book_title}" 批判 OR 問題点')

    # Step 2: Make a single, powerful call to Gemini.
    gemini_result = call_gemini_for_cocktail(
        book_title,
        summary_source['snippet'] if summary_source else "情報なし",
        comp_source['snippet'] if comp_source else "情報なし",
        cont_source['snippet'] if cont_source else "情報なし"
    )

    if not gemini_result:
        return {"error": "Failed to generate cocktail data from Gemini."}

    # Step 3: Search for the tangent source using the theme Gemini generated.
    tangent_theme = gemini_result.get("tangent_theme", "")
    tangent_source = None
    if tangent_theme:
        tangent_source = google_search(f'"{book_title}" {tangent_theme}')
        if tangent_source:
             tangent_source['commentary'] = f"テーマ「{tangent_theme}」に関して、この情報源は新たな視点を提供します。"

    # Step 4: Assemble the final cocktail.
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
    if not data or 'book_title' not in data:
        return jsonify({"error": "book_title is required"}), 400
    
    book_title = data['book_title']
    try:
        cocktail_data = generate_cocktail_data(book_title)
        return jsonify(cocktail_data)
    except Exception as e:
        print(f"Error generating cocktail data for web: {e}")
        return jsonify({"error": "カクテルの生成中にエラーが発生しました。"}), 500

@app.route('/api/cocktail', methods=['POST'])
def api_for_bot():
    data = request.get_json()
    if not data or 'book_title' not in data:
        return jsonify({"error": "book_title is required"}), 400
    
    book_title = data['book_title']
    try:
        cocktail_data = generate_cocktail_data(book_title)
        return jsonify(cocktail_data)
    except Exception as e:
        print(f"Error in API endpoint: {e}")
        return jsonify({"error": "Failed to generate cocktail data"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
