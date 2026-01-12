# exp000_sample

## 概要
サンプル実験。テンプレートの動作確認用。

## 目的
- Hydra による設定管理の確認
- wandb 連携の確認
- 実験フォルダ構成のサンプル

## 実行方法

```bash
# デフォルト設定で実行
uv run python experiments/exp000_sample/run.py

# 設定を指定して実行
uv run python experiments/exp000_sample/run.py conf=001
```

## 設定ファイル
- `config.yaml`: メイン設定
- `conf/000.yaml`: デフォルト実験設定
- `conf/001.yaml`: 別シード実験設定

## 結果
<!-- 実験結果を記載 -->

## メモ
<!-- 実験中の気づきなど -->
