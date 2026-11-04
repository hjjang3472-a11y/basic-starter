"""Meaningful regression checks: task source files must survive kit installation."""
import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("install_kit", ROOT / "tools" / "install_kit.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
check_spec = importlib.util.spec_from_file_location("check_kit", ROOT / "tools" / "check_kit.py")
checker = importlib.util.module_from_spec(check_spec)
check_spec.loader.exec_module(checker)

SKILL_NAMES = (
    "starter-clarify-requirements", "starter-plan-tasks", "starter-test-behavior",
    "starter-debug", "starter-review", "starter-verify-completion", "starter-record-decisions",
)
SKILL_PATHS = tuple(f".agents/skills/{name}/SKILL.md" for name in SKILL_NAMES)
GUIDE_PATHS = (
    ".agents/skills/THIRD_PARTY_NOTICES.md", "references/SKILLS.md", "references/TIME_MANAGEMENT.md",
)


def fixture_source(directory: str) -> Path:
    """Build an independent valid source, even before real skill files are authored."""
    source = Path(directory) / "source"
    source.mkdir()
    base_files = (*module.PAYLOAD, "README.md", "src/README.md", "outputs/README.md", "tools/install_kit.py")
    for relative in base_files:
        original = ROOT / relative
        if original.is_file():
            target = source / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original, target)
    for name, relative in zip(SKILL_NAMES, SKILL_PATHS):
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            f'---\nname: {name}\ndescription: "Use when a synthetic test task needs this workflow."\n---\n'
            '# Synthetic workflow\n\nRead the task, act within scope, and report observed evidence.\n',
            encoding="utf-8",
        )
    for relative in GUIDE_PATHS:
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# Synthetic preparation guide\n\nOriginal test fixture content.\n", encoding="utf-8")
    return source


class InstallSafetyTests(unittest.TestCase):
    def test_install_delivers_seven_skills_and_shared_guides(self):
        with tempfile.TemporaryDirectory() as directory:
            source = fixture_source(directory)
            target = Path(directory) / "task"
            target.mkdir()
            (target / "README.md").write_text("original task", encoding="utf-8")
            module.install(target, apply=True, source=source)
            for relative in (*SKILL_PATHS, *GUIDE_PATHS):
                with self.subTest(path=relative):
                    self.assertTrue((target / relative).is_file(), f"Not installed: {relative}")
                    self.assertEqual((target / relative).read_bytes(), (source / relative).read_bytes())
            self.assertEqual((target / "README.md").read_text(encoding="utf-8"), "original task")

    def test_install_preserves_existing_user_and_colliding_skills(self):
        with tempfile.TemporaryDirectory() as directory:
            source = fixture_source(directory)
            target = Path(directory) / "task"
            target.mkdir()
            originals = {
                SKILL_PATHS[0]: "my edited starter skill",
                ".agents/skills/user-only/SKILL.md": "my unrelated private workflow",
                "data/source.csv": "original,data\n1,2\n",
            }
            for relative, content in originals.items():
                path = target / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            rows = module.install(target, apply=True, source=source)
            for relative, content in originals.items():
                self.assertEqual((target / relative).read_text(encoding="utf-8"), content)
            self.assertTrue((target / SKILL_PATHS[1]).is_file())
            self.assertEqual(next(row["status"] for row in rows if row["path"] == SKILL_PATHS[0]), "EXISTS")

    def test_checker_rejects_invalid_skill_metadata_and_unfinished_body(self):
        with tempfile.TemporaryDirectory() as directory:
            source = fixture_source(directory)
            self.assertEqual(checker.check(source), [])
            name, relative = SKILL_NAMES[0], SKILL_PATHS[0]
            path = source / relative
            cases = {
                "missing name": '---\ndescription: "Valid description"\n---\nRead the task.\n',
                "wrong name": '---\nname: unrelated-skill\ndescription: "Valid description"\n---\nRead the task.\n',
                "missing description": f'---\nname: {name}\n---\nRead the task.\n',
                "blank description": f'---\nname: {name}\ndescription: "  "\n---\nRead the task.\n',
                "unfinished description": f'---\nname: {name}\ndescription: "TBD"\n---\nRead the task.\n',
                "missing frontmatter": f'# {name}\n\nRead the task.\n',
                "empty body": f'---\nname: {name}\ndescription: "Valid description"\n---\n',
                "duplicate metadata": f'---\nname: {name}\nname: {name}\ndescription: "Valid description"\n---\nRead the task.\n',
            }
            for label, content in cases.items():
                with self.subTest(case=label):
                    path.write_text(content, encoding="utf-8")
                    errors = checker.check(source)
                    self.assertTrue(any(relative in error for error in errors), errors)

    def test_checker_reports_missing_skill(self):
        with tempfile.TemporaryDirectory() as directory:
            source = fixture_source(directory)
            relative = SKILL_PATHS[-1]
            path = source / relative
            path.unlink()
            errors = checker.check(source)
            self.assertTrue(any(relative in error for error in errors), errors)

    def test_checker_reports_invalid_utf8(self):
        with tempfile.TemporaryDirectory() as directory:
            source = fixture_source(directory)
            relative = SKILL_PATHS[-1]
            path = source / relative
            path.write_bytes(b"\xff\xfe\xff")
            try:
                errors = checker.check(source)
            except UnicodeError as error:
                self.fail(f"Invalid UTF-8 must be reported as a validation failure, not raised: {error}")
            self.assertTrue(any(relative in error for error in errors), errors)

    def test_preview_writes_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            rows = module.install(target)
            self.assertTrue(rows)
            self.assertEqual(list(target.iterdir()), [])

    def test_task_readme_and_existing_instructions_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            original = {"README.md": "original task", "AGENTS.md": "original rules", "docs/PLAN.md": "original plan"}
            for name, content in original.items():
                path = target / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            module.install(target, apply=True)
            for name, content in original.items():
                self.assertEqual((target / name).read_text(encoding="utf-8"), content)
            self.assertTrue((target / "AGENTS.practice.md").is_file())
            self.assertTrue((target / ".codex/agents/implementer.toml").is_file())
            self.assertTrue((target / ".codex/agents/explainer.toml").is_file())
            self.assertTrue((target / ".codex/agents/verifier.toml").is_file())
            self.assertFalse((target / ".codex/agents/reviewer.toml").exists())
            self.assertNotIn("tools/check_kit.py", (target / "RUN.md").read_text(encoding="utf-8"))

    def test_repeated_install_does_not_overwrite_user_edits(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            module.install(target, apply=True)
            edited = target / "docs/EXPLAIN.md"
            edited.write_text("my actual work", encoding="utf-8")
            module.install(target, apply=True)
            self.assertEqual(edited.read_text(encoding="utf-8"), "my actual work")
            self.assertFalse((target / "AGENTS.practice.md").exists())

    def test_invalid_parent_fails_before_any_file_is_created(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "docs").write_text("not a folder", encoding="utf-8")
            with self.assertRaises(ValueError):
                module.install(target, apply=True)
            self.assertEqual(sorted(p.name for p in target.iterdir()), ["docs"])

    def test_existing_directory_at_file_destination_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "RUN.md").mkdir()
            with self.assertRaises(ValueError):
                module.install(target, apply=True)
            self.assertFalse((target / "AGENTS.md").exists())

    def test_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                module.checked_destination(Path(directory).resolve(), "../outside.md")

    def test_linked_parent_rejected(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            target = Path(directory)
            try:
                (target / "docs").symlink_to(outside, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"Symlink creation unavailable: {error}")
            with self.assertRaises(ValueError):
                module.install(target, apply=True)
            self.assertEqual(list(Path(outside).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
