#!/usr/bin/env bash
# エラーが発生したら即座に停止
set -o errexit

# 1. パッケージリストの更新と ffmpeg のインストール
apt-get update && apt-get install -y ffmpeg

# 2. Pythonライブラリのインストール
pip install -r requirements.txt
