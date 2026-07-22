import os
import discord
from discord.ext import commands
import deepl

# Koyebの環境変数から読み込み
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
DEEPL_API_KEY = os.environ.get("DEEPL_API_KEY")

# 特定チャンネルのみで動かしたい場合はチャンネルID（数値）を指定。全体なら None
TARGET_CHANNEL_ID = None  

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
translator = deepl.Translator(DEEPL_API_KEY)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

@bot.event
async def on_message(message):
    # ボットの発言、または空メッセージ（画像のみ等）は無視
    if message.author.bot or not message.content.strip():
        return

    # チャンネル制限がある場合、対象以外はスルー
    if TARGET_CHANNEL_ID and message.channel.id != TARGET_CHANNEL_ID:
        return

    try:
        # 言語自動判定のため仮呼び出し
        check = translator.translate_text(message.content, target_lang="JA")
        detected_lang = check.detected_source_lang

        # 韓国語 ⇄ 日本語 相互判定
        if detected_lang == "KO":
            target_lang = "JA"
        elif detected_lang == "JA":
            target_lang = "KO"
        else:
            return  # 英語や記号などは無視

        # 翻訳実行
        result = translator.translate_text(message.content, target_lang=target_lang)

        # 返信（リプライ）
        await message.reply(f"**[{detected_lang} ➔ {target_lang}]**\n{result.text}", mention_author=False)

    except Exception as e:
        print(f"Error: {e}")

    await bot.process_commands(message)

bot.run(DISCORD_TOKEN)
