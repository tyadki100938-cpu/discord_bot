import os

# API Tokens & Keys
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
DEEPL_API_KEY = os.environ.get("DEEPL_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# チャンネルID設定 (環境変数または直接数値で指定)
# 特定のチャンネルでのみ動かす場合はID(整数)を指定
TRANSLATION_CHANNEL_ID = None  
