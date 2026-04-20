---
name: kaggle:past-solutions
description: Kaggle MCP 経由で類似過去コンペの上位解法 Writeup を収集し、docs/insights/past_solutions_{slug}.md に保存する。新コンペ開始時の初期仮説づくりに使う。
argument-hint: [対象コンペの slug（例: playground-series-s5e1）。省略時は docs/official/ から推定]
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch
---

# 類似過去コンペの Writeup を収集する

このスキルは Kaggle 公式 MCP サーバー (`https://www.kaggle.com/mcp`) を使い、対象コンペに似た過去コンペの上位解法を集めて `docs/insights/past_solutions_{target_slug}.md` に保存する。

ユーザーと対話しながら進める。MCP の検索結果は LLM が要約して保存するが、要約の方向性（重視ポイント）はユーザーに確認する。

## 前提チェック

1. **MCP 接続確認**
   - `claude mcp list | grep kaggle` で `✓ Connected` を確認
   - 未接続なら以下を案内して終了:
     - `claude mcp add --transport http kaggle https://www.kaggle.com/mcp`
     - 起動後 `/mcp` で `kaggle` を選択し、ブラウザ認証を Approve

2. **Kaggle MCP ツールが利用可能かを確認**
   - `mcp__kaggle__*` プレフィックスのツールがツールリストにあるはず
   - なければユーザーに `/mcp` で再認証を依頼

## フェーズ 1: 対象コンペの特定

1. **$ARGUMENTS から slug を取得**
   - 引数があれば slug として使用
   - なければ `docs/official/` 配下を Read してコンペ slug の手がかりを探す
   - それでも不明ならユーザーに確認:
     - 「対象コンペの slug を教えてください（例: `titanic`、`playground-series-s5e1`）」

2. **対象コンペのメタデータを取得**
   - `mcp__kaggle__get_competition(competitionName=slug)` で取得
   - 以下を記録: 公式名、評価指標、タスク種別、データ種別、開催期間、参加者数

3. **類似基準をユーザーと合意**
   - 評価指標一致を最優先するか / タスク種別一致を優先するか / データ種別（画像・テーブル・テキスト・音声等）一致を優先するか
   - 出力に含めたい解法の数（デフォルト: 各コンペ Top 3、最大 5 件）

## フェーズ 2: 類似過去コンペの抽出

1. **`mcp__kaggle__search_competitions` で候補列挙**
   - 検索クエリは「評価指標名 + タスクキーワード + データ種別」を組み合わせる
   - 例: target が `RMSE` × `tabular regression` なら `"tabular regression rmse"`
   - **完了済み (closed)** のコンペに限定する（解法が公開されているもの）

2. **候補の絞り込み**
   - 取得結果から 3〜5 件を選定
   - ユーザーに候補リストを提示し、「この 3 件で進めますか？追加・除外したいものはありますか？」と確認

## フェーズ 3: 上位解法 Writeup の取得

各類似コンペについて以下を実行:

1. **コンペの forum を特定**
   - `mcp__kaggle__list_forums` または `get_competition` の応答から `forum_id` を取得

2. **上位解法トピックを検索**
   - `mcp__kaggle__list_forum_topics(forum_id=..., query="1st place|2nd place|3rd place|solution|winner")`
   - タイトルに "1st"/"2nd"/"3rd"/"place"/"solution" を含むトピックを抽出
   - upvote 数や順位の明記を見て、本物の上位解法かを判定

3. **Writeup 本文を取得**
   - 各トピックに対し `mcp__kaggle__get_writeup_by_topic(topic_id=...)` で本文取得
   - 取得失敗時は `mcp__kaggle__get_forum_topic(topic_id=..., includeComments=true)` でフォーラム本文をフォールバックで取得

4. **参照リンク解決**
   - `mcp__kaggle__get_resolved_writeup_links(...)` で writeup 内のリンクを解決
   - データセット・ノートブック・YouTube・外部 URL を分類して保持

## フェーズ 4: 出力ファイルの生成

1. **保存先**: `docs/insights/past_solutions_{target_slug}.md`
2. **既存ファイルがある場合**: ユーザーに上書き or 追記 or 中止を確認
3. **フォーマット**（必ずこの構造で書く）:

```markdown
# Past Solutions: {target_competition_name}

- 調査日: {YYYY-MM-DD}
- 対象コンペ: [{slug}](https://www.kaggle.com/competitions/{slug})
- 評価指標: {metric}
- タスク種別: {task_type}
- データ種別: {data_type}
- 類似基準: {ユーザーと合意した基準}

---

## 類似コンペ 1: {comp_name}

- URL: https://www.kaggle.com/competitions/{slug}
- 評価指標: {metric}
- 開催期間: {YYYY-MM} 〜 {YYYY-MM}
- 参加チーム数: {n}

### 1st place solution

- 著者: {user}（@{username}）
- リンク: {forum_topic_url}

**要約**

（3〜5 行で手法の核を要約。LLM の地の言葉で書く）

**採用手法**

- モデル: {model_arch}
- 前処理: {key_preprocessing}
- 後処理 / アンサンブル: {ensemble_strategy}
- CV 戦略: {cv_strategy}

**参照リソース**

- データセット: {resolved_dataset_links}
- ノートブック: {resolved_notebook_links}
- 外部リンク: {resolved_external_links}

### 2nd place solution

（同上）

### 3rd place solution

（同上）

---

## 類似コンペ 2: ...

---

## 全体所感（LLM の地の言葉）

- 共通して効いていた手法: ...
- 本コンペで試す価値が高そうなもの: ...
- 注意点・本コンペでは効かない可能性があるもの: ...
```

