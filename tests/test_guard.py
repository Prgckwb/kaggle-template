"""`.claude/hooks/guard.py` の判定テスト。

hook は「共有作業ツリーを壊す git 操作」と「Kaggle への提出」を止める最後の砦で、
判定はすべて正規表現に載っている。正規表現の退行（穴が開く / 正当なコマンドを誤って
拒否する）を止めるため、DENY 期待と ALLOW 期待を両方固定する。

`.claude/` はパッケージではないので `importlib` でファイルから直接読み込む
（パスは tests/ の親を起点にして cwd に依存させない）。
"""

from __future__ import annotations

import importlib.util
import io
import json
import time
import types
from pathlib import Path

import pytest

_GUARD_PATH = Path(__file__).parents[1] / ".claude" / "hooks" / "guard.py"


def _load_guard() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("guard_hook", _GUARD_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guard = _load_guard()


# 止めなければならないコマンド。`git -C <path>` / `git --git-dir=...` のように
# グローバルオプションが挟まった形は deny の glob（先頭一致）では拾えず、
# hook だけが見ているので必ず含める。
DENY_COMMANDS = [
    # 追跡中の全変更 / 未追跡ファイルを巻き込む add
    "git add -A",
    "git add .",
    "git add --all",
    "git add -u",
    "git add --update",
    "git add -Av",
    "git add -vu",
    "git -C /tmp add -A",
    "git -C /tmp add -u",
    "git --git-dir=/x/.git add .",
    # 追跡中の全変更を巻き込む commit
    'git commit -am "x"',
    "git commit -a",
    "git commit --all -m x",
    'git -C /tmp commit -am "x"',
    # 相手の未コミット作業を消す操作
    "git stash",
    "git stash push -m wip",
    "git -C /tmp stash",
    "git reset --hard",
    "git reset --hard HEAD~1",
    "git checkout -- .",
    "git checkout -- src/utils/cv.py",
    # 提出はユーザーの専管
    "kaggle competitions submit -c x -f y",
    "uv run kaggle competitions submit -c x -f y",
]


# 通さなければならないコマンド。ここが壊れるとガードが日常操作を止めてしまう。
ALLOW_COMMANDS = [
    "git add path/to/file",
    "git add src/utils/cv.py tests/test_cv.py",
    "git add -- src/utils/cv.py",
    "git add -p src/utils/cv.py",
    "git add -N src/utils/new.py",
    "git status",
    "git status --short",
    "git diff",
    "git diff --cached",
    'git commit -m "add -A stuff"',
    "git commit --amend --no-edit",
    "git checkout main",
    "git checkout -b feature/x",
    "git reset HEAD~1",
    "git restore --staged src/utils/cv.py",
    # `submissions` は読み取り専用の照会。`submit` の前方一致で巻き込まない
    "uv run kaggle competitions submissions",
    "uv run kaggle competitions submissions -c x",
    "uv run kaggle competitions list -s knee",
    "uv run python tools/check_submission.py",
]


@pytest.mark.parametrize("command", DENY_COMMANDS)
def test_denied_commands(command: str) -> None:
    assert guard.decide(command) is not None, f"素通しした: {command}"


@pytest.mark.parametrize("command", ALLOW_COMMANDS)
def test_allowed_commands(command: str) -> None:
    assert guard.decide(command) is None, f"誤って拒否した: {command}"


def test_deny_reason_points_to_the_documented_agreement() -> None:
    """理由文には代替手段の在り処を書く（黙って止めない）。"""
    reason = guard.decide("git add -A")
    assert reason is not None
    assert "docs/ai-agent-guidelines.md" in reason


def _run_main(stdin_text: str, monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setattr(guard.sys, "stdin", io.StringIO(stdin_text))
    printed: list[str] = []
    monkeypatch.setattr("builtins.print", lambda *a, **k: printed.append(str(a[0])))
    assert guard.main() == 0
    return "".join(printed)


def test_main_emits_deny_json_for_a_blocked_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {"tool_name": "Bash", "tool_input": {"command": "git add -A"}}
    out = _run_main(json.dumps(payload), monkeypatch)
    decision = json.loads(out)["hookSpecificOutput"]
    assert decision["hookEventName"] == "PreToolUse"
    assert decision["permissionDecision"] == "deny"
    assert decision["permissionDecisionReason"]


def test_main_stays_silent_for_an_allowed_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {"tool_name": "Bash", "tool_input": {"command": "git status"}}
    assert _run_main(json.dumps(payload), monkeypatch) == ""


@pytest.mark.parametrize(
    "stdin_text",
    [
        "not json at all",
        "",
        '["not", "a", "dict"]',
        '{"tool_input": "not a dict"}',
        '{"tool_input": {"command": ["not", "a", "str"]}}',
        '{"tool_input": {}}',
        "{}",
    ],
)
def test_malformed_payloads_fail_open(
    stdin_text: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """判定できない入力では黙って通す（hook 自身の失敗で作業を止めない）。

    これは意図した挙動である。fail-open だからこそ `permissions.deny` が
    外側の網として必要になる（README「2 層が必要な理由」）。
    """
    assert _run_main(stdin_text, monkeypatch) == ""


@pytest.mark.parametrize(
    "command",
    [
        "git " + "-a " * 40 + "zzz",
        "git commit " + "--a " * 40 + "zzz",
        "git " + "-C /tmp " * 40 + "add -A",
    ],
)
def test_pathological_option_runs_do_not_backtrack(command: str) -> None:
    """オプションの繰り返しで指数バックトラックしない。

    ハングすると hook はタイムアウトして fail-open になり、ガードが無いのと同じになる。
    """
    started = time.perf_counter()
    guard.decide(command)
    assert time.perf_counter() - started < 1.0
