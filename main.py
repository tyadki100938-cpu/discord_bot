import asyncio
import discord
from discord.ext import commands
import config

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 読み込むCogのモジュールパス一覧
INITIAL_EXTENSIONS = [
    "cogs.translation",
    "cogs.ai",
    "cogs.trend",
    "cogs.music",
]

@bot.event
async def on_ready():
    # スラッシュコマンドの同期
    await bot.tree.sync()
    print(f"Logged in as {bot.user.name}")

async def load_extensions():
    for extension in INITIAL_EXTENSIONS:
        try:
            await bot.load_extension(extension)
            print(f"Loaded extension: {extension}")
        except Exception as e:
            print(f"Failed to load extension {extension}: {e}")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(config.DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
