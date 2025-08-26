# api_server.py
# This is the central brain of the BookCocktail project.
# It handles all logic for searching sources and generating text with Gemini.

import os
import random
import google.generativeai as genai
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv()
app = Flask(__name__)

# --- API Configuration ---
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SEARCH_ENGINE_ID = os.getenv('SEARCH_ENGINE_ID')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# --- Core Functions ---

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

def call_gemini(prompt):
    print("🧠 Calling Gemini API...")
    if not GEMINI_API_KEY: return "[Gemini API Key not configured]"
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"❌ An error occurred during Gemini API call: {e}")
        return f"[Gemini API Error: {e}]"

def generate_cocktail_data(book_title):
    summary_query = f'"{book_title}" 要約 OR あらすじ OR 解説'
    summary_source = google_search(summary_query)
    summary_text = "[要約のための情報が見つかりませんでした。]"
    if summary_source:
        summary_prompt = f"書籍『{book_title}』に関する以下の情報を元に、この本の核心的なテーマを3〜4文で要約してください。\n\n情報:\n{summary_source['snippet']}"
        summary_text = call_gemini(summary_prompt)

    source_types = {
        "complementary": f'"{book_title}" 論文 OR 学術的考察',
        "contrasting": f'"{book_title}" 批判 OR 問題点',
        "tangent": f'"{book_title}" {random.choice(["ポストコロニアル 批評", "フェミニズム 批評", "経済学的解釈", "精神分析学的批評"])}'
    }
    
    cocktail_sources = {}
    for key, query in source_types.items():
        source = google_search(query)
        if source:
            commentary_prompt = f"以下のタイトルと文章の断片を元に、これが書籍『{book_title}』に対してどのような関係性を持つか、1〜2文の自然な解説文を生成してください。\n\nタイトル: {source['title']}\n断片: {source['snippet']}"
            generated_commentary = call_gemini(commentary_prompt)
            source['commentary'] = generated_commentary.strip()
            cocktail_sources[key] = source
        else:
            cocktail_sources[key] = None

    twist_prompt = f"書籍『{book_title}』のテーマを踏まえて、皮肉で知的な、あるいはユーモラスな一言を生成してください。"
    twist_text = call_gemini(twist_prompt).strip().replace('"', '')

    return {
        "book_title": book_title, "summary": summary_text,
        "complementary": cocktail_sources["complementary"],
        "contrasting": cocktail_sources["contrasting"],
        "tangent": cocktail_sources["tangent"], "twist": twist_text
    }

@app.route('/generate-cocktail', methods=['POST'])
def create_cocktail_endpoint():
    data = request.get_json()
    book_title = data.get('book_title')
    if not book_title:
        return jsonify({"error": "Book title is required"}), 400
    
    cocktail_data = generate_cocktail_data(book_title)
    return jsonify(cocktail_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True) # Use a different port like 5001
