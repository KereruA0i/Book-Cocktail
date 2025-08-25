# bot.py (Final Discord Bot)
# This bot listens for commands on Discord and communicates with the API server.

import os
import discord
from discord import app_commands
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
API_URL = "http://127.0.0.1:5000/cocktail" # The local API server

# Setup Bot client
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    """Called when the bot is ready and connected to Discord."""
    print(f'Logged in as {client.user}')
    await tree.sync()
    print("Slash commands synced.")

@tree.command(name="cocktail", description="書籍に基づいた思考のカクテルを提供します。")
@app_commands.describe(book_title="書籍のタイトル")
async def cocktail(interaction: discord.Interaction, book_title: str):
    """Handles the /cocktail slash command."""
    # Immediately acknowledge the command to avoid a timeout
    await interaction.response.defer(thinking=True)

    try:
        # Send a request to the API server
        params = {'title': book_title}
        response = requests.get(API_URL, params=params, timeout=120) # Increase timeout for Gemini
        response.raise_for_status()

        data = response.json()
        cocktail_text = data.get("cocktail", "エラー: サーバーから予期せぬ応答がありました。")

        # Send the result back to the Discord channel
        await interaction.followup.send(cocktail_text)

    except requests.exceptions.Timeout:
        await interaction.followup.send("サーバーからの応答がタイムアウトしました。処理に時間がかかりすぎているようです。")
    except requests.exceptions.RequestException as e:
        print(f"API connection error: {e}")
        await interaction.followup.send("ブックカクテルのサーバーに接続できませんでした。サーバーが起動しているか確認してください。")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        await interaction.followup.send("予期せぬエラーが発生しました。")

# Run the bot
if DISCORD_TOKEN:
    client.run(DISCORD_TOKEN)
else:
    print("FATAL ERROR: DISCORD_TOKEN is not set in the .env file.")
