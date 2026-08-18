#!/usr/bin/env python3
"""PreToolUse hook: 共有作業ツリーと提出枠を守るガード。

Bash ツールに渡されたコマンドを検査し、次の 2 種類を実行前に止める。

1. 併走セッションの未コミット作業を壊す git 操作
   （`git add -A` / `git add .` / `git stash` / `git reset --hard` / `git checkout --`）
2. Kaggle への提出（提出はユーザーの専管）

判定は `.claude/settings.json` の `permissions.deny` と二重の網になっている。
deny は宣言的にパターンを弾き、この hook は理由を添えて止める。

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

# (正規表現, deny の理由) の並び。先に一致したものが採用される。
RULES: list[tuple[str, str]] = [
    (
        r"git\s+add\s+(-A\b|--all\b|\.(\s|$))",
        "git add -A / git add . は併走セッションの未コミット作業を巻き込みます。"
        "コミットしたいパスを明示してください"
        "（docs/ai-agent-guidelines.md の「運用の合意」）。",
    ),
    (
        r"git\s+(stash|reset\s+--hard|checkout\s+--)",
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
