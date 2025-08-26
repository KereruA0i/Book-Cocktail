# webapp.py
# This Flask application provides the web user interface.
# It calls the api_server.py to get the cocktail data and renders an HTML template.

import requests
from flask import Flask, request, render_template # render_templateをインポート

app = Flask(__name__)

# The URL of our API server
API_SERVER_URL = "http://127.0.0.1:5001/generate-cocktail"

@app.route('/', methods=['GET', 'POST'])
def home():
    cocktail = None
    error = None
    book_title_value = ""
    if request.method == 'POST':
        book_title = request.form.get('book_title')
        book_title_value = book_title
        if book_title:
            try:
                response = requests.post(API_SERVER_URL, json={'book_title': book_title}, timeout=120)
                response.raise_for_status()
                cocktail = response.json()
            except requests.exceptions.RequestException as e:
                print(f"Error calling API server: {e}")
                error = "カクテルサーバーへの接続に失敗しました。APIサーバーが起動しているか確認してください。"
    
    # render_template_stringの代わりに、'index.html'ファイルを指定してレンダリング
    return render_template('index.html', cocktail=cocktail, error=error, book_title_value=book_title_value)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
