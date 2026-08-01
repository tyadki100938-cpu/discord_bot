import asyncio
import datetime
from zoneinfo import ZoneInfo
import discord
from discord import app_commands
from discord.ext import commands, tasks
import requests
import yt_dlp

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}
YDL_OPTIONS = {'format': 'bestaudio/best'}

# 日本時間（JST）の午前8:00を指定
JST = ZoneInfo("Asia/Tokyo")
TARGET_TIME = datetime.time(hour=8, minute=0, second=0, tzinfo=JST)

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.send_weekly_playlist.start()

    def cog_unload(self):
        self.send_weekly_playlist.cancel()

    def _fetch_apple_music_kpop_top_tracks(self):
        """Apple Musicの無料RSSフィードからK-POPのランキング情報を取得（同期処理）"""
        url = "https://rss.applemarketingtools.com/api/v2/jp/music/most-played/10/by-genre/11/songs.json"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.json().get('feed', {}).get('results', [])
            else:
                print(f"[Apple Music Error] Status Code: {response.status_code}")
        except Exception as e:
            print(f"[Apple Music Fetch Error] {e}")
        return []

    async def build_playlist_embed(self):
        """取得したデータをDiscord用のEmbedカードに変換（非同期化）"""
        try:
            results = await asyncio.to_thread(self._fetch_apple_music_kpop_top_tracks)
            if not results:
                return None

            embed = discord.Embed(
                title="🎶 今週のK-POPヒットチャート (TOP 5)",
                description="Apple Musicの最新チャートよりお届けします！",
                color=0xFA243C # Apple Musicカラー (赤)
            )
            
            # 1位の曲のジャケット画像をカードのサムネイル画像としてセット (高画質化)
            if results[0].get('artworkUrl100'):
                img_url = results[0]['artworkUrl100'].replace("100x100bb", "500x500bb")
                embed.set_thumbnail(url=img_url)

            # 1位〜5位をリスト化
            for i, item in enumerate(results[:5], 1):
                track_name = item.get('name', '不明')
                artist_name = item.get('artistName', '不明')
                embed.add_field(name=f"{i}位：{track_name}", value=artist_name, inline=False)

            return embed
        except Exception as e:
            print(f"[Embed Build Error] {e}")
            return None

    # --- ① 定期実行タスク（毎週日曜日 朝8:00） ---
    @tasks.loop(time=TARGET_TIME)
    async def send_weekly_playlist(self):
        # 今日が「日曜日（weekday() == 6）」でなければスキップ
        if datetime.datetime.now(JST).weekday() != 6:
            return

        import config
        channel_id = getattr(config, 'MUSIC_CHANNEL_ID', None)
        if not channel_id:
            print("[Music Task Warning] MUSIC_CHANNEL_ID が設定されていません。")
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            print(f"[Music Task Error] チャンネルID ({channel_id}) が見つかりませんでした。")
            return

        embed = await self.build_playlist_embed()
        if embed:
            await channel.send(embed=embed)

    @send_weekly_playlist.before_loop
    async def before_send_weekly_playlist(self):
        await self.bot.wait_until_ready()

    # --- ② コマンド手動実行 (/playlist) ---
    @app_commands.command(name="playlist", description="最新のK-POPヒットチャートを表示します")
    async def playlist_command(self, interaction: discord.Interaction):
        # 最優先で defer() を呼んでタイムアウトを防止
        await interaction.response.defer()

        embed = await self.build_playlist_embed()
        
        if embed:
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("ランキングの取得に失敗しました。ログを確認してください。")

    # --- ③ VC音源再生用のスラッシュコマンド (/play) ---
    @app_commands.command(name="play", description="ボイスチャンネルでYouTube等の音声を再生します")
    @app_commands.describe(url="再生したいYouTubeなどのURL")
    async def play(self, interaction: discord.Interaction, url: str):
        if not interaction.user.voice:
            await interaction.response.send_message("ボイスチャンネルに入ってから実行してください！", ephemeral=True)
            return

        await interaction.response.defer()
        channel = interaction.user.voice.channel
        
        vc = interaction.guild.voice_client
        if not vc:
            try:
                vc = await channel.connect()
            except Exception as e:
                print(f"[VC Connect Error] {e}")
                await interaction.followup.send("ボイスチャンネルへの接続に失敗しました。")
                return

        try:
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = await asyncio.to_thread(ydl.extract_info, url, download=False)
                stream_url = info['url']
                title = info.get('title', '音声')
                
                source = await discord.FFmpegOpusAudio.from_probe(stream_url, **FFMPEG_OPTIONS)
                
                if vc.is_playing():
                    vc.stop()
                
                vc.play(source)
                await interaction.followup.send(f"🎵 再生中: **{title}**")
        except Exception as e:
            print(f"[Play Command Error] {e}")
            await interaction.followup.send(f"再生エラーが発生しました: {e}")

async def setup(bot):
    await bot.add_cog(MusicCog(bot))
