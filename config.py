import os

# API Tokens & Keys
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
DEEPL_API_KEY = os.environ.get("DEEPL_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TMDB_API_KEY = os.environ.get("TMDB_API_KEY")
SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")

# チャンネルID設定 (環境変数または直接数値で指定)
# 特定のチャンネルでのみ動かす場合はID(整数)を指定
TRANSLATION_CHANNEL_ID = None  
TREND_CHANNEL_ID = 123456789012345678  # トレンド情報を投稿したいチャンネルID
MUSIC_CHANNEL_ID = 123456789012345678  # プレイリストを投稿したいチャンネルID
