---
name: kaggle:past-solutions
description: 新しいコンペの開始時や「過去の似たコンペの上位解法を調べて」と頼まれたときに使う。類似する過去コンペの上位 Writeup を集めて要約し、docs/insights/past_solutions_{slug}.md に保存する。
argument-hint: [対象コンペの slug（例: playground-series-s5e1）。省略時は profile から取る]
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch
---

# 類似過去コンペの上位解法を集める

情報源の使い分け（ai-agent-guidelines.md と同じ方針）:

- **コンペのメタデータと検索**: `kaggle` CLI を優先する（`uv run kaggle competitions list -s <keyword>` など）
- **Writeup / Discussion の本文**: Kaggle MCP を使う（`list_forum_topics` / `get_writeup_by_topic` / `get_forum_topic` / `get_resolved_writeup_links`）
  - `kaggle` CLI と `kagglesdk` には forum や writeup を取得する機能がないため
- **どちらも使えないとき**: WebFetch を使う（`https://www.kaggle.com/competitions/{slug}/discussion/...`）。保存時に「自動抽出のため不正確な可能性あり」と注記する

このスキルは読み取り専用。提出系・アップロード系の API は呼ばない。

## 前提チェック

- MCP を使う前に `mcp__kaggle__*` ツールが見えているか確認する
  - 見えていない、または `authenticate` しか無い場合は、ユーザーに `/mcp` → `kaggle` で認証してもらう
  - 認証できなければ WebFetch に切り替える
- 過去解法は参考情報であり、「この手法が効く」という結論ではない（CLAUDE.md「探索の独立性」）

## フェーズ 1: 対象コンペの特定

1. slug を決める。優先順は `$ARGUMENTS` → `docs/competition-profile.yaml` の `competition.slug` → ユーザーに確認
2. 評価指標・タスク種別・データ種別を、profile と `docs/official/` から把握する。足りない分は `mcp__kaggle__get_competition` で補う
3. 類似の基準をユーザーと合意する
   - 指標一致・タスク一致・データ種別一致のどれを優先するか
   - 各コンペから何件拾うか（既定は Top 3、最大 5）

## フェーズ 2: 類似過去コンペの抽出

1. 終了済みのコンペを候補にする。検索クエリは「指標 + タスク + データ種別」の組み合わせ
   - CLI: `uv run kaggle competitions list -s "<query>"`
   - 足りなければ `mcp__kaggle__search_competitions`
2. 3〜5 件に絞ってユーザーに提示し、追加や除外の希望を確認する

## フェーズ 3: 上位解法の取得

各コンペについて次を行う。

1. forum を特定する（`get_competition` の応答、または `list_forums`）
2. `list_forum_topics` で "1st place" / "solution" / "winner" 等を含むトピックを探す。順位の明記と upvote を見て、本物の上位解法か判断する
3. 本文を取得する。`get_writeup_by_topic` を試し、失敗したら `get_forum_topic(includeComments=true)` を使う
4. 本文中のリンクを `get_resolved_writeup_links` で解決し、データセット・notebook・外部リンクに分類する
5. 取れなかったコンペは無理に埋めず、「収集失敗（理由）」と記録して次へ進む

## フェーズ 4: 出力

保存先は `docs/insights/past_solutions_{slug}.md`。既にある場合は、上書き・追記・中止のどれにするかをユーザーに確認する。

```markdown
# Past Solutions: {コンペ名}

- 調査日: {YYYY-MM-DD} / 対象: [{slug}](https://www.kaggle.com/competitions/{slug})
- 評価指標: {metric} / タスク: {task} / データ: {data}
- 類似基準: {合意した基準}
- 取得経路: CLI（検索）/ MCP（コンペ A, B の writeup）/ WebFetch（コンペ C）
- 収集失敗: {n}/{m} コンペ（理由）

## 類似コンペ 1: {名前}（{URL}、{期間}、{チーム数}）

### {順位} place — {著者}（{リンク}）
- 要約: 手法の核を 3〜5 行で（自分の言葉で書く。本文のコピペはしない）
- モデル / 前処理 / 後処理・アンサンブル / CV 戦略
- 参照リソース: データセット・notebook・外部リンク

## 全体所感
- 複数の解法で共通して効いていた手法
- 本コンペでの適用条件（データ特性が合うかどうか）と、効かない可能性
```

## フェーズ 5: 完了報告

- 生成したファイルのパスと、収集できた件数（n コンペ × m 件）
- 次の一手として次のどちらかを案内する
  - `/kaggle:review-strategy`: 探索マップに候補を載せる
  - `/kaggle:new-experiment`: 初回の実験を設計する
