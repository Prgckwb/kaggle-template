#!/usr/bin/env python3
"""PreToolUse hook: 共有作業ツリーと提出枠を守るガード。

Bash ツールに渡されたコマンドを検査し、次の 2 種類を実行前に止める。

1. 併走セッションの未コミット作業を壊す git 操作
   （`git add -A` / `git add .` / `git commit -a` / `git stash` /
   `git reset --hard` / `git checkout --`）
2. Kaggle への提出（提出はユーザーの専管）

判定は `.claude/settings.json` の `permissions.deny` と二重の網になっている。
deny は宣言的にパターンを弾き、この hook は理由を添えて止める。
hook 側だけが見られるのは `git -C <path> add -A` のように**グローバルオプションが
サブコマンドの前に挟まった形**である（deny の glob は先頭一致なので拾えない）。
逆に hook は fail-open（スクリプトに届かなければ黙って通る）なので、
deny 側が外側の網として必要になる。どちらも欠かせない。

前提の設定は `docs/competition-profile.yaml` の `workflow` にある。
`concurrent_sessions: false` なら git 系の規則、`submission_by: agent` なら
提出の規則をそれぞれ外してよい（理由は `docs/ai-agent-guidelines.md` の「運用の合意」）。

stdin から PreToolUse の payload（JSON）を読み、抵触したときだけ
`permissionDecision: deny` の JSON を stdout に出す。抵触しなければ何も出さない
（= 通常の許可フローに委ねる）。判定できない入力では黙って通す
（hook 自身の失敗でエージェントの作業を止めないため）。
"""

from __future__ import annotations

import json
import re
import sys

# git のサブコマンドの前に挟まるグローバルオプションを吸収する接頭辞。
# `git -C <path> add -A` / `git --git-dir=... add .` を素通しさせないため
# （`/kaggle:harvest-template` は `git -C "$TMPL"` の書き方を教えている）。
# `-C <path>` のように値が別トークンになる形も 1 要素として食う。
_GIT = r"git\s+(?:(?:-[A-Za-z]|--[A-Za-z][\w-]*)(?:[=\s]+\S+)?\s+)*"

# (正規表現, deny の理由) の並び。先に一致したものが採用される。
RULES: list[tuple[str, str]] = [
    (
        _GIT + r"add\s+(-A\b|--all\b|\.(\s|$))",
        "git add -A / git add . は併走セッションの未コミット作業を巻き込みます。"
        "コミットしたいパスを明示してください"
        "（docs/ai-agent-guidelines.md の「運用の合意」）。",
    ),
    (
        # `-a` を含む短オプション束（-a / -am / -va）と `--all`。`--amend` は素通しする。
        _GIT + r"commit\s+(?:-[^\s]*\s+|--\S+\s+)*(?:-[A-Za-z]*a[A-Za-z]*|--all)\b",
        "git commit -a / -am は追跡中の全変更を巻き込みます（git add -A と同じ危険）。"
        "パスを明示して git add してから git commit してください"
        "（docs/ai-agent-guidelines.md の「運用の合意」）。",
    ),
    (
        _GIT + r"(stash|reset\s+--hard|checkout\s+--)",
        "この操作は併走セッションの未コミット作業を消します。共有ファイルには打たず、"
        "必要ならユーザーに確認してください"
        "（docs/ai-agent-guidelines.md の「併走セッション前提の作業規律」）。",
    ),
    (
        r"kaggle\s+competitions\s+submit",
        "提出はユーザーの専管です"
        "（docs/competition-profile.yaml の workflow.submission_by）。"
        "notebook の commit と出力確認までで止めてください。",
    ),
]


def decide(command: str) -> str | None:
    """コマンドに抵触する規則があればその理由を返す。無ければ None。"""
    for pattern, reason in RULES:
        if re.search(pattern, command):
            return reason
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return 0
    if not isinstance(payload, dict):
        return 0
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    command = tool_input.get("command")
    if not isinstance(command, str):
        return 0

    reason = decide(command)
    if reason is None:
        return 0

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
