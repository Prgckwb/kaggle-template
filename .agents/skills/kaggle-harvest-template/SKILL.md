---
name: kaggle:harvest-template
description: ユーザーが依頼したときだけ使う（「テンプレートに還流して」「harvest して」など）。コンペで得た汎用知見・運用の合意・テンプレート自体の誤りの訂正を、テンプレートリポジトリへ戻す PR を作る。コンペ終了時や節目向け。
argument-hint: [テンプレートリポジトリのパス（省略時は対話で確認）]
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# コンペの知見をテンプレートへ還流する

汎用知見が per-competition 層（`/kaggle:init` がリセットする）やエージェントの memory に埋もれると、
次のコンペで失われる。このスキルはそれをテンプレートへ戻す。**PR の作成までで止め、マージはユーザーが判断する。**

> ⚠ シェル変数は Bash 呼び出しをまたいで残らない。各ブロックの先頭で `TMPL` / `FORK` を置き直す。

## フェーズ 1: 収集

1. **テンプレートのパス**: $ARGUMENTS か、ユーザーに聞く。

   ```bash
   TMPL=<template-path>
   git -C "$TMPL" rev-parse --show-toplevel
   ```

2. **fork 点**: 候補を探し、**SHA をユーザーに提示して確認を取る**（誤ると差分の範囲がずれる）。

   ```bash
   git log --oneline --reverse | head -3              # clone して始めた場合の最初のコミット
   git merge-base HEAD template/main 2>/dev/null      # テンプレートを remote に持つ場合
   ```

   fork 点は `src/exp*` にコンペ固有の実験が無く、`docs/official/` がプレースホルダーのまま。
   `git show --stat <sha>` で確かめる。確信が持てなければユーザーに直接聞く。

3. **差分の範囲**:

   ```bash
   FORK=<sha>
   git diff --stat "$FORK" HEAD -- CLAUDE.md docs .claude .agents/skills tools src/utils src/exp000_sample
   git log --oneline "$FORK"..HEAD -- .agents/skills .claude | wc -l   # 0 なら還流が回っていなかった証拠として PR に書く
   ```

4. **memory**（ユーザーの働き方の合意はここにしか無いことがある）:

   ```bash
   ls ~/.claude/projects/*$(basename "$PWD")*/memory/ 2>/dev/null
   ```

   ユーザーの指示・訂正に由来するものは、テンプレートの記述と 1 件ずつ照合する。

5. **`<!-- harvest -->` マーカー**: `grep -rn "<!-- harvest -->" docs/`（`/kaggle:record-result` が付けたもの）

6. **per-competition 層に埋もれた汎用知見**:
   `head -1 docs/*.md EXP_SUMMARY.md | grep -B1 "per-competition"` の各ファイルから、汎用の記述を抜き出す

## フェーズ 2: 分類

集めた項目を **`docs/README.md` の「知見の routing」表**で分類する（分類と還流先はその表が正本）。
加えて、**テンプレート自体の誤り**（規約が実態と逆・動かないレシピ・存在しない参照先）は「矛盾の訂正」として
最優先で還流する。表にしてユーザーに確認を取る。

- 迷ったら問う:「次のコンペが別ドメインでも意味を持つか」。No ならコンペ固有で、還流しない
- 汎用に見えても、数値の閾値・ライブラリ固有の引数・ラベル名を含む文はコンペ固有。
  ただし「自分のコンペで較正し直す」という**手順**は汎用なので、閾値を例に落として手順だけ残す
- 働き方の合意は profile の `workflow` キーと 1 対 1 に対応させる。キーが無ければ、
  キーの追加（profile と `docs/ai-agent-guidelines.md` の表の両方）も PR に含める

## フェーズ 3: 還流

1. テンプレートにブランチを切る:

   ```bash
   TMPL=<template-path>
   git -C "$TMPL" status --short          # 未コミットの作業が無いこと
   git -C "$TMPL" checkout main && git -C "$TMPL" pull --ff-only
   git -C "$TMPL" checkout -b feature/$(basename "$PWD")-learnings
   ```

2. fork 点のスナップショットを読み比べ用に展開する（固定パスは併走セッションと衝突するので mktemp）:

   ```bash
   FORK=<sha>
   SRC=$(mktemp -d "${TMPDIR:-/tmp}/harvest-src.XXXXXX")
   git archive "$FORK" | tar -x -C "$SRC"
   echo "$SRC"
   ```

   終わったら `rm -rf <その実パス>`。

3. 分類に従って書き込む。規約やレシピを直したら、**それを参照している側**
   （CLAUDE.md・README.md・`.agents/skills/*/SKILL.md`）も同じ改訂で揃える。
   `.claude/agents/*.md` を変えたら `uv run python -m tools.sync_codex_agents` で `.codex/agents/` を再生成する

4. **固有名詞の除去を確認する**:

   ```bash
   TMPL=<template-path>
   grep -rniE "<コンペ略称>|<データ名>|<バケット名>|<ユーザー名>|<ラベル名>|<backbone 名>" \
     "$TMPL"/docs "$TMPL"/CLAUDE.md "$TMPL"/.agents/skills "$TMPL"/.claude "$TMPL"/src/utils || echo "クリーン"
   ```

5. per-competition のファイルは**骨格だけ**持ち込む。lifecycle マーカーの漏れを確認する:

   ```bash
   TMPL=<template-path>
   ls "$TMPL"/docs/*.md | wc -l
   head -1 "$TMPL"/docs/*.md | grep -c "lifecycle:"   # 上と一致すること
   ```

6. コミット前に任意で整形する（自動チェックは無い）。実験パイプラインに触れたら
   `src/exp000_sample` を `run_mode=debug` で 1 回通す:

   ```bash
   TMPL=<template-path>
   uv run --directory "$TMPL" --with ruff ruff check --fix src/ tools/ .claude/hooks/
   uv run --directory "$TMPL" --with ruff ruff format src/ tools/ .claude/hooks/
   ```

7. 分類ごとに 1 コミット（矛盾の訂正 → 汎用の方法論 → 運用の合意の順、gitmoji + 日本語）。
   `git add` は**パスを明示する**:

   ```bash
   TMPL=<template-path>
   git -C "$TMPL" status --short
   git -C "$TMPL" add <path> <path> ...
   git -C "$TMPL" commit -m "🔧 ..."
   ```

8. PR を作る。本文に分類の根拠（なぜ汎用でなぜ固有でないか）を書く:

   ```bash
   TMPL=<template-path>
   REPO=$(cd "$TMPL" && gh repo view --json nameWithOwner -q .nameWithOwner)
   echo "PR 先: $REPO"                      # 期待どおりか目で確認する
   git -C "$TMPL" push -u origin HEAD
   gh pr create --repo "$REPO" --title "..." --body "..."
   ```

## フェーズ 4: 報告

分類ごとの項目数、**還流しなかった項目の一覧と理由**、固有名詞 grep の結果、PR の URL。
次のコンペでは `/kaggle:init` が `workflow` を対話で埋めるので、働き方の指示を口頭で出し直す必要はないと伝える。
