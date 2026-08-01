import datetime
from zoneinfo import ZoneInfo
import discord
from discord import app_commands
from discord.ext import commands, tasks
import requests
import config

TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

# 日本時間（JST）の午前8:00を指定
JST = ZoneInfo("Asia/Tokyo")
TARGET_TIME = datetime.time(hour=8, minute=0, second=0, tzinfo=JST)

class TrendCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if config.TMDB_API_KEY:
            self.send_weekly_trends.start()

    def cog_unload(self):
        self.send_weekly_trends.cancel()

    def get_trending_tv(self):
        """TMDB APIから今週のトレンドTV番組を取得"""
        url = "https://api.themoviedb.org/3/trending/tv/week"
        params = {
            "api_key": config.TMDB_API_KEY,
            "language": "ja-JP"
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get("results", [])[:5]
        return []

    def build_trend_embeds(self, shows):
        """トレンド情報のEmbedリストを生成する共通処理"""
        embeds = []
        for idx, show in enumerate(shows, 1):
            title = show.get("name", "タイトル不明")
            overview = show.get("overview", "あらすじ準備中...")
            score = show.get("vote_average", 0.0)
            poster_path = show.get("poster_path")

            if len(overview) > 120:
                overview = overview[:120] + "..."

            embed = discord.Embed(
                title=f"{idx}位：{title}",
                description=overview or "説明はありません。",
                color=0xE50914
            )
            embed.add_field(name="⭐ 評価", value=f"{score:.1f} / 10", inline=True)

            if poster_path:
                embed.set_thumbnail(url=f"{TMDB_IMAGE_BASE_URL}{poster_path}")
            
            embeds.append(embed)
        return embeds

    # --- ① 定期実行タスク（毎週日曜日 朝8:00） ---
    @tasks.loop(time=TARGET_TIME)
    async def send_weekly_trends(self):
        # 今日が「日曜日（weekday() == 6）」でなければスキップ
        if datetime.datetime.now(JST).weekday() != 6:
            return

        if not config.TREND_CHANNEL_ID:
            return

        channel = self.bot.get_channel(config.TREND_CHANNEL_ID)
        if not channel:
            return

        shows = self.get_trending_tv()
        if not shows:
            return

        await channel.send("🎬 **【今週の話題作・トレンドランキング】**")
        embeds = self.build_trend_embeds(shows)
        for embed in embeds:
            await channel.send(embed=embed)

    @send_weekly_trends.before_loop
    async def before_send_weekly_trends(self):
        await self.bot.wait_until_ready()

    # --- ② コマンド手動実行（/trend） ---
    @app_commands.command(name="trend", description="今週の話題作・トレンドランキングを表示します")
    async def trend_command(self, interaction: discord.Interaction):
        await interaction.response.defer()

        shows = self.get_trending_tv()
        if not shows:
            await interaction.followup.send("トレンド情報の取得に失敗しました。")
            return

        embeds = self.build_trend_embeds(shows)
        await interaction.followup.send("🎬 **【今週の話題作・トレンドランキング】**")
        for embed in embeds:
            await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(TrendCog(bot))
