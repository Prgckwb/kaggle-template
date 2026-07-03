# Tailwind CSS ビルド環境

ダッシュボードの `app/static/css/app.css` を生成するビルド環境。**リポジトリにコミットする**
（`.gitignore` は `/build/`（ルートのみ）を除外しており、このディレクトリは対象外。
`node_modules/` のみ ignore され、`package-lock.json` は再現性のためコミットする）。

## 使い方

```bash
make css   # ルートから実行（npm install + build）
```

テンプレート（`app/templates/`）や fragment ガイド（`docs/guides/**/*.html`）に
**新しい Tailwind ユーティリティクラスを追加したら再ビルドが必要**。
既存クラスと safelist 済みの動的色クラス（下記）はそのままで動く。

## 動的色クラスと safelist

テンプレートには `bg-{{ meta.color }}-50` のように色を変数展開する箇所があり、
コンテンツスキャンでは検出できない。`tailwind.config.js` の safelist が
emerald / amber / sky / rose / violet / blue / red / orange / indigo / gray の
よく使うパターン（bg/text/border/ring × hover/dark/group-hover）をカバーしている。

- 新しい色ファミリーを動的に使う場合は `DYNAMIC_COLORS` に追加して再ビルド
- safelist にないパターン（例: `bg-{color}-200`）を動的に使うとスタイルが当たらないので注意

## 注意

- この環境は 2026-07 に再構築されたもの（初版は `.gitignore` の `build/` パターンにより
  誤ってコミットから漏れていた）。出力が旧 app.css と完全一致する保証はないが、
  全テンプレートのクラスカバレッジを検証済み
- Tailwind v3 系。v4 への更新時は safelist の書式が変わるため要移行作業
