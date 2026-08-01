import asyncio
import datetime
import traceback
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

    async def _fetch_trending_tv(self, country: str = "KR"):
        """TMDB APIから今週のトレンドTV番組を非同期で取得
        :param country: 'KR' (韓国), 'JP' (日本)
        """
        api_key = getattr(config, 'TMDB_API_KEY', None)
        
        if not api_key:
            print("[Trend Error] TMDB_API_KEY が config に設定されていません。")
            return []

        # 週間トレンドAPIエンドポイントに変更
        url = "https://api.themoviedb.org/3/trending/tv/week"
        params = {
            "language": "ja-JP"
        }

        # 認証方式の自動判定 (Bearer Token か 通常の API Key か)
        headers = {}
        if api_key.startswith("eyJ"):  # Bearer Token (v4) の場合
            headers["Authorization"] = f"Bearer {api_key}"
        else:                         # API Key (v3) の場合
            params["api_key"] = api_key

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get("results", [])
                        
                        # 国・言語コードでフィルタリング (KR: 韓国語 'ko', JP: 日本語 'ja')
                        target_lang = "ko" if country == "KR" else "ja"
                        filtered_shows = [
                            show for show in results 
                            if show.get("original_language") == target_lang
                        ]
                        
                        return filtered_shows[:5]
                    else:
                        error_text = await response.text()
                        print(f"[TMDB API Error] Status: {response.status}, Body: {error_text}")
                        return []
        except Exception as e:
            print(f"[TMDB Fetch Error] 通信エラーが発生しました: {e}")
            traceback.print_exc()
            return []

    async def build_trend_embeds(self, country: str = "KR"):
        """トレンド情報のEmbedリストを生成"""
        shows = await self._fetch_trending_tv(country=country)
        if not shows:
            return []

        embeds = []
        for idx, show in enumerate(shows, 1):
            title = show.get("name") or show.get("original_name", "タイトル不明")
            overview = show.get("overview", "あらすじ準備中...")
            score = show.get("vote_average", 0.0)
            poster_path = show.get("poster_path")

            if len(overview) > 120:
                overview = overview[:120] + "..."

            embed = discord.Embed(
                title=f"{idx}位：{title}",
                description=overview if overview else "説明はありません。",
                color=0xE50914
            )
            embed.add_field(name="⭐ 評価", value=f"{score:.1f} / 10", inline=True)

            if poster_path:
                embed.set_thumbnail(url=f"{TMDB_IMAGE_BASE_URL}{poster_path}")
            
            embeds.append(embed)
        return embeds

    # --- ① 定期実行タスク (毎週日曜日 朝8:00) ---
    @tasks.loop(time=TARGET_TIME)
    async def send_weekly_trends(self):
        # 毎週日曜日（weekday == 6）のみ実行
        if datetime.datetime.now(JST).weekday() != 6:
            return

        channel_id = getattr(config, 'TREND_CHANNEL_ID', None)
        if not channel_id:
            print("[Trend Task Warning] TREND_CHANNEL_ID が設定されていません。")
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            print(f"[Trend Task Error] チャンネルID ({channel_id}) が見つかりませんでした。")
            return

        categories = [
            ("🇰🇷 **今週の韓国ドラマ TOP 5**", "KR"),
            ("🇯🇵 **今週の日本ドラマ・番組 TOP 5**", "JP")
        ]

        await channel.send("🎬 **【今週の話題作・トレンドランキング配信】**")

        for title, country_code in categories:
            embeds = await self.build_trend_embeds(country=country_code)
            if embeds:
                await channel.send(f"\n### {title}")
                for embed in embeds:
                    await channel.send(embed=embed)
            await asyncio.sleep(1)

    @send_weekly_trends.before_loop
    async def before_send_weekly_trends(self):
        await self.bot.wait_until_ready()

    # --- ② コマンド手動実行（/trend） ---
    @app_commands.command(name="trend", description="今週の韓国・日本ドラマランキングを表示します")
    @app_commands.describe(category="絞り込むカテゴリを選択してください")
    @app_commands.choices(category=[
        app_commands.Choice(name="🇰🇷 韓国ドラマ", value="KR"),
        app_commands.Choice(name="🇯🇵 日本ドラマ・番組", value="JP"),
    ])
    async def trend_command(self, interaction: discord.Interaction, category: app_commands.Choice[str] = None):
        await interaction.response.defer()

        # オプション未選択時はデフォルトで「韓国ドラマ」を表示
        selected_country = category.value if category else "KR"
        category_name = category.name if category else "🇰🇷 韓国ドラマ"

        embeds = await self.build_trend_embeds(country=selected_country)

        if embeds:
            await interaction.followup.send(f"🎬 **【今週のトレンドランキング - {category_name}】**")
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
