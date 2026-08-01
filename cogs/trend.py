import asyncio
import datetime
from zoneinfo import ZoneInfo
import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiohttp
import config  # 先頭でインポート

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

    async def _fetch_trending_tv(self):
        """TMDB APIから今週のトレンドTV番組を非同期で取得"""
        api_key = getattr(config, 'TMDB_API_KEY', None)
        
        if not api_key:
            print("[Trend Error] TMDB_API_KEY が config に設定されていません。")
            return []

        url = "https://api.themoviedb.org/3/trending/tv/week"
        
        # 認証方式の自動判定 (Bearer Token か 通常の API Key か)
        headers = {}
        params = {"language": "ja-JP"}

        if api_key.startswith("eyJ"):  # Bearer Token (v4) の場合
            headers["Authorization"] = f"Bearer {api_key}"
        else:                         # API Key (v3) の場合
            params["api_key"] = api_key

        try:
            # aiohttpによる完全非同期通信
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("results", [])[:5]
                    else:
                        error_text = await response.text()
                        print(f"[TMDB API Error] Status: {response.status}, Body: {error_text}")
                        return []
        except Exception as e:
            print(f"[TMDB Fetch Error] 通信エラーが発生しました: {e}")
            return []

    async def build_trend_embeds(self):
        """トレンド情報のEmbedリストを生成"""
        shows = await self._fetch_trending_tv()
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

    # --- ① 定期実行タスク ---
    @tasks.loop(time=TARGET_TIME)
    async def send_weekly_trends(self):
        if datetime.datetime.now(JST).weekday() != 6:
            return

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
        await interaction.response.defer()

        embeds = await self.build_trend_embeds()

        if embeds:
            await interaction.followup.send("🎬 **【今週の話題作・トレンドランキング】**")
            for embed in embeds:
                await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("トレンド情報の取得に失敗しました。コンソールログのエラー内容を確認してください。")

async def setup(bot):
    await bot.add_cog(TrendCog(bot))
