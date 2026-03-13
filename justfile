# デフォルト: レシピ一覧を表示
default:
    @just --list

# Web アプリを起動（ホットリロード有効）
app:
    uv run uvicorn app.main:app --reload

# 実験をデバッグモードで実行
debug exp:
    cd src/{{exp}} && uv run python train.py

# 実験を本番モードで実行
train exp:
    cd src/{{exp}} && uv run python train.py debug=false

# 推論を実行
infer exp:
    cd src/{{exp}} && uv run python inference.py

# TTA 推論を実行
infer-tta exp:
    cd src/{{exp}} && uv run python inference_tta.py
