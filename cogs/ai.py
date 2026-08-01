import discord
from discord import app_commands
from discord.ext import commands
from google import genai
import config

class AICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ai_client = genai.Client(api_key=config.GEMINI_API_KEY) if config.GEMINI_API_KEY else None

    @app_commands.command(name="ask", description="Geminiに質問・メッセージを送信します")
    @app_commands.describe(prompt="Geminiへの質問内容")
    async def ask(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()

        if not self.ai_client:
            await interaction.followup.send("Gemini APIキーが設定されていません。")
            return

        try:
            response = self.ai_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            text = response.text

            # 2000文字上限対策
            if len(text) > 2000:
                for i in range(0, len(text), 1900):
                    await interaction.followup.send(text[i : i + 1900])
            else:
                await interaction.followup.send(text)

        except Exception as e:
            await interaction.followup.send(f"Gemini APIエラー: {e}")

async def setup(bot):
    await bot.add_cog(AICog(bot))
