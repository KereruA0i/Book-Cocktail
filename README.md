# 🍸 BookCocktail Project

書籍のタイトルを入力すると、その本に関する「ベース」「スパイス」「隠し味」を提案してくれるインテリジェントなアプリケーションです。このプロジェクトは、Webアプリ版とDiscordボット版の両方を提供します。

---

## 📂 フォルダ構成 (Project Structure)

このプロジェクトは、役割ごとにファイルとフォルダが整理されています。

* **`app.py` (心臓部 ❤️)**
    * WebアプリとDiscordボットの両方に対応する、プロジェクトの頭脳です。Google検索、Geminiによる文章生成、Webページの表示など、すべてのロジックがこのファイルに集約されています。

* **`discord_bot.py` (Discord受付 🤖)**
    * Discordからの`/cocktail`コマンドを待ち受ける専門のファイルです。コマンドを受け取ると、`app.py`に問い合わせて結果をDiscordに投稿します。

* **`templates/` フォルダ**
    * WebページのHTMLファイル（骨格）を格納します。
    * **`index.html`**: Webアプリのメインページです。

* **`static/` フォルダ**
    * Webページのデザインや動きを制御するファイルを格納します。
    * **`style.css`**: ページの見た目（色、レイアウトなど）を定義します。
    * **`script.js`**: ボタンが押されたときの通信など、ページの動的な機能を担当します。

---

## ⚙️ セットアップガイド (Installation & Setup)

### ステップ1: プロジェクトの準備

1.  **リポジトリをクローン (ダウンロード):**
    ```bash
    git clone [https://github.com/KereruA0i/Book-Cocktail.git](https://github.com/KereruA0i/Book-Cocktail.git)
    cd Book-Cocktail
    ```

2.  **`.env`ファイルの設定 (APIキー):**
    プロジェクトのルートに`.env`ファイルを作成し、4種類のAPIキーをすべて設定してください。
    ```
    # .env ファイル
    GOOGLE_API_KEY="YOUR_GOOGLE_SEARCH_API_KEY"
    SEARCH_ENGINE_ID="YOUR_SEARCH_ENGINE_ID"
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
    DISCORD_TOKEN="YOUR_DISCORD_BOT_TOKEN"
    ```

### ステップ2: Python環境の構築

1.  **仮想環境を作成・有効化:**
    ```bash
    # 作成 (初回のみ)
    python3 -m venv venv
    # 有効化 (ターミナルを開くたび)
    source venv/bin/activate
    ```

2.  **ライブラリをインストール:**
    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

---

## ⚠️ 注意事項: APIの無料利用枠について

このアプリケーションは、外部のAPIを利用しており、無料の範囲で利用できる回数に制限があります。

* **Google Custom Search API (検索用)**
    * **1日あたり100回**の検索が無料です（作成時点で）。
    * 1回のカクテル生成で最大4回検索するため、**1日におよそ25杯**のカクテルを生成できます。
    * この上限を超えると、APIがエラーを返すようになります。

* **Gemini API (文章生成用)**
    * レート制限はモデルによって**1分あたり2-15回**と非常に幅があります（作成時点で）。
    * 1回のカクテルで1回利用するように調整していますが、普段使いや他デバイスからのアクセスが重なると、エラーを出す可能性が高いです。
    

---

## 🚀 ローカルでの実行方法

#### 1. サーバーを起動

まず、ターミナルで以下のコマンドを実行して、心臓部である`app.py`を起動します。

```bash
# ターミナル 1
python app.py
```
これで、Webアプリと、Discordボットが接続するためのAPIの両方が起動します。

#### 2. Webアプリ または Discordボットを試す

* **Webアプリ版を試す場合:**
    ブラウザで `http://127.0.0.1:5000` にアクセスしてください。

* **Discordボット版を試す場合:**
    **別の**ターミナルを開き、`discord_bot.py`を起動します。
    ```bash
    # ターミナル 2
    python discord_bot.py
    ```

---

## ☁️ RenderでのWebアプリ公開ガイド

このセクションでは、**Webアプリ版**をインターネットに公開する手順を説明します。**サービスは1つだけ**で完了します。

1.  **Renderで新しいWebサービスを作成**し、GitHubリポジトリに接続します。
2.  **サービス詳細設定:**
    * **Name**: `book-cocktail` など、お好きな名前をつけます。
    * **Start Command**: `gunicorn app:app`
    * その他（Region, Branch, Build Command, Instance Type）は通常通り設定します。
3.  **環境変数を設定:** `GOOGLE_API_KEY`, `SEARCH_ENGINE_ID`, `GEMINI_API_KEY` の3つを設定します。
4.  **デプロイを開始**します。

すべて成功すると、公開URLにアクセスして、世界中のどこからでもBookCocktailが利用できるようになります！

### ✨ おまけ: Discordボットを公開Webアプリと連携させる

ローカルで動かす`discord_bot.py`に、Renderで公開したサーバーの住所を教えることで、PCを落としてもDiscordボットが機能するようにできます。

`discord_bot.py`の以下の行を書き換えてください。

```python
# 変更前
# API_SERVER_URL = "[http://127.0.0.1:5000/api/cocktail](http://127.0.0.1:5000/api/cocktail)"

# 変更後
API_SERVER_URL = "[https://your-app-name.onrender.com/api/cocktail](https://your-app-name.onrender.com/api/cocktail)"
