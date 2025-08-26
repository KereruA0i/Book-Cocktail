# discord_bot.py
# This bot listens for commands on Discord and calls the app.py server.

import os
import discord
from discord import app_commands
import requests
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
API_SERVER_URL = os.getenv('API_SERVER_URL', "http://127.0.0.1:5000/api/cocktail")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

def format_for_discord(data):
    # Use the title returned from the API
    title_text = f"## 🍸 『{data.get('book_title', '無題の作品')}』のカクテル"
    summary_text = f"### ■作品の要約\n{data.get('summary', '情報が見つかりませんでした。')}"
    parts = [title_text, summary_text]
    
    icons = {"complementary": "🍸", "contrasting": "🍅", "tangent": "🌶️"}
    titles = {"complementary": "ベース", "contrasting": "スパイス", "tangent": "隠し味"}

    for key in ["complementary", "contrasting", "tangent"]:
        source_data = data.get(key)
        text = f"### {icons[key]} {titles[key]}\n"
        if source_data and source_data.get('url'):
            text += f"**[{source_data.get('title', 'タイトル不明')}]({source_data.get('url')})**\n→ **解説:** {source_data.get('commentary', '')}"
        else:
            text += "関連情報が見つかりませんでした。"
        parts.append(text)
        
    twist_text = f"### 🥜 おつまみ\n「{data.get('twist', '')}」"
    parts.append(twist_text)
    return "\n\n---\n\n".join(parts)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    await tree.sync()
    print("Slash commands synced.")

@tree.command(name="cocktail", description="書籍のタイトルまたはURLから思考のカクテルを提供します。")
@app_commands.describe(query="書籍のタイトルまたはURL")
async def cocktail(interaction: discord.Interaction, query: str):
    await interaction.response.defer(thinking=True)
    try:
        # The key in the JSON payload is 'user_input'
        response = requests.post(API_SERVER_URL, json={'user_input': query}, timeout=120)
        response.raise_for_status()
        cocktail_data = response.json()
        
        if cocktail_data.get("error"):
             await interaction.followup.send(f"エラー: {cocktail_data['error']}")
             return

        formatted_text = format_for_discord(cocktail_data)
        await interaction.followup.send(formatted_text)
    except requests.exceptions.RequestException as e:
        print(f"API connection error: {e}")
        await interaction.followup.send("カクテルサーバーへの接続に失敗しました。")

if DISCORD_TOKEN:
    client.run(DISCORD_TOKEN)
else:
    print("FATAL ERROR: DISCORD_TOKEN is not set in the .env file.")
