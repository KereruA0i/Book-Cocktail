# discord_bot.py
# This bot listens for commands on Discord and calls the api_server.py.

import os
import discord
from discord import app_commands
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
API_SERVER_URL = "https://book-cocktail.onrender.com/api/cocktail"

# Setup Bot client
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

def format_for_discord(data):
    """Formats the JSON data from the API server into a Discord-friendly string."""
    summary_text = f"### ■作品の要約\n{data.get('summary', '情報が見つかりませんでした。')}"
    parts = [summary_text]
    icons = {"complementary": "🍸", "contrasting": "🍅", "tangent": "🌶️"}
    titles = {"complementary": "ベース", "contrasting": "スパイス", "tangent": "隠し味"}

    for key in ["complementary", "contrasting", "tangent"]:
        source_data = data.get(key)
        text = f"### {icons[key]} {titles[key]} ({key.capitalize()})\n"
        if source_data:
            text += f"**[{source_data['title']}]({source_data['url']})**\n→ **解説:** {source_data['commentary']}"
        else:
            text += "関連情報が見つかりませんでした。"
        parts.append(text)
        
    twist_text = f"### 🎭 おつまみ (Final Twist)\n「{data.get('twist', '')}」"
    parts.append(twist_text)
    
    return "\n\n---\n\n".join(parts)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    await tree.sync()
    print("Slash commands synced.")

@tree.command(name="cocktail", description="書籍に基づいた思考のカクテルを提供します。")
@app_commands.describe(book_title="書籍のタイトル")
async def cocktail(interaction: discord.Interaction, book_title: str):
    await interaction.response.defer(thinking=True)
    try:
        response = requests.post(API_SERVER_URL, json={'book_title': book_title}, timeout=120)
        response.raise_for_status()
        cocktail_data = response.json()
        formatted_text = format_for_discord(cocktail_data)
        await interaction.followup.send(formatted_text)

    except requests.exceptions.RequestException as e:
        print(f"API connection error: {e}")
        await interaction.followup.send("カクテルサーバーへの接続に失敗しました。APIサーバーが起動しているか確認してください。")

if DISCORD_TOKEN:
    client.run(DISCORD_TOKEN)
else:
    print("FATAL ERROR: DISCORD_TOKEN is not set in the .env file.")
