import datetime
from zoneinfo import ZoneInfo
import discord
from discord import app_commands
from discord.ext import commands, tasks
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp
import config

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
        if config.SPOTIFY_CLIENT_ID and config.SPOTIFY_CLIENT_SECRET:
            self.sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
                client_id=config.SPOTIFY_CLIENT_ID,
                client_secret=config.SPOTIFY_CLIENT_SECRET
            ))
            self.send_weekly_playlist.start()
        else:
            self.sp = None

    def cog_unload(self):
        if self.sp:
            self.send_weekly_playlist.cancel()

    def build_playlist_embed(self):
        """Spotifyからプレイリスト情報を取得してEmbedを作成する共通処理"""
        if not self.sp:
            return None

        # 例: Spotify公式「K-Pop ON!」プレイリストID
        playlist_id = '37i9dQZF1DX9tPFwD21M3M'
        results = self.sp.playlist(playlist_id)

        embed = discord.Embed(
            title="🎶 今週のK-POPおすすめプレイリスト",
            url=results['external_urls']['spotify'],
            color=0x1DB954
        )
        if results.get('images'):
            embed.set_thumbnail(url=results['images'][0]['url'])

        tracks = results['tracks']['items'][:5]
        for i, item in enumerate(tracks, 1):
            track = item['track']
            artist = track['artists'][0]['name']
            embed.add_field(name=f"{i}. {track['name']}", value=artist, inline=False)

        return embed

    # --- ① 定期実行タスク（毎週日曜日 朝8:00） ---
    @tasks.loop(time=TARGET_TIME)
    async def send_weekly_playlist(self):
        # 今日が「日曜日（weekday() == 6）」でなければスキップ
        if datetime.datetime.now(JST).weekday() != 6:
            return

        if not config.MUSIC_CHANNEL_ID or not self.sp:
            return

        channel = self.bot.get_channel(config.MUSIC_CHANNEL_ID)
        if not channel:
            return

        embed = self.build_playlist_embed()
        if embed:
            await channel.send(embed=embed)

    @send_weekly_playlist.before_loop
    async def before_send_weekly_playlist(self):
        await self.bot.wait_until_ready()

    # --- ② コマンド手動実行（/playlist） ---
    @app_commands.command(name="playlist", description="おすすめのK-POPプレイリストを表示します")
    async def playlist_command(self, interaction: discord.Interaction):
        if not self.sp:
            await interaction.response.send_message("Spotify APIが設定されていません。", ephemeral=True)
            return

        await interaction.response.defer()
        embed = self.build_playlist_embed()
        if embed:
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("プレイリストの取得に失敗しました。")

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
            vc = await channel.connect()

        try:
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(url, download=False)
                stream_url = info['url']
                title = info.get('title', '音声')
                
                source = await discord.FFmpegOpusAudio.from_probe(stream_url, **FFMPEG_OPTIONS)
                
                if vc.is_playing():
                    vc.stop()
                
                vc.play(source)
                await interaction.followup.send(f"🎵 再生中: **{title}**")
        except Exception as e:
            await interaction.followup.send(f"再生エラー: {e}")

async def setup(bot):
    await bot.add_cog(MusicCog(bot))
