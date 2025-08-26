# app.py (Stable Unified Version with AI-driven Search Queries)
# This definitive version has Gemini generate the optimal Google Search queries
# to ensure relevant results are always found.

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

def call_gemini(prompt, schema=None):
    """A versatile function to call the Gemini API."""
    print("🧠 Calling Gemini API...")
    if not GEMINI_API_KEY: return None
    try:
        config = {}
        model_name = 'gemini-2.5-flash'
        if schema:
            config = {"response_mime_type": "application/json"}
        
        model = genai.GenerativeModel(model_name, generation_config=config)
        response = model.generate_content(prompt)
        
        return json.loads(response.text) if schema else response.text
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

    # Step 1: Establish a clear "book_title" and "summary_text".
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
        summary_text = summary_source['snippet'] if summary_source else book_title

    # --- [最重要改善点] ---
    # Step 2: Have Gemini generate everything, including the search queries themselves.
    cocktail_schema = {
        "type": "object", "properties": {
            "summary": {"type": "string"},
            "complementary_query": {"type": "string"}, "complementary_commentary": {"type": "string"},
            "contrasting_query": {"type": "string"}, "contrasting_commentary": {"type": "string"},
            "tangent_query": {"type": "string"}, "tangent_commentary": {"type": "string"},
            "twist": {"type": "string"}
        }, "required": ["summary", "complementary_query", "complementary_commentary", "contrasting_query", "contrasting_commentary", "tangent_query", "tangent_commentary", "twist"]
    }
    
    main_prompt = f"""
    『{book_title}』という作品（要約：{summary_text}）について、BookCocktailを生成してください。

    # 指示
    以下の項目を考察し、JSON形式で出力してください。
    1.  **summary**: 提供された要約を元に、自然で完成された3〜4文の最終的な要約文を生成。
    2.  **complementary_query**: この作品を補強するような学術論文や深い分析記事を見つけるための、最適なGoogle検索クエリ（日本語）を生成。
    3.  **complementary_commentary**: 上記クエリで見つかるであろう記事が、作品とどう関連するかの解説文を生成。
    4.  **contrasting_query**: この作品に批判的な視点を提供する記事を見つけるための、最適なGoogle検索クエリ（日本語）を生成。
    5.  **contrasting_commentary**: 上記クエリで見つかるであろう記事が、作品とどう関連するかの解説文を生成。
    6.  **tangent_query**: この作品に意外な視点（例：「経営者の自叙伝」に対する「サイコパスの特性」）を与える記事を見つけるための、最適なGoogle検索クエリ（日本語）を生成。
    7.  **tangent_commentary**: 上記クエリで見つかるであろう記事が、作品とどう関連するかの解説文を生成。
    8.  **twist**: 全体を締めくくる、気の利いた「最後の一ひねり」を生成。
    """
    
    gemini_result = call_gemini(main_prompt, schema=cocktail_schema)

    if not gemini_result:
        return {"error": "Failed to generate cocktail data from Gemini."}

    # Step 3: Execute the AI-generated search queries.
    comp_source = google_search(gemini_result.get("complementary_query"))
    cont_source = google_search(gemini_result.get("contrasting_query"))
    tangent_source = google_search(gemini_result.get("tangent_query"))

    # Step 4: Final assembly with AI-generated commentaries.
    if comp_source:
        comp_source['commentary'] = gemini_result.get("complementary_commentary")
    if cont_source:
        cont_source['commentary'] = gemini_result.get("contrasting_commentary")
    if tangent_source:
        tangent_source['commentary'] = gemini_result.get("tangent_commentary")

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
