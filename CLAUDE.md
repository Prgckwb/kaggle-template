# CLAUDE.md

AI エージェントがこのリポジトリで作業する際のガイドライン。

## プロジェクト概要

Kaggle コンペティション用テンプレート。Hydra + Wandb で実験管理、FastAPI + htmx でダッシュボード。

## ディレクトリ構成

```
kaggle-template/
├── input/          # データ格納（gitignore）
├── output/         # 出力格納（gitignore）
├── sandbox/        # AI Agent 検証用（gitignore）
├── notebook/       # Jupyter Notebook（公開Code、検証用）
├── app/            # Web アプリ（FastAPI + htmx）
├── docs/
│   ├── official/   # Kaggle 公式情報
│   ├── discussion/ # Discussion 情報（YYYY-MM-DD_topic.md）
│   └── insights/   # 実験知見（YYYY-MM-DD_topic.md）
└── src/            # 実験ディレクトリ
    └── exp000-sample/
```

## 技術スタック

- **パッケージ管理**: uv
- **実験管理**: Hydra, Wandb
- **モデル学習**: PyTorch Lightning（最新版）、wandb logger、rich progress
  - Trainer 内蔵ライブラリ（transformers 等）はその Trainer 利用も検討
  - MPS / CUDA / CPU を想定（`pin_memory` は GPU 時のみ有効化、`accelerator="auto"` を使用）
- **Web アプリ**: FastAPI, htmx, Jinja2

## TDD 適用除外

このプロジェクトでは TDD は適用しない。`debug: true` でパイプライン全体の動作確認を行うことで代替する。

## 実験ディレクトリの規則

### 命名・構成

`exp{番号}-{subtitle}` 形式。各実験は独立し、他の実験に依存しない。共通コードが必要な場合はコピーする。

```
src/exp001-xxx/
├── README.md       # 目的・仮説・結果・考察
├── train.py        # 学習スクリプト
├── inference.py    # 推論スクリプト
├── model.py        # モデル定義
├── data.py         # データ処理
└── config/
    └── config.yaml
```

### 推論スクリプト

各実験ディレクトリに `inference.py` を作成する:

- チェックポイント自動検索（`best-*.ckpt` パターン）
- 全 fold の softmax 確率平均によるアンサンブル
- OOF 予測の保存: `oof_predictions.csv`（image_id, fold, true_label, pred_label, prob_0〜prob_N）
- TTA が必要な場合は `inference_tta.py` を追加

### デバッグモード

`config.yaml` の `debug: true` でデータ・エポック・fold 数を制限し、wandb を無効化する。まずデバッグモードでパイプライン全体が通ることを確認してから `debug=false` で本番実行する。

### wandb ログの統一

評価指標の wandb log は実験を跨いで比較するため、同じキー名を使い続ける。表記揺れ（`acc` vs `accuracy`、`valid` vs `val`）を避ける。メトリクス名はプロジェクト初回の実験で決定し、以降変更しない。

### 再現性

シード固定（random, numpy, torch）、シード値は `config.yaml` に記録、環境は `uv.lock` で管理。

### 実験後の更新（必須）

1. **各実験の README.md**: 目的・仮説（開始時）、結果・考察（完了時）
2. **ルート README.md**: Experiments テーブルと Experiment Tree を更新
3. **docs/insights/**: `YYYY-MM-DD_exp{番号}-{subtitle}.md` で知見を記録

**exp000 はサンプル実験のため、exp001 以降が作成された後は README.md の Experiments テーブルおよび Experiment Tree に載せない。**

## 探索の独立性（AI エージェントへの注意）

LLM は過去の実験結果に引きずられ、探索空間を狭めてしまう傾向がある。

**引き継いでよいもの（コードレベルの知見のみ）:**
- データ前処理・特徴量生成の実装上の工夫
- バグ修正・速度改善の技術的発見
- `docs/insights/` に記録された実装知見

**引き継いではいけないもの:**
- 「このアプローチはうまくいかない」という結論
- 特定の手法やモデルへの偏り・先入観
- 探索範囲の絞り込み

**新しい実験では:** 問題の本質・データの特性・ドメイン知識から仮説をゼロベースで立てる。

## sandbox

AI Agent が検証用スクリプトを実行するディレクトリ。gitignore される。

## Git 規則

- **ブランチ**: `main`（デフォルト）、`exp/{番号}-{subtitle}`、`feature/{名前}`、`fix/{内容}`
- **コミット**: gitmoji + 日本語。1コミット = 1つの論理的な変更。例: `🧪 exp001-baseline を追加`
- **push**: 作業の区切りごと、実験完了時に push

## コマンド

```bash
uv sync                        # 依存関係インストール
just app                       # Web アプリ起動
just debug exp001-baseline     # デバッグモードで実行
just train exp001-baseline     # 本番モードで実行
just infer exp001-baseline     # 推論実行
just infer-tta exp001-baseline # TTA 推論実行
```
