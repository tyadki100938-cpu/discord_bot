#!/bin/bash

# エラーが発生したらその時点でスクリプトを終了させる
set -e

# 現在の日時を取得（コミットメッセージ用）
CURRENT_DATE=$(date "+%Y-%m-%d %H:%M:%S")

echo "🚀 Git自動コミット処理を開始します... ($CURRENT_DATE)"

# 1. 変更されたファイルをすべて追加
git add .

# 2. コミット（メッセージに日時を含める）
# ※変更がない場合にエラーにならないよう、条件分岐を入れるとより安全です
if ! git diff-index --quiet HEAD --; then
    git commit -m "Auto-commit: $CURRENT_DATE"
    
    # 3. リモートリポジトリ（現在設定されているブランチ）にプッシュ
    git push origin HEAD
    echo "🎉 リモートへのプッシュが完了しました！"
else
    echo "✨ 変更点がないため、コミットはスキップされました。"
fi
