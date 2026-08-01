import asyncio
import os
import discord
from discord.ext import commands
import config

# インテントの設定
intents = discord.Intents.default()
intents.message_content = True  # メッセージコンテンツインテントが必要な場合

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

async def main():
    async with bot:
        # Cogの読み込み処理
        initial_extensions = [
            'cogs.trend',
            'cogs.music',
            # 他のCogがあればここに追加
        ]
        
        for extension in initial_extensions:
            try:
                await bot.load_extension(extension)
                print(f"Loaded extension: {extension}")
            except Exception as e:
                print(f"Failed to load extension {extension}: {e}")

        # トークンの確認ログ
        token = getattr(config, 'DISCORD_TOKEN', os.getenv('DISCORD_TOKEN'))
        if not token:
            print("❌ ERROR: DISCORD_TOKEN が設定されていません！")
            return

        print("🚀 Starting Bot...")
        await bot.start(token)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
