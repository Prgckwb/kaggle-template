---
name: kaggle:add-app-page
description: ダッシュボードに新しいページや可視化を対話的に追加する。既存パターンに従った実装。
argument-hint: [追加したい内容の概要]
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Glob, Edit
---

# ダッシュボードにページ・可視化を追加する

ユーザーと対話しながら、Web ダッシュボード（FastAPI + htmx + Jinja2）に新しいページや可視化を追加する。

## 前提知識

### アーキテクチャ

- **フレームワーク**: FastAPI + Jinja2 + htmx
- **スタイル**: Tailwind CSS (CDN)、FontAwesome 6 Free（アイコン）、Nunito フォント
- **カラー**: エメラルドアクセント（`emerald-500` = `#10b981`）
- **レイアウト**: 左サイドバー（固定 w-64）+ メインコンテンツ（`ml-64`）

### ファイル構成

```
app/
├── main.py             # Router 登録
├── template_env.py     # Jinja2 環境（フィルタ・グローバル）
├── utils.py            # 再エクスポートファサード
├── services/           # ビジネスロジック
├── pages/              # APIRouter（各ページ）
├── templates/
│   ├── base.html       # 共通レイアウト
│   ├── components/     # 再利用マクロ（_badge, _metric_card, _empty_state, _data_table, _markdown, _yaml_viewer）
│   ├── partials/       # htmx 差し替え用パーシャル
│   └── {page}/         # 各ページのテンプレート
└── static/             # JS/CSS（htmx, highlight.js, Chart.js）
```

### コーディング規則

- エンドポイントは `def`（非 `async`）で定義
- `is_htmx(request)` で full page / partial を出し分け
- テンプレートは `base.html` を extends
- `active_page` 変数でサイドバーのアクティブ状態を制御
- アイコンは FontAwesome（絵文字は使わない）
- コンポーネントは `{% from "components/_xxx.html" import xxx %}` で使用

## フェーズ 1: 要件のヒアリング

1. **何を見たいか確認する**
   - $ARGUMENTS があればそこから意図を読み取る
   - 「どんな情報を可視化したいですか？」
   - 「それはどんな場面で見たいですか？」

2. **既存ページとの関係を判断する**
   - 既存ページ一覧を提示:
     - **Home** (`/`): ダッシュボードトップ
     - **Experiments** (`/experiments`): 実験一覧・詳細・OOF・スコアグラフ
     - **Data** (`/data`): input/ 配下のファイル閲覧・CSV プレビュー・画像ギャラリー
     - **Discussions** (`/discussions`): Discussion ドキュメント閲覧
     - **Knowledge** (`/knowledge`): 公式情報・実験知見の閲覧
     - **Notebooks** (`/notebooks`): Jupyter Notebook 一覧
   - 「既存のページに追加するのが自然ですか？それとも新しいページが必要ですか？」
   - **可能な限り既存ページへの追加を推奨する**（ユーザーの認知負荷を減らすため）

3. **データソースを確認する**
   - 表示するデータがどこにあるか（ファイル、API、計算結果等）
   - 必要なサービス関数が既存にあるか確認

## フェーズ 2: 設計の提案

ユーザーに以下を提示して合意を得る:

1. **配置**: 新規ページ or 既存ページのどのセクションに追加するか
2. **UI 概要**: どんな見た目になるか（テーブル、カード、グラフ、タブ等）を言葉で説明
3. **使用コンポーネント**: 既存コンポーネント（`_metric_card`, `_badge`, `_empty_state`, `_data_table`）のどれを使うか
4. **htmx パターン**: 動的更新が必要か（検索、タブ切り替え、遅延ロード等）
5. **必要なファイル変更の一覧**

## フェーズ 3: 実装

### 新規ページの場合

1. **サービス関数を作成**（`app/services/` に追加、または既存ファイルに追加）
2. **Router を作成**（`app/pages/{page_name}.py`）
   - 既存の Router パターンに従う:
     ```python
     from app.template_env import templates
     from app.utils import is_htmx, ...
     router = APIRouter()
     ```
3. **テンプレートを作成**
   - `app/templates/{page_name}/` ディレクトリ
   - full page テンプレート: `base.html` を extends
   - partial テンプレート: `app/templates/partials/` に配置
4. **`app/main.py`** に Router を登録
5. **`base.html`** のサイドバーにナビリンクを追加
   - FontAwesome アイコンを選択
   - `active_page` の条件分岐を追加

### 既存ページへの追加の場合

1. 必要ならサービス関数を追加
2. 既存の Router にエンドポイントを追加
3. 既存テンプレートを編集、または partial を追加
4. htmx で動的ロードする場合は partial エンドポイントを追加

### スタイリングの遵守事項

- カード: `bg-white rounded-2xl shadow-sm border border-gray-200`
- ボタン (primary): `bg-emerald-500 text-white rounded-full font-bold`
- バッジ: `rounded-full bg-{color}-50 text-{color}-600 text-xs font-semibold px-3 py-1`
- アイコン背景: `rounded-xl w-{size} h-{size} bg-{color}-50 flex items-center justify-center`
- テキスト: 主 `text-gray-800`、副 `text-gray-500`、ミュート `text-gray-400`
- **絵文字は使わない**。必ず FontAwesome アイコンを使用する。

## フェーズ 4: 動作確認

1. `just app` または `uv run uvicorn app.main:app --reload` でアプリを起動
2. ブラウザで該当ページにアクセスし、表示を確認
3. htmx の動的更新が正しく動作するか確認
4. エラーがあれば修正

## フェーズ 5: 完了報告

- 追加・変更したファイルの一覧を表示
- アクセス URL を表示
- 追加した機能の概要を説明
