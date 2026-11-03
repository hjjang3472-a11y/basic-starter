"""Validate kit structure and TOML syntax, not service or subagent execution."""
from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check(root: Path) -> list[str]:
    failures: list[str] = []
    required = (
        "README.md", "AGENTS.md", "RUN.md", "docs/SPEC.md", "docs/PLAN.md",
        "docs/VERIFY.md", "docs/EXPLAIN.md",
        "prompts/START_CYCLE.md", "prompts/ROLE_FALLBACK.md",
        "references/TOOLS.md", "tools/install_kit.py", "src/README.md", "outputs/README.md",
    )
    for name in required:
        path = root / name
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            failures.append(f"Missing or empty: {name}")
    for name in ("implementer", "explainer", "verifier"):
        path = root / ".codex" / "agents" / f"{name}.toml"
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
            for field in ("name", "description", "developer_instructions"):
                if not isinstance(data.get(field), str) or not data[field].strip():
                    failures.append(f"Invalid {field}: {path.name}")
            if data.get("name") != name:
                failures.append(f"Agent name mismatch: {path.name}")
            if "model" in data or "model_reasoning_effort" in data:
                failures.append(f"Unexpected fixed model setting: {path.name}")
        except (OSError, ValueError) as error:
            failures.append(f"Cannot parse {path.name}: {error}")
    for path in root.rglob("*.md"):
        if ".git" in path.relative_to(root).parts:
            continue
        content = path.read_text(encoding="utf-8")
        for link in re.findall(r"\]\(([^)]+)\)", content):
            if "://" in link or link.startswith("#"):
                continue
            if not (path.parent / link.split("#", 1)[0]).exists():
                failures.append(f"Broken local link in {path.name}: {link}")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    failures = check(args.root)
    for failure in failures:
        print(f"FAIL: {failure}")
    if failures:
        sys.exit(1)
    print("PASS: kit structure, UTF-8 files, TOML fields, and local Markdown links")
    print("NOT CHECKED: service behavior, Codex custom-agent discovery, actual subagent calls")


if __name__ == "__main__":
    main()
