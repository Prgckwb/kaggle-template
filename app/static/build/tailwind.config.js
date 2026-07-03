/** @type {import('tailwindcss').Config} */

// テンプレートで `bg-{{ meta.color }}-50` のように色を変数展開している箇所は
// コンテンツスキャンで検出できないため、safelist の正規表現でカバーする。
// 対象色・値・バリアントを増やすと CSS サイズが線形に増えるので、
// 実際に動的に使う組み合わせだけを列挙する（リテラルで書いたクラスはスキャンで拾われる）。
const C = "(emerald|amber|sky|rose|violet|red|yellow|gray)";

module.exports = {
  darkMode: "class",
  content: [
    "../../templates/**/*.html",
    "../../pages/**/*.py",
    // fragment ガイド（docs/guides/）も Tailwind クラスを使うためスキャン対象
    "../../../docs/guides/**/*.html",
  ],
  safelist: [
    // 正規表現は必ず ^...$ でアンカーする。アンカーがないと不透明度修飾
    // （bg-emerald-500/40 等）まで全展開され、CSS が 10 倍以上に肥大化する。
    {
      pattern: new RegExp(`^bg-${C}-(50|100|500|600|900)$`),
      variants: ["hover", "dark", "dark:hover"],
    },
    {
      pattern: new RegExp(`^bg-${C}-900/30$`),
      variants: ["hover", "dark", "dark:hover"],
    },
    {
      pattern: new RegExp(`^text-${C}-(100|200|300|400|500|600|700|800)$`),
      variants: ["hover", "dark", "dark:hover", "group-hover"],
    },
    {
      pattern: new RegExp(`^border-${C}-(50|100|200|400|700|800)$`),
      variants: ["hover", "dark"],
    },
  ],
  plugins: [require("@tailwindcss/typography")],
};
