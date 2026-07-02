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

# Lint（ruff check）
lint:
    uv run ruff check src/ app/ tests/

# Format（ruff format）
format:
    uv run ruff format src/ app/ tests/

# Lint 自動修正 + Format
fix:
    uv run ruff check --fix src/ app/ tests/ && uv run ruff format src/ app/ tests/

# 型チェック（ty）
typecheck:
    uv run ty check src/ app/

# テスト実行（scikit-learn を一時追加して pytest）
test:
    uv run --with scikit-learn pytest

# キャッシュディレクトリを削除
clean:
    rm -rf .ruff_cache .pytest_cache
    find . -type d -name __pycache__ -prune -exec rm -rf {} +
