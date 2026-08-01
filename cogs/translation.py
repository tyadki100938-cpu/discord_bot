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
        # ボットの発言、または空メッセージは無視
        if message.author.bot or not message.content.strip():
            return

        # スラッシュコマンドやコマンド文字は対象外
        if message.content.startswith("/") or message.content.startswith("!"):
            return

        # チャンネル制限がある場合、対象以外はスルー
        if config.TRANSLATION_CHANNEL_ID and message.channel.id != config.TRANSLATION_CHANNEL_ID:
            return

        if not self.translator:
            return

        try:
            # 1. まず「日本語」宛てに1回だけ翻訳してみる
            result = self.translator.translate_text(message.content, target_lang="JA")
            detected_lang = result.detected_source_lang

            # 2. 判定結果に応じて処理を分岐
            if detected_lang == "KO":
                # 元が韓国語だった場合 ➔ 1回目で「日本語」に翻訳された結果をそのまま使う
                final_text = result.text
                target_lang = "JA"

            elif detected_lang == "JA":
                # 元が日本語だった場合 ➔ 改めて「韓国語」に翻訳を行う
                result_ko = self.translator.translate_text(message.content, target_lang="KO")
                final_text = result_ko.text
                target_lang = "KO"

            else:
                # 韓国語でも日本語でもない場合は無視
                return

            # 返信（リプライ）
            await message.reply(
                f"**[{detected_lang} ➔ {target_lang}]**\n{final_text}",
                mention_author=False,
            )

        except Exception as e:
            print(f"Translation Error: {e}")

async def setup(bot):
    await bot.add_cog(TranslationCog(bot))
