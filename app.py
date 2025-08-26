# app.py (Stable Unified Version with Corrected URL Handling)
# This version fixes the critical bug that caused null/empty results
# by redesigning the data generation logic for maximum stability.

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
        if not items: 
            print(" -> No results found.")
            return None
        print(" -> Found result.")
        return {"title": items[0].get('title'), "url": items[0].get('link'), "snippet": items[0].get('snippet', '')}
    except Exception as e:
        print(f"An error occurred during Google Search: {e}")
        return None

def call_gemini(prompt, expect_json=False):
    """A versatile function to call the Gemini API."""
    print("🧠 Calling Gemini API...")
    if not GEMINI_API_KEY: return None
    try:
        config = {}
        model_name = 'gemini-2.5-flash' # Use flash for speed and generous limits
        if expect_json:
            config = {"response_mime_type": "application/json"}
        
        model = genai.GenerativeModel(model_name, generation_config=config)
        response = model.generate_content(prompt)
        
        return json.loads(response.text) if expect_json else response.text
    except Exception as e:
        print(f"❌ An error occurred during Gemini API call: {e}")
        return None

def read_url_content(url):
    """Uses Jina AI Reader to reliably get content from any URL."""
    print(f"🔗 Reading URL with professional tool: {url}")
    try:
        reader_url = f"https://r.jina.ai/{url}"
        response = requests.get(reader_url, timeout=60)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"❌ Professional reader failed: {e}")
        return None

def generate_cocktail_data(user_input):
    book_title = user_input
    summary_text = ""
    is_url = user_input.strip().startswith('http')

    # --- [最重要改善点] ---
    # Step 1: Establish a clear "book_title" and "summary_text" for the subject.
    if is_url:
        content = read_url_content(user_input)
        if not content:
            return {"error": "URLの内容を読み取れませんでした。"}
        
        summarization_prompt = f"以下のテキストから、この記事の適切なタイトルと、内容の核心を突く3〜4文の要約を生成してください。タイトルと要約だけを返してください。例:\nタイトル: 宇宙での妊娠のリスク\n要約: この記事は...\n\nテキスト: {content[:15000]}"
        initial_summary = call_gemini(summarization_prompt)
        
        if not initial_summary:
            return {"error": "URLの内容から要約を生成できませんでした。"}
        
        lines = initial_summary.splitlines()
        book_title = lines[0].replace("タイトル:", "").strip() if lines else "無題の記事"
        summary_text = "\n".join(lines[1:]).replace("要約:", "").strip()
    else:
        summary_source = google_search(f'"{book_title}" 要約 OR あらすじ')
        if summary_source:
            summary_text = summary_source['snippet']
        else:
            # If no summary is found, use the title itself as the context.
            summary_text = book_title 

    # Step 2: Gather supplementary sources. These can be None.
    comp_source = google_search(f'"{book_title}" 論文 OR 学術的考察')
    cont_source = google_search(f'"{book_title}" 批判 OR 問題点')

    # Step 3: Call Gemini for the main cocktail generation with a robust prompt.
    cocktail_schema = {
        "type": "object",
        "properties": {
            "summary": {"type": "string"}, "complementary_commentary": {"type": "string"},
            "contrasting_commentary": {"type": "string"}, "tangent_theme": {"type": "string"},
            "twist": {"type": "string"}
        }, "required": ["summary", "complementary_commentary", "contrasting_commentary", "tangent_theme", "twist"]
    }
    
    main_prompt = f"""
    書籍または記事『{book_title}』に関する以下の情報を元に、BookCocktailを生成し、JSON形式で出力してください。

    # 主要な情報
    - **要約**: {summary_text}

    # 補足情報
    - **ベース（相補的）用スニペット**: {comp_source['snippet'] if comp_source else "なし"}
    - **スパイス（対照的）用スニペット**: {cont_source['snippet'] if cont_source else "なし"}

    # 指示
    1.  **summary**: 「主要な情報」を元に、自然で完成された3〜4文の要約に書き直してください。
    2.  **complementary_commentary**: 「ベース」のスニペットが「なし」でなければ、それが主要な情報とどう関連するか1〜2文で解説してください。「なし」の場合は「関連情報は見つかりませんでした。」と記述してください。
    3.  **contrasting_commentary**: 「スパイス」のスニペットが「なし」でなければ、それが主要な情報とどう関連するか1〜2文で解説してください。「なし」の場合は「関連情報は見つかりませんでした。」と記述してください。
    4.  **tangent_theme**: 「主要な情報」から、本質を突くような「隠し味」となる意外なテーマを一つ考案してください。（例：「経営者の自叙伝」に対する「サイコパスの特性」）
    5.  **twist**: 全体を締めくくる、気の利いた「最後の一ひねり」を生成してください。
    """
    
    gemini_result = call_gemini(main_prompt, expect_json=True)

    if not gemini_result:
        return {"error": "Failed to generate cocktail data from Gemini."}

    # Step 4: Final assembly.
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
