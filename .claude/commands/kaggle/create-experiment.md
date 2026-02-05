# 新しい実験を作成

新しい実験ディレクトリを作成してください。

## 手順

1. `src/` ディレクトリ内の既存の実験を確認し、次の番号を決定
2. `src/exp000-sample/` をコピーして新しい実験ディレクトリを作成
   - 命名規則: `exp{番号}-{subtitle}`
   - 番号は3桁ゼロ埋め（001, 002, ...）
3. 新しい実験の `config/config.yaml` の `exp_name` を更新
4. `README.md` の Experiments テーブルに新しい行を追加（CV, LB は `-` で初期化）
5. `README.md` の Experiment Tree（mermaid）に新しいノードを追加

## 引数

$ARGUMENTS に実験のサブタイトル（例: `baseline`, `feature-engineering`）が渡されます。
引数がない場合は、ユーザーに実験の目的を質問してサブタイトルを決定してください。

## 完了後

- 作成したディレクトリのパスを報告
- 次のステップ（train.py の編集など）を案内
