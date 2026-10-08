#!/usr/bin/env -S uv run --no-project
"""PreToolUse hook: 共有作業ツリーと提出枠を守るガード（ガード規則の唯一の正本）。

止めるもの:
1. 併走セッションの未コミット作業を巻き込む・消す git 操作
   （profile の `workflow.concurrent_sessions: true` のとき）
   - `git add -A` / `--all` / `-u` / `--update` / `.`（パスを明示させる）
   - `git commit -a` / `--all`
   - `git stash`（list / show 以外）/ `git reset --hard` / `git checkout -- …` / `git checkout .`
   - `git restore …`（`--staged` だけのものは許可）/ `git clean -f…`
2. Kaggle への提出（profile の `workflow.submission_by: user` のとき）
   - Bash の `kaggle competitions submit`
   - Kaggle MCP の提出系ツール（submit / submission upload）
3. `uv run` を通さない Python の実行（常に有効）
   - `python` / `python3` / `pip` / `.venv/bin/python` などの直接呼び出し。
     `uv run python ...` / `uv run script.py` / `uv run --with X ...` を使わせる

判定はコマンドを引用符の外の `&&` `||` `;` `|` `$(` 改行で区切った**各セグメントの先頭**に対して行う。
`grep 'git add -A' docs` や `echo`・引用符・ヒアドキュメント本文の中の文字列では発火しない。
`git -C <path> add -A` のようにサブコマンドの前に挟まるグローバルオプションは吸収する。

stdlib のみで動く（hook は `uv run --no-project` で起動され、プロジェクトの .venv に依存しない）。
判定できない入力は通す。
profile が読めない場合は安全側（両方のガードを有効）に倒す。
"""

from __future__ import annotations

import json
import re
import shlex
import sys
from pathlib import Path

PROFILE = Path(__file__).resolve().parents[2] / "docs" / "competition-profile.yaml"

GIT_REASON = (
    "併走セッションの未コミット作業を巻き込む／消す git 操作です。"
    "パスを明示して git add するか、必要ならユーザーに確認してください"
    "（docs/competition-profile.yaml の workflow.concurrent_sessions）。"
)
SUBMIT_REASON = (
    "提出はユーザーの専管です（docs/competition-profile.yaml の workflow.submission_by）。"
    "notebook の commit と出力確認までで止めてください。"
)
PYTHON_REASON = (
    "Python は必ず uv run 経由で実行してください"
    "（例: uv run python -m src.exp001_xxx.train / uv run script.py / uv run --with ruff ruff check）。"
)
BARE_PYTHON = re.compile(r"^(python(\d+(\.\d+)?)?|pip\d*(\.\d+)?)$")
SUBMIT_MCP = re.compile(
    r"^mcp__kaggle__(submit|start_competition_submission|create_.*submission)"
)
SEPARATORS = ";&|()`\n"
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1")
GIT_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}


def workflow_flags() -> tuple[bool, bool]:
    """(concurrent_sessions, submission_by_user) を profile から読む（YAML パーサ無しの簡易読み）。"""
    try:
        text = PROFILE.read_text()
    except OSError:
        return True, True
    concurrent = re.search(r"^\s*concurrent_sessions:\s*(\w+)", text, re.MULTILINE)
    submission = re.search(r"^\s*submission_by:\s*(\w+)", text, re.MULTILINE)
    return (
        concurrent is None or concurrent.group(1).lower() != "false",
        submission is None or submission.group(1).lower() != "agent",
    )


def _git_args(tokens: list[str]) -> list[str] | None:
    """`git [global opts] <sub> args...` なら [<sub>, args...] を返す。"""
    if not tokens or Path(tokens[0]).name != "git":
        return None
    i = 1
    while i < len(tokens) and tokens[i].startswith("-"):
        i += 2 if tokens[i] in GIT_OPTS_WITH_VALUE else 1
    return tokens[i:] or None


def _short_flags(args: list[str]) -> str:
    return "".join(a[1:] for a in args if a.startswith("-") and not a.startswith("--"))


def dangerous_git(args: list[str]) -> bool:
    sub, rest = args[0], args[1:]
    flags = _short_flags(rest)
    if sub == "add":
        return (
            any(a in ("--all", "--update", ".", "./", ":/") for a in rest)
            or "A" in flags
            or "u" in flags
        )
    if sub == "commit":
        return "--all" in rest or "a" in flags
    if sub == "stash":
        return not rest or rest[0] not in ("list", "show")
    if sub == "reset":
        return "--hard" in rest
    if sub == "checkout":
        return "--" in rest or "." in rest
    if sub == "restore":
        return (
            not ("--staged" in rest or "S" in flags)
            or "--worktree" in rest
            or "W" in flags
        )
    if sub == "clean":
        return "f" in flags or "--force" in rest
    return False


def is_submit(tokens: list[str]) -> bool:
    words = [t for t in tokens if not t.startswith("-")]
    while words and words[0] in ("uv", "run", "uvx", "python", "python3", "-m"):
        words = words[1:]
    return words[:3] == ["kaggle", "competitions", "submit"]


def _tokenize(command: str) -> list[str]:
    """引用符を尊重してトークン化し、制御演算子（; & | ( ) ` 改行）を独立トークンにする。"""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=SEPARATORS)
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:  # 閉じていない引用符など。素朴な分割で判定を続ける
        return re.split(r"\s+|(?=[;&|()`\n])|(?<=[;&|()`\n])", command)


def _strip_heredocs(command: str) -> str:
    """ヒアドキュメントの本文はコマンドではないので判定対象から外す（本文中の文字列で誤検知させない）。"""
    lines = command.split("\n")
    kept: list[str] = []
    terminator: str | None = None
    for line in lines:
        if terminator is not None:
            if line.strip() == terminator:
                terminator = None
            continue
        kept.append(line)
        match = HEREDOC.search(line)
        if match:
            terminator = match.group(2)
    return "\n".join(kept)


def segments(command: str) -> list[list[str]]:
    result: list[list[str]] = [[]]
    for token in _tokenize(_strip_heredocs(command)):
        if token and set(token) <= set(SEPARATORS):
            result.append([])
        elif token:
            result[-1].append(token)
    cleaned = []
    for tokens in result:
        # 先頭の環境変数代入（FOO=1 cmd）を読み飛ばす
        while tokens and re.match(r"^\w+=", tokens[0]):
            tokens = tokens[1:]
        if tokens:
            cleaned.append(tokens)
    return cleaned


def decide_bash(command: str, guard_git: bool, guard_submit: bool) -> str | None:
    for tokens in segments(command):
        if BARE_PYTHON.match(Path(tokens[0]).name):
            return PYTHON_REASON
        git = _git_args(tokens)
        if guard_git and git and dangerous_git(git):
            return GIT_REASON
        if guard_submit and is_submit(tokens):
            return SUBMIT_REASON
    return None


def decide(payload: dict) -> str | None:
    guard_git, guard_submit = workflow_flags()
    tool = payload.get("tool_name", "")
    if tool.startswith("mcp__kaggle__"):
        return SUBMIT_REASON if guard_submit and SUBMIT_MCP.match(tool) else None
    command = (payload.get("tool_input") or {}).get("command")
    if not isinstance(command, str):
        return None
    return decide_bash(command, guard_git, guard_submit)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return 0
    if not isinstance(payload, dict):
        return 0
    reason = decide(payload)
    if reason:
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
