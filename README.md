# 🍸 BookCocktail Discord Bot

書籍のタイトルを入力すると、その本に関する「相補的な一杯」「対照的な一杯」「意外な一杯」を提案してくれるインテリジェントなDiscordボットです。Google Search APIで情報を収集し、Gemini APIが動的に解説文を生成します。

---

## 🔧 必要なもの (Prerequisites)

* **Python 3.8** 以上
* **Git**
* **Visual Studio Code** (またはお好きなコードエディタ)
* 各種APIキー (下記参照)

---

## ⚙️ セットアップガイド (Installation & Setup)

### ステップ1: プロジェクトのクローンと移動

まず、このリポジトリをあなたのPCにダウンロードします。ターミナルで以下のコマンドを実行してください。

```bash
git clone [https://github.com/KereruA0i/Book-Cocktail.git](https://github.com/KereruA0i/Book-Cocktail.git)
cd Book-Cocktail
```

### ステップ2: APIキーと`.env`ファイルの設定

プロジェクトの動作には4種類のAPIキーが必要です。プロジェクトのルートフォルダ（`app.py`と同じ場所）に`.env`という名前のファイルを作成し、以下の内容を貼り付けて、あなたのキーに書き換えてください。

**`.env`**
```
# .env ファイル

# Google Custom Search API (ウェブ検索用)
GOOGLE_API_KEY="あなたのGoogle Custom Search APIキーをここに入力"
SEARCH_ENGINE_ID="あなたの検索エンジンIDをここに入力"

# Gemini API (文章生成用)
GEMINI_API_KEY="あなたのGemini APIキーをここに入力"

# Discord Bot
DISCORD_TOKEN="あなたのDiscordボットのトークンをここに入力"
```
**重要**: この`.env`ファイルは、秘密情報が含まれるため絶対にGitでコミットしないでください。(`gitignore`に含まれているので通常は大丈夫です)

### ステップ3: Python環境の構築

プロジェクト専用の仮想環境を作成し、必要なライブラリをインストールします。

1.  **仮想環境を作成 (初回のみ):**
    ```bash
    python3 -m venv venv
    ```

2.  **仮想環境を有効化 (ターミナルを開くたびに実行):**
    * **macOS / Linux:**
        ```bash
        source venv/bin/activate
        ```
    * **Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    *(ターミナルの行頭に `(venv)` と表示されれば成功です)*

3.  **必要なライブラリをインストール:**
    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    ```
    *(注: `requirements.txt` に必要なライブラリがすべて記載されています)*

### ステップ4: VS Codeの設定 (推奨)

エディタ上で `インポートを解決できません` というエラーが出る場合は、VS Codeに仮想環境の場所を教えてあげます。

1.  **コマンドパレットを開く**: `Cmd`+`Shift`+`P` (Mac) / `Ctrl`+`Shift`+`P` (Windows)
2.  **インタープリターを選択**: `Python: Select Interpreter` と入力して選択。
3.  **仮想環境を指定**: `./venv/bin/python` というパスが含まれているものを選択します。

---

## 🚀 アプリケーションの実行

**重要**: APIサーバーとDiscordボットは、それぞれ**別のターミナルで同時に**動かす必要があります。

#### ➡️ ターミナル 1: APIサーバーを起動

```bash
# 仮想環境が有効になっていることを確認
python app.py
```

#### ➡️ ターミナル 2: Discordボットを起動

```bash
# こちらも仮想環境が有効になっていることを確認
python bot.py
```

---

## 🎮 使い方 (Usage)

ボットを招待したDiscordサーバーで、以下のスラッシュコマンドを実行します。

```
/cocktail book_title:星の王子さま
```

Geminiによって生成された、あなただけのブックカクテルをお楽しみください！
