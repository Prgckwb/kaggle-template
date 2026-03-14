# デフォルト: レシピ一覧を表示
default:
    @just --list

# Web アプリを起動（ホットリロード有効）
app:
    uv run uvicorn app.main:app --reload

# 実験をデバッグモードで実行
debug exp:
    cd src/{{exp}} && uv run python train.py
