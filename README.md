# 🍸 BookCocktail Project

書籍のタイトルを入力すると、その本に関する「相補的な一杯」「対照的な一杯」「意外な一杯」を提案してくれるインテリジェントなアプリケーションです。このプロジェクトは、Webアプリ版とDiscordボット版の両方を提供します。

## 🏛️ プロジェクト構成

このプロジェクトは、役割ごとに3つの主要なファイルに分割されています。

1.  **`api_server.py` (頭脳 🧠)**
    * BookCocktailを生成する全てのロジック（Google検索、Geminiによる文章生成）を担当するAPIサーバーです。WebアプリとDiscordボットの両方が、このサーバーを呼び出して結果を得ます。

2.  **`webapp.py` (Webアプリ受付 🌐)**
    * ブラウザでアクセスできるユーザーインターフェースを提供します。ユーザーからのリクエストを受け取り、`api_server.py`に問い合わせて結果を表示します。

3.  **`discord_bot.py` (Discordボト受付 🤖)**
    * Discord上でのスラッシュコマンドを待ち受けます。コマンドが実行されると、`api_server.py`に問い合わせて結果をDiscordに投稿します。

---

## ⚙️ セットアップガイド

### ステップ1: プロジェクトの準備

1.  **リポジトリをクローン:**
    ```bash
    git clone [https://github.com/KereruA0i/Book-Cocktail.git](https://github.com/KereruA0i/Book-Cocktail.git)
    cd Book-Cocktail
    ```

2.  **`.env`ファイルの設定:**
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

## 🚀 ローカルでの実行方法

`api_server.py`は、WebアプリとDiscordボットの両方にとって必須です。

#### 1. APIサーバーを起動 (必須)

まず、ターミナルで以下のコマンドを実行して、頭脳となるAPIサーバーを起動します。
```bash
# ターミナル 1
python api_server.py
```

#### 2. Webアプリ または Discordボットを起動

**別の**ターミナルを開き、使いたい方の受付を起動します。

* **Webアプリ版を使いたい場合:**
    ```bash
    # ターミナル 2
    python webapp.py
    ```
    その後、ブラウザで `http://127.0.0.1:5000` にアクセスしてください。

* **Discordボット版を使いたい場合:**
    ```bash
    # ターミナル 2
    python discord_bot.py
    ```

---

## ☁️ Webアプリ版のRenderデプロイガイド

このセクションでは、**Webアプリ版**をインターネットに公開する手順を説明します。これには、APIサーバーとWebアプリの2つをRenderにデプロイする必要があります。

### Part 1: APIサーバーのデプロイ

1.  **Renderで新しいWebサービスを作成**し、GitHubリポジトリに接続します。
2.  **サービス詳細設定:**
    * **Name**: `book-cocktail-api` など、APIサーバーだと分かる名前をつけます。
    * **Start Command**: `gunicorn api_server:app`
    * その他（Region, Branch, Build Command, Instance Type）は通常通り設定します。
3.  **環境変数を設定:** `GOOGLE_API_KEY`, `SEARCH_ENGINE_ID`, `GEMINI_API_KEY` の3つを設定します。
4.  **デプロイを開始**し、成功したら公開URL（例: `https://book-cocktail-api.onrender.com`）をコピーしておきます。

### Part 2: Webアプリのデプロイ

1.  **Renderで"もう一つ"新しいWebサービスを作成**し、同じGitHubリポジトリに接続します。
2.  **サービス詳細設定:**
    * **Name**: `book-cocktail-webapp` など、Webアプリだと分かる名前をつけます。
    * **Start Command**: `gunicorn webapp:app`
3.  **環境変数を設定:**
    * **`API_SERVER_URL`** という名前で新しい環境変数を追加します。
    * **Value**には、Part 1でコピーした**APIサーバーの公開URL**の末尾に`/generate-cocktail`を付け加えたものを貼り付けます。（例: `https://book-cocktail-api.onrender.com/generate-cocktail`）
4.  **デプロイを開始**します。

すべて成功すると、Webアプリの公開URLにアクセスして、世界中のどこからでもBookCocktailが利用できるようになります！
