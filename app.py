# app.py (Definitive Version with Hallucination Guard and Prompt Refinement)
# This version prevents hallucinations for non-existent works and improves
# the naturalness of the generated commentaries.

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
        # --- [最重要改善点 1] ---
        # If no summary is found for a title, the work likely doesn't exist. Stop here.
        if not summary_source:
            return {"error": "入力された書籍や記事が見つかりませんでした。実在する作品名を入力してください。"}
        summary_text = summary_source['snippet']

    # Step 2: Have Gemini generate search queries.
    query_generation_schema = {
        "type": "object", "properties": {
            "complementary_query": {"type": "string"},
            "contrasting_query": {"type": "string"},
            "tangent_query": {"type": "string"}
        }, "required": ["complementary_query", "contrasting_query", "tangent_query"]
    }
    query_prompt = f"『{book_title}』という作品（要約：{summary_text}）について、以下の3つの目的のGoogle検索クエリ（日本語）を生成し、JSON形式で出力してください。\n1. complementary_query: 作品を補強する学術論文や深い分析記事を見つけるためのクエリ。\n2. contrasting_query: 作品に批判的な視点を提供する記事を見つけるためのクエリ。\n3. tangent_query: 作品に意外な視点を与える記事を見つけるためのクエリ。"
    
    queries = call_gemini(query_prompt, schema=query_generation_schema)
    if not queries:
        return {"error": "検索クエリの生成に失敗しました。"}

    # Step 3: Execute the AI-generated search queries.
    comp_source = google_search(queries.get("complementary_query"))
    cont_source = google_search(queries.get("contrasting_query"))
    tangent_source = google_search(queries.get("tangent_query"))

    # Step 4: Generate the final text based on the ACTUAL search results.
    final_generation_schema = {
        "type": "object", "properties": {
            "summary": {"type": "string"}, "complementary_commentary": {"type": "string"},
            "contrasting_commentary": {"type": "string"}, "tangent_commentary": {"type": "string"},
            "twist": {"type": "string"}
        }, "required": ["summary", "complementary_commentary", "contrasting_commentary", "tangent_commentary", "twist"]
    }
    # --- [最重要改善点 2] ---
    # The prompt for commentaries is now much more specific.
    final_prompt = f"""
    『{book_title}』という作品について、以下の情報源を分析し、BookCocktailを生成してJSON形式で出力してください。

    # 主要な情報
    - **作品の要約**: {summary_text}

    # 検索で見つかった情報源
    - **ベース（相補的）**: {comp_source['snippet'] if comp_source else "なし"}
    - **スパイス（対照的）**: {cont_source['snippet'] if cont_source else "なし"}
    - **隠し味（意外）**: {tangent_source['snippet'] if tangent_source else "なし"}

    # 指示
    1.  **summary**: 「作品の要約」を元に、自然で完成された3〜4文の最終的な要約文に書き直してください。
    2.  **complementary_commentary**: **見つかった「ベース」の情報源の内容のみを分析し**、それが主要な作品とどう関連するか1〜2文で解説してください。検索クエリ自体には言及しないでください。
    3.  **contrasting_commentary**: **見つかった「スパイス」の情報源の内容のみを分析し**、それが主要な作品とどう関連するか1〜2文で解説してください。検索クエリ自体には言及しないでください。
    4.  **tangent_commentary**: **見つかった「隠し味」の情報源の内容のみを分析し**、それが作品にどのような意外な視点を与えるか1〜2文で解説してください。検索クエリ自体には言及しないでください。
    5.  **twist**: 全体を締めくくる、気の利いた「最後の一ひねり」を生成してください。
    """
    
    final_result = call_gemini(final_prompt, schema=final_generation_schema)
    if not final_result:
        return {"error": "最終的なカクテルデータの生成に失敗しました。"}

    # Step 5: Final assembly.
    if comp_source:
        comp_source['commentary'] = final_result.get("complementary_commentary")
    if cont_source:
        cont_source['commentary'] = final_result.get("contrasting_commentary")
    if tangent_source:
        tangent_source['commentary'] = final_result.get("tangent_commentary")

    return {
        "book_title": book_title,
        "summary": final_result.get("summary"),
        "complementary": comp_source,
        "contrasting": cont_source,
        "tangent": tangent_source,
        "twist": final_result.get("twist")
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
