---
name: kaggle:harvest-template
description: コンペで得た汎用知見をテンプレートリポジトリへ還流する PR を作る。コンペ終了時や節目に実行する。
argument-hint: [テンプレートリポジトリのパス（省略時は対話で確認）]
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# コンペの知見をテンプレートへ還流する

コンペで確立した働き方・実験方法論・規約を、テンプレートリポジトリへ戻して PR を作る。

**なぜこのスキルが必要か**: あるコンペで 200 コミット超・2 ヶ月分の知見を蓄積したが、
テンプレートは fork 時点から一度も更新されなかった。原因は
「この学びは汎用か固有か」を判定して振り分ける工程がどのスキルにも無かったこと。
その結果、汎用の実験方法論が `/kaggle:init` がリセットする層（`docs/guardrails.md`）に埋もれ、
ユーザーの働き方の合意はエージェントの memory にしか残らなかった。

**このスキルは PR の作成までで止める。マージはユーザーが判断する。**

## フェーズ 1: 対象の特定

> ⚠ **シェル変数は Bash 呼び出しをまたいで残らない**（1 コマンド = 1 プロセス）。
> このスキルの各コードブロックは**自己完結**にしてある。`TMPL` と `FORK` は
> ブロックごとに先頭で置き直すこと（値は下の 0. と 1. で確定させ、以降は同じ値を書く）。

0. **テンプレートのパスを確定する**（以降の全ブロックで使う）

   ```bash
   TMPL=<template-path>       # $ARGUMENTS があればそれを使う。無ければユーザーに聞く
   git -C "$TMPL" rev-parse --show-toplevel   # 実在する git リポジトリであることを確認
   ```

1. **fork 点を特定する**

   テンプレートから複製した時点のコミットを探す。次の順に試し、**得られた SHA を
   ユーザーに提示して確認を取る**（誤ると差分の範囲が丸ごとずれる）:

   ```bash
   TMPL=<template-path>       # 0. で確定した値

   # (a) テンプレートを clone して作業を始めた場合: 最初のコミット
   git log --oneline --reverse | head -3

   # (b) テンプレートを remote として持っている場合: 分岐点
   git remote -v
   git merge-base HEAD template/main 2>/dev/null

   # (c) テンプレート側の最新コミットが履歴に含まれている場合:
   #     テンプレートの HEAD と同じ tree を持つコミットを探す
   git -C "$TMPL" log --oneline -5
   git log --oneline --all | head -30
   ```

   判定の目安: fork 点のコミットは `src/exp*` にコンペ固有の実験が無く、
   `docs/official/` がプレースホルダーのままである。
   `git show --stat <sha>` で確認できる。**確認が取れない場合はユーザーに直接聞く。**

2. **差分の範囲を確認する**

   ```bash
   FORK=<sha>                 # 1. で確定し、ユーザーの確認を取った SHA
   git diff --stat "$FORK" HEAD -- CLAUDE.md docs .claude tools src/utils tests
   git log --oneline "$FORK"..HEAD -- .claude | wc -l   # スキルが更新されたか
   ```

   `.claude` の変更が 0 件なら、それ自体が「還流の工程が動いていなかった」証拠として
   PR 本文に書く。

3. **memory も走査対象にする**（最重要。ユーザーの働き方の合意はここにしか無いことがある）

   ```bash
   ls ~/.claude/projects/*$(basename "$PWD")*/memory/ 2>/dev/null
   ```

   ユーザーの指示・訂正に由来する memory は**ほぼすべて還流候補**（③に分類される）。
   テンプレートの記述と矛盾していないかを 1 件ずつ照合する。

4. **`<!-- harvest -->` マーカーを回収する**

   ```bash
   grep -rn "<!-- harvest -->" docs/
   ```

   `/kaggle:record-result` の「知見の routing」で②に分類された箇所。

5. **per-competition 層に埋もれた汎用知見を拾う**

   ```bash
   head -1 docs/*.md | grep -B1 "per-competition"
   ```

   `docs/guardrails.md` / `docs/training-conventions.md` 等の中で、
   フェーズ 2 の判定基準に照らして②に当たる記述を抜き出す
   （**この層は `/kaggle:init` がリセットするので、還流しないと消える**）。

## フェーズ 2: 4 分類

収集した項目を分類し、**表にしてユーザーに提示して確認を取る**。分類を誤ると、
コンペ固有の制約が次のコンペのテンプレートに紛れ込む（②③の取りこぼしより悪い）。

| 分類 | 判定基準 | 還流先 |
|---|---|---|
| ① 矛盾の訂正 | テンプレートの記述が実運用と食い違っていた（規約が実態と逆、動かないレシピ、参照先の不在） | 該当ファイルを直接修正 |
| ② 汎用の方法論 | **コンペのドメイン・データ形式・評価指標に依存しない**判定作法・運用手順 | `docs/experiment-methodology.md` / `docs/remote-training-ops.md`（invariant） |
| ③ 働き方の合意 | ユーザーが指示した既定の振る舞い（run mode・提出主体・ブランチ運用・併走） | `docs/ai-agent-guidelines.md`「運用の合意」+ `docs/competition-profile.yaml` の `workflow` |
| ④ コンペ固有 | ドメイン知識・ラベル定義・データの癖・固有名詞・そのコンペで得た閾値 | **還流しない**（骨格だけを per-competition テンプレへ） |

**判定基準の運用**:

- ②④ の切り分けで迷ったら問う: **「次のコンペが全く別のドメイン（表形式・NLP・時系列）でも、
  この文は意味を持つか」**。No なら④
