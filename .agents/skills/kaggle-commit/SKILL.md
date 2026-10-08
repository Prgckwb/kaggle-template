---
name: kaggle:commit
description: ユーザーがコミットやプッシュを頼んだときだけ使う（「コミットして」「push して」など）。変更を論理単位に分け、gitmoji + 日本語でパスを明示してコミットする。
argument-hint: [コミットの概要（省略可）]
allowed-tools: Bash, Read, Glob, Grep
---

# 変更を論理単位でコミットし、プッシュする

規約（gitmoji + 日本語、1 コミット = 1 つの論理的な変更、ブランチ運用）は CLAUDE.md の「Git 規則」が正本。
git の危険操作は `.claude/hooks/guard.py` が止める（規則は同ファイルの docstring に書いてある）。

- amend ではなく新しいコミットを作る。`--no-verify` / `--force` は使わない
- **`git add` は常にパスを明示する**（`-A` / `.` / `-u` / `commit -a` は使わない）

## gitmoji

| gitmoji | 用途 | 例 |
|---|---|---|
| 🧪 | 実験の追加・変更 | `🧪 exp001_baseline を追加` |
| 🐛 | バグ修正 | `🐛 データローダーの index エラーを修正` |
| ✨ | 新機能 | `✨ OOF 誤差分析ツールを追加` |
| ♻️ | リファクタリング | `♻️ fold 生成を src/utils/cv.py に集約` |
| 📝 | ドキュメント | `📝 exp003 の考察を追記` |
| 🔧 | 設定 | `🔧 run002-lr3e4 の config を追加` |
| 🗑️ | 削除 | `🗑️ 使われていないユーティリティを削除` |
| ⬆️ | 依存の更新 | `⬆️ lightning を 2.x に更新` |
| 📓 | notebook | `📓 exp005 の提出 notebook を追加` |
| 🔀 | マージ | `🔀 feature/xxx を main にマージ` |

## フェーズ 1: 変更の把握

1. `git status` と `git diff` / `git diff --cached` で差分を把握する。変更が無ければそう伝えて終了する
2. **持ち主の確認**: `docs/competition-profile.yaml` の `workflow.concurrent_sessions` が `true` なら、
   未コミットの変更が自分のものとは限らない。このセッションで触っていないファイルはコミット案から外し、ユーザーに確認する。
   - 共有ファイル（`EXP_SUMMARY.md` / `docs/guardrails.md` / `docs/submissions.md` / `docs/SESSION_NOTES.md` 等）は
     `git diff <file>` で追加された節を見て、他セッションの追記が混ざっていないか確かめる。
     混ざっていたら 1 コミットにまとめ、メッセージに両方の由来を書く
3. **除外・警告するもの**:
   - シークレット（`.env`, `credentials.json`, `*.pem`, `*.key`, `kaggle.json`）は警告して除外する
   - `src/*/output/`・`src/*/logs/`・`input/`・`sandbox/` 配下と ckpt 類は警告する（gitignore されているはず）
4. **notebook の出力除去**: ステージ対象に `*.ipynb` があれば、コミット前に
   `uv run --with nbstripout nbstripout <path>` を実行して出力を消す（自動では走らない）

## フェーズ 2: 論理グループへの分類

- 同じ目的の変更はまとめる（例: 実験追加 → config + train.py + model.py + README）
- 目的の違う変更は分ける（バグ修正とリファクタリング、ドキュメントとコードは別にする）
- 削除は独立したコミットにすることが多い
- `$ARGUMENTS` があれば意図として分類に反映する

各グループについて、対象ファイル・gitmoji・メッセージ（何を・なぜ）を決める。

## フェーズ 3: ユーザー確認

```
コミット 1: 🧪 exp001_baseline を追加
  - src/exp001_baseline/train.py (new)
  - src/exp001_baseline/config/config.yaml (new)
コミット 2: 📝 EXP_SUMMARY を更新
  - EXP_SUMMARY.md (modified)
```

統合・分割・メッセージ修正・順序変更・除外をユーザーが調整できるようにし、**承認を得てから**実行する。

## フェーズ 4: コミットとプッシュ

グループごとに `git add <パスを列挙>` → `git commit -m "{gitmoji} {message}"`。
全部終わったら `git push`（上流が無ければ `-u` を付ける）。

## フェーズ 5: 完了報告

- 作成したコミット（短いハッシュ + メッセージ）、push 先のブランチ
- push に失敗したら原因と対処を説明する（force push は提案しない）
