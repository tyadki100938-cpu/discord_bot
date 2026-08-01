import asyncio
import datetime
from zoneinfo import ZoneInfo
import discord
from discord import app_commands
from discord.ext import commands, tasks
import requests

JST = ZoneInfo("Asia/Tokyo")
TARGET_TIME = datetime.time(hour=8, minute=0, second=0, tzinfo=JST)

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.send_weekly_playlist.start()

    def cog_unload(self):
        self.send_weekly_playlist.cancel()

    def _fetch_apple_music_top_tracks(self):
        """Apple Musicの無料RSSフィードからK-POP/J-POPのトレンドを取得"""
        # 日本のTop 100ソングを取得するRSS URL (認証不要)
        url = "https://rss.applemarketingtools.com/api/v2/jp/music/most-played/10/songs.json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json().get('feed', {}).get('results', [])
        return []

    async def build_playlist_embed(self):
        try:
            results = await asyncio.to_thread(self._fetch_apple_music_top_tracks)
            if not results:
                return None

            embed = discord.Embed(
                title="🎶 今週のヒットチャート (Top 5)",
                color=0xFA243C # Apple Musicカラー
            )
            
            # 1位のジャケット画像をサムネイルに設定
            if results[0].get('artworkUrl100'):
                # 高画質化処理
                img_url = results[0]['artworkUrl100'].replace("100x100bb", "500x500bb")
                embed.set_thumbnail(url=img_url)

            for i, item in enumerate(results[:5], 1):
                track_name = item.get('name', '不明')
                artist_name = item.get('artistName', '不明')
                embed.add_field(name=f"{i}. {track_name}", value=artist_name, inline=False)

            return embed
        except Exception as e:
            print(f"[Music Fetch Error] {e}")
            return None

    # --- ① 定期実行タスク ---
    @tasks.loop(time=TARGET_TIME)
    async def send_weekly_playlist(self):
        if datetime.datetime.now(JST).weekday() != 6:
            return

        if not config.MUSIC_CHANNEL_ID:
            return

        channel = self.bot.get_channel(config.MUSIC_CHANNEL_ID)
        if not channel:
            return

        embed = await self.build_playlist_embed()
        if embed:
            await channel.send(embed=embed)

    @send_weekly_playlist.before_loop
    async def before_send_weekly_playlist(self):
        await self.bot.wait_until_ready()

    # --- ② コマンド手動実行 (/playlist) ---
    @app_commands.command(name="playlist", description="今週のヒットチャートを表示します")
    async def playlist_command(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = await self.build_playlist_embed()
        
        if embed:
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("ランキングの取得に失敗しました。")

async def setup(bot):
    await bot.add_cog(MusicCog(bot))