- ②に見えても**数値の閾値・特定ライブラリの引数・ラベル名を含む文は④**。
  ただし「同じ手順で自分のコンペで較正し直す」という**手順**は②なので、
  閾値を例（「あるコンペでの実測例」）に落として手順だけを残す
- ①は最優先で還流する（テンプレートが間違っている状態は次のコンペで同じ事故を再生産する）
- ③は必ず `workflow` のキーと 1 対 1 に対応させる。対応するキーが無ければ
  **キーの追加も PR に含める**（`docs/competition-profile.yaml` と
  `docs/ai-agent-guidelines.md` の表の両方）

## フェーズ 3: 還流

> ⚠ 各ブロックは自己完結。`TMPL`（フェーズ 1 の 0.）と `FORK`（フェーズ 1 の 1.）は
> ブロックの先頭で置き直す。

1. テンプレートにブランチを切る:

   ```bash
   TMPL=<template-path>
   git -C "$TMPL" status --short      # 未コミットの作業がないことを確認
   git -C "$TMPL" checkout main && git -C "$TMPL" pull --ff-only
   git -C "$TMPL" checkout -b feature/$(basename "$PWD")-learnings
   ```

2. fork 点のスナップショットを展開して参照元にする（何を足したかを差分で見るため）:

   ```bash
   FORK=<sha>
   # 固定パスは併走セッションと衝突する（相手の展開先を rm -rf しかねない）ので mktemp を使う。
   # パスは次のブロックで使うので、標準出力に出したうえでメモしておく
   SRC=$(mktemp -d -t harvest-src)
   git archive "$FORK" | tar -x -C "$SRC"
   echo "fork 点のスナップショット: $SRC"
   ```

   使い終わったら `rm -rf "$SRC"` で片付ける（`$SRC` は `mktemp` が返した実パスに置き換える）。

3. **固有名詞の除去を検証する**。コンペ略称・データセット名・バケット名・ユーザー名・
   ラベル名・ドメイン用語・backbone 名を列挙して grep する:

   ```bash
   TMPL=<template-path>
   grep -rniE "<コンペ略称>|<データ名>|<バケット名>|<ユーザー名>|<ラベル名>|<backbone 名>" \
     "$TMPL"/docs/experiment-methodology.md "$TMPL"/docs/remote-training-ops.md \
     "$TMPL"/docs/ai-agent-guidelines.md "$TMPL"/CLAUDE.md "$TMPL"/.claude \
     || echo "クリーン"
   ```

   実測値を引くときは「あるコンペでの実測例」と匿名化する。

4. `per-competition` のファイルは**骨格だけ**還流する（中身は持ち込まない）。
   `lifecycle` マーカーが全ファイルにあることを確認する:

   ```bash
   TMPL=<template-path>
   ls "$TMPL"/docs/*.md | wc -l
   head -1 "$TMPL"/docs/*.md | grep -c "lifecycle:"   # 上と一致すること
   ```

5. **コミットの前に**品質チェックを通す（`make fix` は formatter がファイルを書き換えるので、
   コミット後に走らせるとその変更がコミットに入らない）:

   ```bash
   TMPL=<template-path>
   make -C "$TMPL" fix && make -C "$TMPL" lint \
     && make -C "$TMPL" test && make -C "$TMPL" typecheck
   ```

   `make typecheck` は既存の diagnostics 件数を**増やしていない**ことだけを見る（0 件が条件ではない）。

6. **分類ごとに 1 コミット**にする（gitmoji + 日本語）。順序は①→②→③。
   `git add` は**常にパスを明示する**（`git add -A` / `git commit -a` は使わない。
   併走セッションの未コミット作業を巻き込むため、テンプレート側の hook も拒否する）。

   ```bash
   TMPL=<template-path>
   git -C "$TMPL" status --short          # make fix の書き換えも含まれていることを確認
   git -C "$TMPL" add <path> <path> ...
   git -C "$TMPL" commit -m "🔧 ..."
   ```

7. PR を作る。本文には**分類の根拠**（なぜ②で、なぜ④でないか）と、
   閉じられた Open Question を書く。`--repo` はプレースホルダのままにせず、
   テンプレートの origin から解決する:

   ```bash
   TMPL=<template-path>
   # origin の URL から owner/repo を取り出す（SSH 形式・HTTPS 形式の両方に対応）。
   # ⚠ 末尾の .git を先に落としてから最後の 2 要素を取る。1 本の式で `[^/]+?` と
   #    書くと BSD sed（macOS 既定）が "repetition-operator operand invalid" で落ちる
   REPO=$(git -C "$TMPL" remote get-url origin \
          | sed -E 's#\.git$##' | sed -E 's#^.*[:/]([^/]+/[^/]+)$#\1#')
   echo "PR 先: $REPO"                      # 期待どおりか目で確認する
   #                                        （origin がローカルパスだと owner が別物になる）
   git -C "$TMPL" push -u origin HEAD
   gh pr create --repo "$REPO" --title "..." --body "..."
   ```

   `--repo` を省いて `gh` の cwd 解決に任せる形でもよいが、その場合は
   **cwd がテンプレート側であること**を確認する（コンペ側リポジトリに PR を出してしまう）。

   **PR の作成までで止める。マージはユーザーが判断する。**

## フェーズ 4: 完了報告

- 分類ごとの項目数と、**還流しなかった（④に分類した）項目の一覧**（判定の根拠つき）
- テンプレート側で閉じた Open Question
- 固有名詞 grep の結果（「クリーン」であること）
- PR の URL
- **次のコンペで最初にやること**: `/kaggle:init` が `workflow` を対話で埋めるので、
  働き方の指示を口頭で出し直す必要はないことを伝える
