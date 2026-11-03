"""Add workflow files to an existing task without replacing any file (Python 3.11+)."""
from __future__ import annotations

import argparse
import json
import stat
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = (
    "AGENTS.md", "RUN.md",
    "docs/SPEC.md", "docs/PLAN.md", "docs/VERIFY.md", "docs/EXPLAIN.md",
    ".codex/agents/implementer.toml", ".codex/agents/explainer.toml", ".codex/agents/verifier.toml",
    "prompts/START_CYCLE.md", "prompts/ROLE_FALLBACK.md", "practice/CYCLE_TRIAL.md",
    "references/TOOLS.md", "references/SOURCES.md",
)


def checked_destination(root: Path, relative: str) -> Path:
    """Reject links/junctions and paths escaping the user-selected task."""
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(f"Unsafe relative path: {relative}")
    destination = root / relative_path
    current = destination
    while current != root:
        attributes = getattr(current.lstat(), "st_file_attributes", 0) if current.exists() or current.is_symlink() else 0
        if current.is_symlink() or attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
            raise ValueError(f"Linked destination is not supported: {relative}")
        if current.exists() and current != destination and not current.is_dir():
            raise ValueError(f"Parent is not a directory: {relative}")
        current = current.parent
    if not destination.resolve().is_relative_to(root):
        raise ValueError(f"Destination escapes target: {relative}")
    return destination


def install(target: Path, apply: bool = False, source: Path = KIT_ROOT) -> list[dict[str, str]]:
    root = target.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Target must be an existing task directory")
    if root == source.resolve():
        raise ValueError("Choose a task directory outside the kit")
    plan: list[tuple[Path, Path, dict[str, str]]] = []
    # Validate every destination before creating anything.
    for relative in PAYLOAD:
        source_file = source / ("templates/RUN.md" if relative == "RUN.md" else relative)
        if not source_file.is_file():
            raise ValueError(f"Missing kit file: {relative}")
        output_name = relative
        if relative == "AGENTS.md" and (root / relative).exists():
            existing = checked_destination(root, relative)
            if not existing.is_file():
                raise ValueError("Existing AGENTS.md is not a file")
            if existing.read_bytes() != source_file.read_bytes():
                output_name = "AGENTS.practice.md"
        destination = checked_destination(root, output_name)
        if destination.exists() and not destination.is_file():
            raise ValueError(f"Destination is not a file: {output_name}")
        row = {"path": output_name, "status": "EXISTS" if destination.exists() else "ADD"}
        plan.append((source_file, destination, row))
    for source_file, destination, row in plan:
        if apply and row["status"] == "ADD":
            destination.parent.mkdir(parents=True, exist_ok=True)
            # Exclusive create protects an existing file if it appeared after planning.
            try:
                with destination.open("xb") as output:
                    output.write(source_file.read_bytes())
                row["status"] = "ADDED"
            except FileExistsError:
                row["status"] = "EXISTS"
    return [row for _, _, row in plan]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--apply", action="store_true", help="Write missing files; default is preview only")
    args = parser.parse_args()
    try:
        rows = install(args.target, args.apply)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Cannot install: {error}\n")
    print(json.dumps({"mode": "apply" if args.apply else "preview", "files": rows}, ensure_ascii=False, indent=2))
    print("Existing files are preserved. Read AGENTS.practice.md explicitly if present.")


if __name__ == "__main__":
    main()
