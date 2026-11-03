"""Meaningful regression checks: task source files must survive kit installation."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("install_kit", ROOT / "tools" / "install_kit.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class InstallSafetyTests(unittest.TestCase):
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
