import asyncio
import traceback
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import config  # 先頭でインポート

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _fetch_apple_music_kpop_top_tracks(self):
        """Apple Musicの無料RSSフィードからランキング情報を非同期取得"""
        url = "https://rss.applemarketingtools.com/api/v2/jp/music/most-played/10/songs.json"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('feed', {}).get('results', [])
                    else:
                        print(f"[Apple Music Error] HTTP Status Code: {response.status}")
        except Exception as e:
            print(f"[Apple Music Fetch Error] {e}")
            traceback.print_exc()
        return []

    async def build_playlist_embed(self):
        """取得したデータをDiscord用のEmbedカードに変換"""
        try:
            results = await self._fetch_apple_music_kpop_top_tracks()
            if not results:
                print("[Embed Build Warning] RSSフィードからの結果が空です。")
                return None

            embed = discord.Embed(
                title="🎶 今週のヒットチャート (TOP 5)",
                description="Apple Musicの最新チャートよりお届けします！",
                color=0xFA243C  # Apple Musicカラー (赤)
            )
            
            # 1位の曲のジャケット画像をカードのサムネイル画像としてセット (高画質化)
            first_track = results[0]
            artwork = first_track.get('artworkUrl100')
            if artwork:
                img_url = artwork.replace("100x100bb", "500x500bb")
                embed.set_thumbnail(url=img_url)

            # 1位〜5位をリスト化
            for i, item in enumerate(results[:5], 1):
                track_name = item.get('name', '不明')
                artist_name = item.get('artistName', '不明')
                embed.add_field(name=f"{i}位：{track_name}", value=artist_name, inline=False)

            return embed
        except Exception as e:
            print(f"[Embed Build Error] {e}")
            traceback.print_exc()
            return None

    # --- コマンド手動実行 (/playlist) ---
    @app_commands.command(name="playlist", description="最新のヒットチャートを表示します")
    async def playlist_command(self, interaction: discord.Interaction):
        await interaction.response.defer()

        embed = await self.build_playlist_embed()
        
        if embed:
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("ランキングの取得に失敗しました。コンソールログを確認してください。")

    # /playlist 専用のエラーハンドラ
    @playlist_command.error
    async def playlist_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        print(f"[Playlist Command Error] {error}")
        traceback.print_exception(type(error), error, error.__traceback__)
        
        if interaction.response.is_done():
            await interaction.followup.send("コマンド実行中にエラーが発生しました。", ephemeral=True)
        else:
            await interaction.response.send_message("コマンド実行中にエラーが発生しました。", ephemeral=True)

async def setup(bot):
    await bot.add_cog(MusicCog(bot))