4. **書き込み後の確認**
   - 生成したファイルパスを表示
   - ファイル冒頭 30 行を Read して整形確認

## フェーズ 5: 完了報告

- 生成ファイルの相対パス（`docs/insights/past_solutions_{slug}.md`）
- 収集できた解法数（n コンペ × 各 m 件）
- ダッシュボードでの閲覧パス（`http://localhost:8000/knowledge/insights/past_solutions_{slug}.md`）
- 次のステップの提案: 「この知見を元に `kaggle:new-experiment` で初回実験を設計しますか？」

## フォールバック: kagglesdk（MCP が使えないとき）

MCP ツール呼び出しが失敗（接続切れ・認証切れ・タイムアウト・該当ツール未提供）した場合、Kaggle 公式 Python SDK (`kagglesdk`) にフォールバックする。`kaggle` パッケージは `pyproject.toml` の `dev` グループに既に入っているので追加インストール不要。

### 前提

- `~/.kaggle/kaggle.json`（API トークン）が設置済みであること（未設定なら https://www.kaggle.com/settings → API → Create New Token）

### MCP → kagglesdk 対応マップ

`uv run python -c "..."` で `KaggleClient` を呼ぶ。サービスは **`c.competitions.competition_api_client` / `c.datasets.dataset_api_client` / `c.models.model_api_client` / `c.kernels.kernels_api_client` / `c.benchmarks.benchmarks_api_client` / `c.search.search_api_client`** に分かれる。

| MCP ツール | kagglesdk 対応メソッド |
|---|---|
| `get_competition` | `competitions.competition_api_client.get_competition(...)` |
| `search_competitions` | `competitions.competition_api_client.list_competitions(...)` |
| `get_competition_data_files_summary` / `list_competition_data_files` | 同名メソッドあり |
| `download_competition_data_file(s)` | `download_data_file` / `download_data_files` |
| `get_competition_leaderboard` / `download_competition_leaderboard` | `get_leaderboard` / `download_leaderboard` |
| `submit_to_competition` / `create_code_competition_submission` | `create_submission` / `create_code_submission` |
| `search_datasets` / `download_dataset` / `get_dataset_*` | `datasets.dataset_api_client.list_datasets` / `download_dataset` / `get_dataset*` |
| `list_models` / `get_model_variation*` / `download_model_variation_version` | `models.model_api_client.list_models` / `get_model_instance*` / `download_model_instance_version` |
| ノートブック系 (`*_notebook_*`) | `kernels.kernels_api_client.*_kernel_*`（notebook=kernel と読み替え） |
| `get_benchmark_leaderboard` | `benchmarks.benchmarks_api_client.get_benchmark_leaderboard` |
| `search_content` | `search.search_api_client.list_entities` |

### kagglesdk でも取れないもの（forum / writeup / discussion 系）

`list_forums`, `list_forum_topics`, `get_forum_topic`, `get_writeup_*`, `get_resolved_writeup_links`, `list_hackathon_write_ups` などは **kagglesdk に対応サービスがない**。この場合の優先順位:

1. **WebFetch を最後の手段として使う**:
   - Discussion 一覧: `https://www.kaggle.com/competitions/{slug}/discussion`
   - 個別 topic: `https://www.kaggle.com/competitions/{slug}/discussion/{topic_id}`
   - 取得結果は「自動抽出のため不正確の可能性あり」と markdown に注記する
2. **取れなかったコンペは飛ばす**: 最終 markdown 冒頭に「収集失敗: N/M コンペ（理由）」を明記

### ad-hoc 実行例

```bash
uv run python - <<'PY'
from kagglesdk import KaggleClient
with KaggleClient() as c:
    comp = c.competitions.competition_api_client.get_competition(
        # GetCompetitionRequest 等の引数型は SDK ヘルプ参照
    )
    print(comp)
PY
```

引数の型・必須フィールドは `help(method)` または `KaggleClient` の各 `*_api_client` のソース (`uv run python -c "import inspect, kagglesdk; print(inspect.getsourcefile(kagglesdk.KaggleClient))"` で場所を特定) で確認する。

### ハンドリング方針

1. **まず MCP を試す**。エラー時のみフォールバック
2. フォールバック発動を markdown 冒頭の「調査メモ」欄に記録（例: `- 取得経路: MCP（コンペ A, B） / kagglesdk（コンペ C） / WebFetch（コンペ D の writeup）`）
3. すべての経路で失敗した場合は **黙ってスキップせず**、その旨を明記する

## 注意事項

- **書き込み系 MCP ツール（`submit_to_competition`, `upload_dataset_file` 等）は呼ばない**: 本スキルは読み取り専用
- **CLAUDE.md の「探索の独立性」**: 過去解法はあくまで参考。「この手法が必ず効く」ではなく「こういう選択肢がある」として記述する
- **Writeup の生コピペ禁止**: 必ず LLM の地の言葉で要約する（著作権 / 文脈の維持のため）
- **取得に失敗したコンペは無理に埋めない**: 該当解法なしと明記して次へ
