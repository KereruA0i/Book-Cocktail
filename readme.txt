【最終版】BookCocktail Discordボット セットアップガイド
このガイドは、APIサーバーと連携する高機能なDiscordボットをセットアップするためのものです。

ステップ1: プロジェクトの準備
新しいフォルダを作成: PCにプロジェクト用の新しい空のフォルダを作成します。（例: bookcocktail-bot-final）

ファイルを保存: 作成したフォルダに、app.py と bot.py の2つのファイルを保存します。

.envファイルを作成: 同じフォルダに .env という名前のファイルを新規作成し、4種類すべてのキーを記述して保存します。

# Google Custom Search API
GOOGLE_API_KEY=あなたのGoogle Custom Search APIキー
SEARCH_ENGINE_ID=あなたの検索エンジンID

# Gemini API
GEMINI_API_KEY=あなたのGemini APIキー

# Discord Bot
DISCORD_TOKEN=あなたのDiscordボットのトークン

ステップ2: Python環境とライブラリのインストール
仮想環境の作成と有効化

プロジェクトフォルダ内でターミナルを開きます。

仮想環境を作成 (初回のみ): python3 -m venv venv

仮想環境を有効化 (ターミナルを開くたびに実行):

Windows: .\venv\Scripts\activate

Mac/Linux: source venv/bin/activate

最新版ライブラリのインストール

仮想環境が有効化されているターミナルで、以下のコマンドを実行します。

pip install --upgrade pip
pip install flask discord.py requests python-dotenv "google-api-python-client>2.0.0" google-generativeai

ステップ3: VS Codeの設定 (推奨)
エディタ上で インポートを解決できません というエラーが出る場合は、以下の設定を行ってください。

VS Codeでフォルダを開く: 作成したプロジェクトフォルダを開きます。

コマンドパレットを開く: Command + Shift + P (Mac) または Ctrl + Shift + P (Windows)

インタープリターを選択: Python: Select Interpreter と入力し、表示されたコマンドを選択します。

仮想環境を選択: ./venv/bin/python というパスが含まれているものを選択します。

ステップ4: アプリケーションの実行
重要: APIサーバーとDiscordボットは、それぞれ別のターミナルで同時に動かす必要があります。

ターミナル1 (APIサーバー用):

プロジェクトフォルダでターミナルを開き、仮想環境を有効化します。

以下のコマンドでAPIサーバーを起動します。

python app.py

ターミナル2 (Discordボット用):

別のターミナルをプロジェクトフォルダで開き、仮想環境を有効化します。

以下のコマンドでDiscordボットを起動します。

python bot.py

ステップ5: Discordでテスト
ボットを招待したDiscordサーバーで /cocktail コマンドを試し、Geminiによって生成された完全な解説文と、気の利いた「最後の一ひねり」をお楽しみください。