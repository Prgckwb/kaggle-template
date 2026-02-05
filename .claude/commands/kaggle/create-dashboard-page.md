# ダッシュボードにページを追加

FastAPI + htmx ダッシュボードに新しいページを追加してください。

## 手順

1. ユーザーに以下を質問（$ARGUMENTS で渡されていない場合）:
   - ページ名（URL パスになる、例: `eda`, `results`, `comparison`）
   - ページの目的・表示内容

2. `app/pages/` に新しいルーターファイルを作成
   - ファイル名: `{ページ名}.py`
   - FastAPI の APIRouter を使用
   - テンプレートをレンダリングするエンドポイントを作成

3. `app/templates/` に対応するテンプレートを作成
   - ファイル名: `{ページ名}.html`
   - htmx を活用したインタラクティブな要素を含める
   - 既存の `index.html` のスタイルを継承

4. `app/main.py` にルーターを登録
   - `include_router` で新しいルーターを追加

5. `app/templates/index.html` のナビゲーションにリンクを追加

## 引数

$ARGUMENTS にページ名が渡される場合があります（例: `eda`）。

## 完了後

- 作成したファイルの一覧を報告
- アプリの起動コマンドを案内: `uv run uvicorn app.main:app --reload`
