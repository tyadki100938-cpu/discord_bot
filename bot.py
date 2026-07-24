import os
import deepl
import discord
from discord import app_commands
from discord.ext import commands
from google import genai

# --- 環境変数の読み込み ---
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
DEEPL_API_KEY = os.environ.get("DEEPL_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 特定チャンネルのみで動かしたい場合はチャンネルID（数値）を指定。全体なら None
TARGET_CHANNEL_ID = None

# --- インスタンスの準備 ---
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
translator = deepl.Translator(DEEPL_API_KEY)

# Gemini クライアントの初期化
ai_client = genai.Client(api_key=GEMINI_API_KEY)


@bot.event
async def on_ready():
    # スラッシュコマンド（/ask）をDiscord側に同期
    await bot.tree.sync()
    print(f"Logged in as {bot.user.name}")


# --------------------------------------------------
# 追加機能：Gemini スラッシュコマンド (/ask)
# --------------------------------------------------
@bot.tree.command(name="ask", description="Geminiに質問・メッセージを送信します")
@app_commands.describe(prompt="Geminiへの質問内容")
async def ask(interaction: discord.Interaction, prompt: str):
    # Geminiの処理に少し時間がかかるため、タイムアウト防止で応答を待機状態にする
    await interaction.response.defer()

    try:
        # Gemini APIへリクエスト送信
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        text = response.text

        # Discordの1メッセージ上限（2000文字）対策
        if len(text) > 2000:
            for i in range(0, len(text), 1900):
                await interaction.followup.send(text[i : i + 1900])
        else:
            await interaction.followup.send(text)

    except Exception as e:
        await interaction.followup.send(f"Gemini APIエラー: {e}")


# --------------------------------------------------
# 既存機能：DeepL 自動翻訳 (on_message)
# --------------------------------------------------
@bot.event
async def on_message(message):
    # ボットの発言、または空メッセージ（画像のみ等）は無視
    if message.author.bot or not message.content.strip():
        return

    # スラッシュコマンド（/で始まる発言）は自動翻訳の対象外にする
    if message.content.startswith("/"):
        await bot.process_commands(message)
        return

    # チャンネル制限がある場合、対象以外はスルー
    if TARGET_CHANNEL_ID and message.channel.id != TARGET_CHANNEL_ID:
        await bot.process_commands(message)
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
            # 英語や記号などは無視して通常のコマンド処理へ
            await bot.process_commands(message)
            return

        # 翻訳実行
        result = translator.translate_text(
            message.content, target_lang=target_lang
        )

        # 返信（リプライ）
        await message.reply(
            f"**[{detected_lang} ➔ {target_lang}]**\n{result.text}",
            mention_author=False,
        )

    except Exception as e:
        print(f"Error: {e}")

    await bot.process_commands(message)


bot.run(DISCORD_TOKEN)
