"""Index updates stay local, preserve manual prose, and record only real changes."""

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import import_yukicoder
import update_problem_index
from test_import_yukicoder import FakeClient, snapshot
from yukicoder.api import ImportError, Unavailable
from yukicoder.index import build_index_plan

FIRST = "2026-11-09T09:00:00+09:00"
SECOND = "2026-11-10T10:30:00+09:00"
README = """# My archive

Manual introduction and profile badges.

<!-- BEGIN AUTO:ARCHIVE_STATUS -->
<!-- END AUTO:ARCHIVE_STATUS -->

Manual footer.
"""


class ProblemIndexTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repository = Path(self.temporary.name) / "repository"
        self.repository.mkdir()
        (self.repository / "README.md").write_text(README)
        self.archive = self.repository / "problems/yukicoder"
        self.index = self.repository / "problems/README.md"
        self.state = self.repository / "problems/.index-state.json"
        self.client = FakeClient()

    def run_import(self, *args, stamp=FIRST):
        out, err = io.StringIO(), io.StringIO()
        with patch.object(import_yukicoder, "ROOT", self.repository), patch(
                "yukicoder.index.current_timestamp", return_value=stamp) as clock, redirect_stdout(out), redirect_stderr(err):
            code = import_yukicoder.main(["3584", "--output", str(self.archive), *args], client=self.client)
        return code, out.getvalue(), err.getvalue(), clock

    def test_import_updates_both_readmes_and_records_jst_timestamp(self):
        self.assertEqual(self.run_import()[0], 0)
        root = (self.repository / "README.md").read_text()
        index = self.index.read_text()
        for document in (root, index):
            self.assertIn("2026-11-09 09:00:00 JST", document)
            self.assertIn("**1 問**", document)
        self.assertIn("Manual introduction and profile badges.", root)
        self.assertIn("Manual footer.", root)
        self.assertIn("yukicoder/3584_camouflage_mole/README.md", index)
        self.assertIn("★1.5", index)
        self.assertIn("https://yukicoder.me/problems/no/3584", index)
        self.assertEqual(json.loads(self.state.read_text())["last_updated_at"], FIRST)

    def test_repeat_preserves_all_bytes_and_mtimes_without_reading_clock(self):
        self.run_import()
        before = snapshot(self.repository)
        code, out, _, clock = self.run_import(stamp=SECOND)
        self.assertEqual(code, 0)
        self.assertIn("INDEX SKIP", out)
        clock.assert_not_called()
        self.assertEqual(snapshot(self.repository), before)

    def test_statement_change_advances_timestamp_even_if_table_stays_the_same(self):
        self.run_import()
        self.client.html = self.client.html.replace("答えを出力する。", "答えを改行して出力する。")
        self.assertEqual(self.run_import(stamp=SECOND)[0], 0)
        self.assertEqual(json.loads(self.state.read_text())["last_updated_at"], SECOND)
        self.assertIn("2026-11-10 10:30:00 JST", self.index.read_text())

    def test_dry_run_plans_new_index_from_unsaved_metadata_without_writing(self):
        before = snapshot(self.repository)
        code, out, _, _ = self.run_import("--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("INDEX CREATE problems/README.md", out)
        self.assertIn("INDEX UPDATE README.md", out)
        self.assertEqual(snapshot(self.repository), before)
        self.assertFalse(self.archive.exists())

    def test_failed_import_does_not_advance_timestamp(self):
        self.run_import()
        before = snapshot(self.repository)
        self.client.values["/api/v1/problems/no/3584"] = Unavailable("HTTP 403")
        code, _, _, clock = self.run_import(stamp=SECOND)
        self.assertEqual(code, 1)
        clock.assert_not_called()
        self.assertEqual(snapshot(self.repository), before)

    def test_custom_output_updates_its_own_index_only(self):
        output = self.repository.parent / "custom-output"
        with patch.object(import_yukicoder, "ROOT", self.repository), patch(
                "yukicoder.index.current_timestamp", return_value=FIRST), redirect_stdout(io.StringIO()):
            self.assertEqual(import_yukicoder.main(["3584", "--output", str(output)], client=self.client), 0)
        self.assertEqual((self.repository / "README.md").read_text(), README)
        self.assertFalse(self.index.exists())
        self.assertIn("3584_camouflage_mole/README.md", (output / "README.md").read_text())
        self.assertTrue((output / ".index-state.json").exists())

    def test_offline_rebuild_adds_removes_and_sorts_problems_preserving_manual_prose(self):
        self.run_import()
        self.index.write_text(self.index.read_text() + "\nManual index notes.\n")
        other = self.archive / "100_title"
        other.mkdir()
        (other / "README.md").write_text("# Problem 100\n")
        (other / "metadata.yml").write_text(yaml.safe_dump({
            "platform": "yukicoder", "problem_no": 100, "title": "A | B [C]", "difficulty": 0,
        }))
        with patch.object(update_problem_index, "ROOT", self.repository), patch(
                "yukicoder.index.current_timestamp", return_value=SECOND), redirect_stdout(io.StringIO()):
            self.assertEqual(update_problem_index.main(["--output", str(self.archive)]), 0)
        index = self.index.read_text()
        self.assertLess(index.index("| [100]"), index.index("| [3584]"))
        self.assertIn(r"A \| B \[C\]", index)
        self.assertIn("★0", index)
        self.assertIn("Manual index notes.", index)
        self.assertIn("**2 問**", (self.repository / "README.md").read_text())
        (other / "metadata.yml").unlink()
        build_index_plan(self.archive, repository_root=self.repository).apply()
        self.assertNotIn("| [100]", self.index.read_text())

    def test_offline_rebuild_refreshes_problem_readme_file_list(self):
        self.run_import()
        directory = self.archive / "3584_camouflage_mole"
        (directory / "solution/brute.py").write_text("print(1)\n")
        (directory / "solution/main.cpp").write_text("int main() {}\n")

        def rebuild():
            with patch.object(update_problem_index, "ROOT", self.repository), patch(
                    "yukicoder.index.current_timestamp", return_value=SECOND), redirect_stdout(io.StringIO()) as out:
                self.assertEqual(update_problem_index.main(["--output", str(self.archive)]), 0)
            return out.getvalue()

        self.assertIn("UPDATE README.md", rebuild())
        readme = (directory / "README.md").read_text()
        self.assertIn("| [solution/brute.py](solution/brute.py) | 愚直解（Python） |", readme)
        self.assertIn("| [solution/main.cpp](solution/main.cpp) | 想定解（C++） |", readme)
        self.assertNotIn("solution/main.py", readme)  # Still an empty placeholder.
        self.assertIn("2026-11-10 10:30:00 JST", self.index.read_text())
        before = snapshot(self.repository)
        self.assertNotIn("README.md", rebuild())
        self.assertEqual(snapshot(self.repository), before)
        (directory / "README.md").write_text("# hand-written\n")
        (directory / "solution/main.py").write_text("print(2)\n")
        self.assertIn("PRESERVE README.md", rebuild())
        self.assertEqual((directory / "README.md").read_text(), "# hand-written\n")

    def test_broken_markers_and_state_preserve_both_readmes(self):
        self.run_import()
        for path, content in ((self.state, b'{"version":1,"last_updated_at":"invalid"}'),
                              (self.repository / "README.md", b"<!-- BEGIN AUTO:ARCHIVE_STATUS -->\n")):
            with self.subTest(path=path):
                original = path.read_bytes()
                path.write_bytes(content)
                before = snapshot(self.repository)
                with self.assertRaises(ImportError):
                    build_index_plan(self.archive, repository_root=self.repository)
                self.assertEqual(snapshot(self.repository), before)
                path.write_bytes(original)

    def test_metadata_errors_leave_existing_index_and_state_untouched(self):
        self.run_import()
        metadata = next(self.archive.glob("*/metadata.yml"))
        metadata.write_text("platform: yukicoder\nproblem_no: [\n")
        before = snapshot(self.repository)
        with self.assertRaises(ImportError):
            build_index_plan(self.archive, repository_root=self.repository)
        self.assertEqual(snapshot(self.repository), before)

    def test_symlink_index_is_rejected_without_touching_target(self):
        self.run_import()
        target = self.repository.parent / "outside.md"
        target.write_text("keep me\n")
        self.index.unlink()
        self.index.symlink_to(target)
        before = snapshot(self.repository)
        with self.assertRaises(ImportError):
            build_index_plan(self.archive, repository_root=self.repository)
        self.assertEqual(snapshot(self.repository), before)
        self.assertEqual(target.read_text(), "keep me\n")


if __name__ == "__main__":
    unittest.main()
