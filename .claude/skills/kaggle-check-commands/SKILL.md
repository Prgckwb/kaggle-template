---
name: kaggle:check-commands
description: Hydra 実験コマンドの構築を支援する。やりたいことを伝えると、正しいコマンドを出力する。
argument-hint: [やりたいこと（例: デバッグ実行、推論、パラメータ変更）]
disable-model-invocation: true
allowed-tools: Bash, Read, Glob
---

# 実験コマンドを確認する

ユーザーがやりたいことをヒアリングし、正しいコマンドを出力する。
コマンドを実行するのではなく、コマンド文字列を提示するだけ。

## 手順

### 1. ユーザーの意図を確認

$ARGUMENTS があればそこから意図を読み取る。なければ質問する:

- 「何をしたいですか？」
  - 学習（デバッグ / 本番）
  - 推論
  - パラメータのオーバーライド
  - config の確認
  - その他

### 2. 対象実験を特定

- `src/exp*/` を Glob で検索し、実験一覧を把握
- ユーザーに対象実験を確認（1つしかなければ自動選択）

### 3. config を確認

- `src/{exp-name}/config/config.yaml` を Read して構造を把握
- `src/{exp-name}/config/run*.yaml` を Glob で検索し、小実験 config の一覧を把握
- Hydra の defaults リスト、パラメータ階層を確認

### 4. run を特定

- 小実験 config が存在する場合、ユーザーに「どの run を実行しますか？」と確認
  - ベース config（config.yaml）で実行する場合は `--config-name` 不要
  - 小実験を指定する場合は `--config-name={run_name}` を付与

### 5. コマンドを生成・提示

以下のパターンに基づいてコマンドを生成する:

**基本コマンド（ベース config）:**

```bash
# デバッグモードで学習
uv run python -m src.{exp-name}.train run_mode=debug

# fold0 で学習（デフォルト）
uv run python -m src.{exp-name}.train

# 全 fold で学習
uv run python -m src.{exp-name}.train run_mode=full

# 推論
uv run python -m src.{exp-name}.inference
```

**小実験を指定する場合:**

```bash
# 小実験をデバッグモードで学習
uv run python -m src.{exp-name}.train --config-name={run_name} run_mode=debug

# 小実験を fold0 で学習
uv run python -m src.{exp-name}.train --config-name={run_name}

# 小実験を全 fold で学習
uv run python -m src.{exp-name}.train --config-name={run_name} run_mode=full
```

**Hydra オーバーライド:**

```bash
# パラメータ変更
uv run python -m src.{exp-name}.train training.lr=5e-4

# config 表示（実行せず）
uv run python -m src.{exp-name}.train --cfg job

# multirun
uv run python -m src.{exp-name}.train -m training.lr=1e-3,5e-4,1e-4
```

**その他:**

```bash
just app    # Web アプリ起動
```

- 各オーバーライドが config のどのパラメータに対応するか簡潔に説明
- 注意点があれば添える（例: debug モードでは wandb が無効化される等）

**注意**: コマンドを実行するかどうかはユーザーに委ねる。このスキルはコマンドの提示のみを行う。
