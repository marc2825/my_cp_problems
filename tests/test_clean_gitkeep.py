"""Only .gitkeep files in directories Git keeps anyway are removed."""

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import clean_gitkeep


class CleanGitkeepTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for name in ("empty/.gitkeep", "filled/.gitkeep", "filled/main.cpp",
                     "nested/.gitkeep", "nested/child/data.txt",
                     "parent/.gitkeep", "parent/child/.gitkeep",
                     "cache/.gitkeep", "cache/__pycache__/x.pyc",
                     ".venv/lib/.gitkeep", ".venv/lib/site.py"):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("" if name.endswith(".gitkeep") else "x")

    def run_cli(self, *args):
        with patch.object(clean_gitkeep, "ROOT", self.root), redirect_stdout(io.StringIO()) as out:
            self.assertEqual(clean_gitkeep.main(list(args)), 0)
        return out.getvalue()

    def test_removes_only_redundant_gitkeeps(self):
        out = self.run_cli()
        for name in ("filled", "nested", "parent"):
            self.assertIn(f"GITKEEP REMOVE {name}/.gitkeep", out)
            self.assertFalse((self.root / name / ".gitkeep").exists())
        for name in ("empty", "parent/child", "cache", ".venv/lib"):
            self.assertTrue((self.root / name / ".gitkeep").exists(), name)
        self.assertIn("GITKEEP SKIP", self.run_cli())

    def test_dry_run_deletes_nothing(self):
        out = self.run_cli("--dry-run")
        self.assertIn("GITKEEP REMOVE filled/.gitkeep", out)
        self.assertTrue((self.root / "filled/.gitkeep").exists())


if __name__ == "__main__":
    unittest.main()
