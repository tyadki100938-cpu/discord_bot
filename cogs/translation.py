import discord
from discord.ext import commands
import deepl
import config

class TranslationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.translator = deepl.Translator(config.DEEPL_API_KEY) if config.DEEPL_API_KEY else None

    @commands.Cog.listener()
    async def on_message(self, message):
        # ボットの発言、または空メッセージ（画像のみ等）は無視
        if message.author.bot or not message.content.strip():
            return

        # スラッシュコマンド（/で始まる発言）は自動翻訳の対象外
        if message.content.startswith("/"):
            return

        # チャンネル制限がある場合、対象以外はスルー
        if config.TRANSLATION_CHANNEL_ID and message.channel.id != config.TRANSLATION_CHANNEL_ID:
            return

        if not self.translator:
            return

        try:
            # 言語自動判定のため仮呼び出し
            check = self.translator.translate_text(message.content, target_lang="JA")
            detected_lang = check.detected_source_lang

            # 韓国語 ⇄ 日本語 相互判定
            if detected_lang == "KO":
                target_lang = "JA"
            elif detected_lang == "JA":
                target_lang = "KO"
            else:
                return

            # 翻訳実行
            result = self.translator.translate_text(
                message.content, target_lang=target_lang
            )

            # 返信（リプライ）
            await message.reply(
                f"**[{detected_lang} ➔ {target_lang}]**\n{result.text}",
                mention_author=False,
            )

        except Exception as e:
            print(f"Translation Error: {e}")

async def setup(bot):
    await bot.add_cog(TranslationCog(bot))
