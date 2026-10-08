""".claude/agents/*.md（正本）から .codex/agents/*.toml を生成する。

エージェント定義を変えたら実行する。.codex/agents/ は手で編集しない。

Usage:
    uv run python -m tools.sync_codex_agents
"""

from __future__ import annotations

import json
import sys

from omegaconf import OmegaConf

from src.utils.profile import PROJECT_ROOT

SRC_DIR = PROJECT_ROOT / ".claude" / "agents"
DST_DIR = PROJECT_ROOT / ".codex" / "agents"
HEADER = "# 生成ファイル: .claude/agents/{name}.md から tools/sync_codex_agents.py が作る。手で編集しない\n"


def toml_str(value: str) -> str:
    """TOML の basic string（JSON の文字列エスケープは TOML と互換）。"""
    return json.dumps(value, ensure_ascii=False)


def convert(text: str) -> tuple[str, str]:
    _, front, body = text.split("---", 2)
    meta = OmegaConf.to_container(OmegaConf.create(front))
    assert isinstance(meta, dict)
    name = meta["name"]
    toml = (
        HEADER.format(name=name)
        + f"name = {toml_str(name)}\n"
        + f"description = {toml_str(meta['description'])}\n"
        + f"developer_instructions = {toml_str(body.strip())}\n"
    )
    return name, toml


def main() -> int:
    DST_DIR.mkdir(parents=True, exist_ok=True)
    expected = set()
    for src in sorted(SRC_DIR.glob("*.md")):
        name, toml = convert(src.read_text())
        expected.add(f"{name}.toml")
        (DST_DIR / f"{name}.toml").write_text(toml)
        print(f"wrote .codex/agents/{name}.toml")
    for stale in DST_DIR.glob("*.toml"):
        if stale.name not in expected:
            stale.unlink()
            print(f"removed .codex/agents/{stale.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
