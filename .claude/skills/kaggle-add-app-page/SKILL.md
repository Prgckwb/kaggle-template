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
- **レイアウト**: 左サイドバー（固定 w-64、トグル可）+ メインコンテンツ（`ml-64` / `ml-0`）
- **スタイルの詳細**: `app/README.md` を参照

### ファイル構成

```
app/
├── main.py             # Router 登録
├── template_env.py     # Jinja2 環境（フィルタ・グローバル）
├── services/           # ビジネスロジック
├── pages/              # APIRouter（各ページ）
├── templates/
│   ├── base.html       # 共通レイアウト（サイドバー + メイン）
│   ├── components/     # 再利用マクロ（_badge, _metric_card, _empty_state, _data_table, _markdown, _yaml_viewer）
│   ├── partials/       # htmx 差し替え用パーシャル
│   └── {page}/         # 各ページのテンプレート
└── static/             # JS/CSS（htmx, highlight.js, Chart.js）
```

### 既存ページ一覧

- **Home** (`/`): ダッシュボードトップ
- **Experiments** (`/experiments`): 実験一覧・詳細・OOF・スコアグラフ
- **Data** (`/data`): input/ 配下のファイル閲覧（ツリー表示・CSV プレビュー・画像ギャラリー）
- **Knowledge** (`/knowledge`): 公式情報・ディスカッション・実験知見（3カテゴリ）
  - `/knowledge/{category}`: カテゴリ別ドキュメント一覧（official / insights / discussion）
  - `/knowledge/{category}/{filename}`: ドキュメント詳細（全幅マークダウン表示）

### コーディング規則

- エンドポイントは `def`（非 `async`）で定義
- `is_htmx(request)` で full page / partial を出し分け
- テンプレートは `base.html` を extends
- `active_page` 変数でサイドバーのアクティブ状態を制御
- アイコンは FontAwesome（絵文字は使わない）
- コンポーネントは `{% from "components/_xxx.html" import xxx %}` で使用

### 新ページ追加の方針

**サブページ優先**: 新しいコンテンツは、まず既存セクションのサブページとして追加を検討する。

- **Knowledge**: カテゴリを追加（`app/pages/knowledge.py` の `KNOWLEDGE_PAGES` 辞書に `type: "category"` のエントリを1つ追加）
- **Experiments**: 詳細ページのタブを追加
- **Data**: ファイルタイプ別プレビューを追加

**トップレベルのサイドバー項目追加は最終手段**。新しいトップレベル項目を追加する場合は:
1. `base.html` のサイドバーに折りたたみ可能なナビアイテムとして追加
2. Home (`index.html`) のカードグリッドにも追加
3. `app/main.py` に Router を登録

### サイドバーの構造

サイドバーは折りたたみ可能なサブアイテムを持つ構造:
- トップレベル: ラベル（`<a>` でページ遷移）+ シェブロンボタン（展開/折りたたみ）
- サブアイテム: 展開時に表示される子リンク（静的 or htmx 遅延読み込み）
- サイドバー自体はトグルボタンで表示/非表示切替（`localStorage` で永続化）

## フェーズ 1: 要件のヒアリング

1. **何を見たいか確認する**
   - $ARGUMENTS があればそこから意図を読み取る
   - 「どんな情報を可視化したいですか？」
   - 「それはどんな場面で見たいですか？」

2. **既存ページとの関係を判断する**
   - 上記の既存ページ一覧を提示
   - 「既存のページに追加するのが自然ですか？それとも新しいページが必要ですか？」
   - **可能な限り既存ページへの追加・サブページとしての追加を推奨する**

3. **データソースを確認する**
   - 表示するデータがどこにあるか（ファイル、API、計算結果等）
   - 必要なサービス関数が既存にあるか確認

## フェーズ 2: 設計の提案

ユーザーに以下を提示して合意を得る:

1. **配置**: 既存ページのサブページ or 新規トップレベルページ
2. **UI 概要**: どんな見た目になるか（テーブル、カード、グラフ、タブ等）を言葉で説明
3. **使用コンポーネント**: 既存コンポーネント（`_metric_card`, `_badge`, `_empty_state`, `_data_table`）のどれを使うか
4. **htmx パターン**: 動的更新が必要か（検索、タブ切り替え、遅延ロード等）
5. **必要なファイル変更の一覧**

## フェーズ 3: 実装

### 既存ページのサブページとして追加する場合

1. **Knowledge カテゴリ追加の場合**:
   - `app/pages/knowledge.py` の `KNOWLEDGE_PAGES` に `{"type": "category", "label": ..., "icon": ..., "color": ..., "description": ...}` 形式でエントリを追加
   - 対応する `docs/{category}/` ディレクトリを作成
   - サイドバーの Knowledge サブアイテムは `knowledge_subnav`（テンプレートグローバル）経由で自動反映される

2. **既存ページにタブや機能を追加する場合**:
   - 既存の Router にエンドポイントを追加
   - 既存テンプレートを編集、または partial を追加
   - htmx で動的ロードする場合は partial エンドポイントを追加

### 新規トップレベルページの場合

1. **サービス関数を作成**（`app/services/` に追加、または既存ファイルに追加）
2. **Router を作成**（`app/pages/{page_name}.py`）
   - 既存の Router パターンに従う:
     ```python
     from app.template_env import templates
     from app.services.helpers import is_htmx, ...
     router = APIRouter()
     ```
3. **テンプレートを作成**
   - `app/templates/{page_name}/` ディレクトリ
   - full page テンプレート: `base.html` を extends
   - partial テンプレート: `app/templates/partials/` に配置
4. **`app/main.py`** に Router を登録
5. **`base.html`** のサイドバーに折りたたみナビアイテムを追加
   - FontAwesome アイコンを選択
   - `active_page` の条件分岐を追加
   - 必要に応じてサブアイテムを追加
6. **`index.html`** の Home カードグリッドにカードを追加

### スタイリングの遵守事項

- カード: `bg-white rounded-2xl shadow-sm border border-gray-200`
- ボタン (primary): `bg-emerald-500 text-white rounded-full font-bold`
- バッジ: `rounded-full bg-{color}-50 text-{color}-600 text-xs font-semibold px-3 py-1`
- アイコン背景: `rounded-xl w-{size} h-{size} bg-{color}-50 flex items-center justify-center`
- テキスト: 主 `text-gray-800`、副 `text-gray-500`、ミュート `text-gray-400`
- **絵文字は使わない**。必ず FontAwesome アイコンを使用する。

### レイアウトの注意

- サイドバー内にさらにサイドバーを入れる「2重サイドバー」は避ける
- ページ幅は内容に応じて `content_width` ブロックで調整:
  - Home / ドキュメント閲覧: `max-w-4xl mx-auto`
  - カード一覧: `max-w-5xl mx-auto`
  - テーブル・データ: `max-w-7xl mx-auto`（デフォルト）

## フェーズ 4: 動作確認

1. `just app` または `uv run uvicorn app.main:app --reload` でアプリを起動
2. ブラウザで該当ページにアクセスし、表示を確認
3. htmx の動的更新が正しく動作するか確認
4. エラーがあれば修正

## フェーズ 5: 完了報告

- 追加・変更したファイルの一覧を表示
- アクセス URL を表示
- 追加した機能の概要を説明
