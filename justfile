# デフォルト: レシピ一覧を表示
default:
    @just --list

# Web アプリを起動（ホットリロード有効、空きポート自動選択）
app:
    #!/usr/bin/env bash
    port=8000
    while lsof -i :"$port" -sTCP:LISTEN >/dev/null 2>&1; do
        port=$((port + 1))
    done
    echo "Starting on port $port"
    uv run uvicorn app.main:app --reload --port "$port"
