import asyncio
import datetime
from zoneinfo import ZoneInfo
import discord
from discord import app_commands
from discord.ext import commands, tasks
import requests

TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

# 日本時間（JST）の午前8:00を指定
JST = ZoneInfo("Asia/Tokyo")
TARGET_TIME = datetime.time(hour=8, minute=0, second=0, tzinfo=JST)

class TrendCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.send_weekly_trends.start()

    def cog_unload(self):
        self.send_weekly_trends.cancel()

    def _fetch_trending_tv_sync(self):
        """TMDB APIから今週のトレンドTV番組を取得（同期処理）"""
        import config
        api_key = getattr(config, 'TMDB_API_KEY', None)
        
        if not api_key:
            print("[Trend Error] TMDB_API_KEY が config に設定されていません。")
            return []

        url = "https://api.themoviedb.org/3/trending/tv/week"
        params = {
            "api_key": api_key,
            "language": "ja-JP"
        }
        try:
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                return response.json().get("results", [])[:5]
            else:
                print(f"[TMDB API Error] Status Code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            print(f"[TMDB Fetch Error] {e}")
        return []

    async def build_trend_embeds(self):
        """トレンド情報のEmbedリストを生成（非同期化）"""
        shows = await asyncio.to_thread(self._fetch_trending_tv_sync)
        if not shows:
            return []

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
        if datetime.datetime.now(JST).weekday() != 6:
            return

        import config
        channel_id = getattr(config, 'TREND_CHANNEL_ID', None)
        if not channel_id:
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            return

        embeds = await self.build_trend_embeds()
        if not embeds:
            return

        await channel.send("🎬 **【今週の話題作・トレンドランキング】**")
        for embed in embeds:
            await channel.send(embed=embed)

    @send_weekly_trends.before_loop
    async def before_send_weekly_trends(self):
        await self.bot.wait_until_ready()

    # --- ② コマンド手動実行（/trend） ---
    @app_commands.command(name="trend", description="今週の話題作・トレンドランキングを表示します")
    async def trend_command(self, interaction: discord.Interaction):
        # 1. タイムアウト防止のため最優先で defer()
        await interaction.response.defer()

        # 2. 非同期で安全にTMDBデータ取得＆Embed生成
        embeds = await self.build_trend_embeds()

        if embeds:
            await interaction.followup.send("🎬 **【今週の話題作・トレンドランキング】**")
            for embed in embeds:
                await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("トレンド情報の取得に失敗しました。`TMDB_API_KEY` の設定またはログを確認してください。")

async def setup(bot):
    await bot.add_cog(TrendCog(bot))
