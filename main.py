import asyncio
import os
import discord
from discord.ext import commands
import config

# インテントの設定
intents = discord.Intents.default()
intents.message_content = True


# Botクラスを拡張して setup_hook を定義
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):
        """Botの起動時に一度だけ非同期で呼び出されるセットアップフック"""
        initial_extensions = [
            'cogs.trend',
            'cogs.music',
            'cogs.translation',
            'cogs.ai'
        ]

        # Cogの読み込み処理
        for extension in initial_extensions:
            try:
                await self.load_extension(extension)
                print(f"Loaded extension: {extension}")
            except Exception as e:
                print(f"❌ Failed to load extension {extension}: {e}")

        # スラッシュコマンド（app_commands）をDiscordサーバーと同期
        print("🔄 Syncing slash commands...")
        try:
            synced = await self.tree.sync()
            print(f"✅ Synced {len(synced)} command(s)")
        except Exception as e:
            print(f"❌ Failed to sync commands: {e}")


bot = MyBot()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

async def main():
    async with bot:
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
