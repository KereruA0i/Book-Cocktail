# app.py (Tangent-Enhanced API Server)
# This version specifically enhances the logic for the "Tangent" source
# to ensure it provides a genuinely surprising or reframing angle.

import os
import random
import google.generativeai as genai
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from googleapiclient.discovery import build

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# --- API Configuration ---
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SEARCH_ENGINE_ID = os.getenv('SEARCH_ENGINE_ID')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Configure the Gemini API client
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# --- Core Functions ---

def google_search(query, num=1):
    """Performs a Google search and returns the best result."""
    print(f"🔎 Searching for: '{query}'")
    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        result = service.cse().list(q=query, cx=SEARCH_ENGINE_ID, num=num).execute()
        items = result.get('items', [])
        if not items:
            print(" -> No results found.")
            return None
        print(" -> Found result.")
        return {
            "title": items[0].get('title'),
            "url": items[0].get('link'),
            "snippet": items[0].get('snippet', '')
        }
    except Exception as e:
        print(f"An error occurred during Google Search: {e}")
        return None

def call_gemini(prompt):
    """Calls the Gemini API using the latest stable model."""
    print("🧠 Calling Gemini API...")
    if not GEMINI_API_KEY:
        return "[Gemini API Key not configured]"
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        print("✅ Successfully received response from Gemini.")
        return response.text
    except Exception as e:
        print(f"❌ An error occurred during Gemini API call: {e}")
        return f"[Gemini API Error: {e}]"

def generate_cocktail_data(book_title):
    """Orchestrates the process of creating the entire cocktail data structure."""
    
    # 1. Generate Summary
    summary_query = f'"{book_title}" 要約 OR あらすじ OR 解説'
    summary_source = google_search(summary_query)
    summary_text = "[要約のための情報が見つかりませんでした。]"
    if summary_source:
        summary_prompt = f"書籍『{book_title}』に関する以下の情報を元に、この本の核心的なテーマを3〜4文で要約してください。\n\n情報:\n{summary_source['snippet']}"
        summary_text = call_gemini(summary_prompt)

    # 2. Process Complementary and Contrasting sources
    sources_to_process = {
        "complementary": f'"{book_title}" 論文 OR 学術的考察 OR 深い分析',
        "contrasting": f'"{book_title}" 批判 OR 問題点 OR 批評',
    }
    
    cocktail_sources = {}
    for key, query in sources_to_process.items():
        source = google_search(query)
        if source:
            commentary_prompt = f"以下のタイトルと文章の断片を元に、これが書籍『{book_title}』に対してどのような関係性を持つか、1〜2文の自然な解説文を生成してください。\n\nタイトル: {source['title']}\n断片: {source['snippet']}"
            generated_commentary = call_gemini(commentary_prompt)
            source['commentary'] = generated_commentary.strip()
            cocktail_sources[key] = source
        else:
            cocktail_sources[key] = None

    # --- [最重要改善点] Tangent Logic ---
    # Use a curated list of keywords designed to reframe the narrative.
    tangent_keywords = [
        "ポストコロニアル 批評", "フェミニズム 批評", "経済学的解釈", 
        "精神分析学的批評", "作者の私生活との関連", "現代社会における意義", 
        "映画化 比較", "翻訳における問題"
    ]
    tangent_query = f'"{book_title}" {random.choice(tangent_keywords)}'
    tangent_source = google_search(tangent_query)
    
    if tangent_source:
        # Use a specific prompt for the Tangent source to ensure a surprising angle.
        tangent_prompt = f"以下の情報源は、書籍『{book_title}』に対して、どのような「意外な視点」や「新しい解釈」を提供しますか？その核心を1〜2文で解説してください。\n\nタイトル: {tangent_source['title']}\n断片: {tangent_source['snippet']}"
        generated_commentary = call_gemini(tangent_prompt)
        tangent_source['commentary'] = generated_commentary.strip()
        cocktail_sources["tangent"] = tangent_source
    else:
        cocktail_sources["tangent"] = None
    # --- End of Tangent Logic ---

    # 4. Generate Final Twist
    twist_prompt = f"書籍『{book_title}』のテーマを踏まえて、皮肉で知的な、あるいはユーモラスな一言を生成してください。"
    twist_text = call_gemini(twist_prompt).strip().replace('"', '')

    return {
        "summary": summary_text,
        "complementary": cocktail_sources.get("complementary"),
        "contrasting": cocktail_sources.get("contrasting"),
        "tangent": cocktail_sources.get("tangent"),
        "twist": twist_text
    }

def format_for_discord(data):
    """Formats the cocktail data into a Discord-friendly Markdown string."""
    summary_text = f"### ■作品の要約\n{data.get('summary', '情報が見つかりませんでした。')}"
    
    parts = [summary_text]
    
    icons = {"complementary": "🍷", "contrasting": "🍋", "tangent": "🧂"}
    titles = {"complementary": "相補的な一杯", "contrasting": "対照的な一杯", "tangent": "意外な一杯"}

    for key in ["complementary", "contrasting", "tangent"]:
        source_data = data.get(key)
        text = f"### {icons[key]} {titles[key]} ({key.capitalize()})\n"
        if source_data and source_data.get('title') and source_data.get('url'):
            text += f"**[{source_data['title']}]({source_data['url']})**\n→ **解説:** {source_data.get('commentary', '')}"
        else:
            text += "関連情報が見つかりませんでした。"
        parts.append(text)
        
    twist_text = f"### 🎭 最後の一ひねり (Final Twist)\n「{data.get('twist', '')}」"
    parts.append(twist_text)
    
    return "\n\n---\n\n".join(parts)

@app.route('/cocktail', methods=['GET'])
def create_cocktail_endpoint():
    book_title = request.args.get('title')
    if not book_title:
        return jsonify({"error": "Book title is required"}), 400
    
    cocktail_data = generate_cocktail_data(book_title)
    formatted_text = format_for_discord(cocktail_data)
    
    return jsonify({"cocktail": formatted_text})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
