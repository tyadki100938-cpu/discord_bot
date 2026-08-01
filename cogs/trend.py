import asyncio
import traceback
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import config

class TrendCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _fetch_mdl_top_dramas(self):
        """
        RapidAPI 経由で MyDramaList から人気・話題の韓国ドラマを取得
        """
        api_key = getattr(config, 'RAPIDAPI_KEY', None)
        if not api_key:
            print("[MDL Error] RAPIDAPI_KEY が config に設定されていません。")
            return []

        # RapidAPI MyDramaList エンドポイント
        url = "https://mydramalist-api.p.rapidapi.com/search/titles"
        
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "mydramalist-api.p.rapidapi.com"
        }
        
        # パラメータ設定 (Type 2=Drama, Country KR=韓国, Top順)
        params = {
            "type": "2",       # 1: Movie, 2: Drama
            "country": "KR",   # 韓国
            "sort": "top",     # 人気順
            "page": "1"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get("results", [])
                        return results[:5]  # TOP 5を抽出
                    else:
                        error_text = await response.text()
                        print(f"[MDL API Error] Status: {response.status}, Body: {error_text}")
                        return []
        except Exception as e:
            print(f"[MDL Fetch Error] 通信エラーが発生しました: {e}")
            traceback.print_exc()
            return []

    async def build_kdrama_embeds(self):
        """MDLデータからDiscord Embedリストを生成"""
        shows = await self._fetch_mdl_top_dramas()
        if not shows:
            return []

        embeds = []
        for idx, show in enumerate(shows, 1):
            # APIの返却キーに合わせて取得（仕様変更時に柔軟に対応できるようfallbackを設定）
            title = show.get("title") or show.get("name", "タイトル不明")
            synopsis = show.get("synopsis") or show.get("description", "あらすじ準備中...")
            score = show.get("rating") or show.get("score", "N/A")
            cover_image = show.get("thumb") or show.get("poster") or show.get("image")
            link = show.get("link") or show.get("url", "")

            # あらすじが長すぎる場合はカット
            if len(synopsis) > 120:
                synopsis = synopsis[:120] + "..."

            embed = discord.Embed(
                title=f"{idx}位：{title}",
                url=link if link.startswith("http") else None,
                description=synopsis if synopsis else "説明はありません。",
                color=0x3B5998  # MDL風のブルー
            )
            embed.add_field(name="⭐ MDL Rating", value=f"{score} / 10", inline=True)

            if cover_image:
                embed.set_thumbnail(url=cover_image)

            embeds.append(embed)
        return embeds

    # --- 手動実行コマンド (/trend) ---
    @app_commands.command(name="trend", description="MyDramaList の話題の韓国ドラマ TOP5 を表示します")
    async def trend_command(self, interaction: discord.Interaction):
        await interaction.response.defer()

        embeds = await self.build_kdrama_embeds()

        if embeds:
            await interaction.followup.send("🎬 **【MyDramaList 今話題の韓国ドラマ TOP 5】**")
            for embed in embeds:
                await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("トレンド情報の取得に失敗したか、該当する作品が見つかりませんでした。")

    # /trend 専用のエラーハンドラ
    @trend_command.error
    async def trend_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        print(f"[Trend Command Error] {error}")
        traceback.print_exception(type(error), error, error.__traceback__)
        
        if interaction.response.is_done():
            await interaction.followup.send("コマンド実行中にエラーが発生しました。", ephemeral=True)
        else:
            await interaction.response.send_message("コマンド実行中にエラーが発生しました。", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TrendCog(bot))
