#!/usr/bin/env bash
# エラーが発生したら即座に停止
set -o errexit

# 1. Pythonライブラリのインストール
pip install -r requirements.txt
