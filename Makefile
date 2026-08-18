# Kaggle テンプレート用タスク定義（make <target> で実行）
.DEFAULT_GOAL := help

.PHONY: help app lint format fix typecheck test css clean

help: ## ターゲット一覧を表示
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-12s\033[0m %s\n", $$1, $$2}'

app: ## Web アプリを起動（ホットリロード有効、空きポート自動選択）
	@port=8000; \
	while lsof -i :$$port -sTCP:LISTEN >/dev/null 2>&1; do \
		port=$$((port + 1)); \
	done; \
	echo "Starting on port $$port"; \
	uv run uvicorn app.main:app --reload --port $$port

lint: ## Lint（ruff check）
	uv run ruff check src/ app/ tests/ tools/ .claude/hooks/

format: ## Format（ruff format）
	uv run ruff format src/ app/ tests/ tools/ .claude/hooks/

fix: ## Lint 自動修正 + Format
	uv run ruff check --fix src/ app/ tests/ tools/ .claude/hooks/
	uv run ruff format src/ app/ tests/ tools/ .claude/hooks/

typecheck: ## 型チェック（ty）
	uv run ty check src/ app/

test: ## テスト実行（scikit-learn を一時追加して pytest）
	uv run --with scikit-learn pytest

css: ## Tailwind CSS を再ビルド（テンプレートに新しいクラスを追加したら実行）
	cd app/static/build && npm install --silent && npm run build

clean: ## キャッシュディレクトリを削除
	rm -rf .ruff_cache .pytest_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
