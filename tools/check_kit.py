"""Check files, TOML, links, and this kit's simple skill metadata; not runtime discovery.

Skill frontmatter supports only an unquoted name and a JSON-compatible double-quoted,
one-line description between --- lines. This is not a general YAML validator.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_NAMES = (
    "starter-clarify-requirements", "starter-plan-tasks", "starter-test-behavior",
    "starter-debug", "starter-review", "starter-verify-completion", "starter-record-decisions",
)
SKILL_FILES = tuple(f".agents/skills/{name}/SKILL.md" for name in SKILL_NAMES)
PLACEHOLDERS = {"todo", "tbd", "fixme", "...", "미정", "작성 예정"}


def check_skill(content: str, expected_name: str, label: str) -> list[str]:
    """Validate only the bounded frontmatter form authored by this kit."""
    failures: list[str] = []
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return [f"Missing skill frontmatter: {label}"]
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return [f"Unclosed skill frontmatter: {label}"]
    fields: dict[str, str] = {}
    for line in lines[1:end]:
        key, separator, value = line.partition(":")
        key = key.strip()
        if not separator or key not in ("name", "description") or key in fields:
            failures.append(f"Invalid or duplicate skill metadata: {label}")
            continue
        fields[key] = value.strip()
    name = fields.get("name", "")
    if name != expected_name or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        failures.append(f"Skill name must match folder {expected_name}: {label}")
    try:
        description = json.loads(fields.get("description", ""))
    except (ValueError, TypeError):
        description = None
    if (not isinstance(description, str) or not description.strip()
            or "\n" in description or "\r" in description
            or description.strip().casefold() in PLACEHOLDERS):
        failures.append(f"Invalid or unfinished skill description: {label}")
    body = "\n".join(lines[end + 1:]).strip()
    if not body or body.casefold() in PLACEHOLDERS:
        failures.append(f"Missing or unfinished skill instructions: {label}")
    return failures


def check(root: Path) -> list[str]:
    failures: list[str] = []
    contents: dict[Path, str] = {}
    checked: set[Path] = set()
    required = (
        "README.md", "AGENTS.md", "RUN.md", "docs/SPEC.md", "docs/PLAN.md",
        "docs/VERIFY.md", "docs/EXPLAIN.md",
        "prompts/START_CYCLE.md", "prompts/ROLE_FALLBACK.md",
        "references/TOOLS.md", "references/SKILLS.md", "references/TIME_MANAGEMENT.md",
        ".agents/skills/THIRD_PARTY_NOTICES.md", "tools/install_kit.py", "src/README.md", "outputs/README.md",
        *SKILL_FILES,
    )
    for name in required:
        path = root / name
        checked.add(path)
        if not path.is_file():
            failures.append(f"Missing or empty: {name}")
            continue
        try:
            contents[path] = path.read_text(encoding="utf-8")
            if not contents[path].strip():
                failures.append(f"Missing or empty: {name}")
        except (OSError, UnicodeError) as error:
            failures.append(f"Cannot read UTF-8 {name}: {error}")
    for name, relative in zip(SKILL_NAMES, SKILL_FILES):
        content = contents.get(root / relative)
        if content is not None:
            failures.extend(check_skill(content, name, relative))
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
        if path in checked:
            if path not in contents:
                continue
            content = contents[path]
        else:
            try:
                content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as error:
                failures.append(f"Cannot read UTF-8 {path.relative_to(root).as_posix()}: {error}")
                continue
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
    print("PASS: kit structure, UTF-8 files, simple skill frontmatter, TOML fields, and local Markdown links")
    print("SKILL FORMAT: unquoted name and double-quoted one-line description; not general YAML")
    print("NOT CHECKED: service behavior, skill/custom-agent discovery, actual skill or subagent calls")


if __name__ == "__main__":
    main()
