"""Missing content gets a destination and an actionable post-run reminder."""

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import import_yukicoder
import check_problem_assets
from test_import_yukicoder import FakeClient, snapshot
from test_yukicoder_assets import AssetClient
from yukicoder.api import ImportError
from yukicoder.manual import build_manual_plan


class ManualReminderTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "archive"
        self.directory = self.root / "3584_camouflage_mole"

    def run_import(self, *args, client=None):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = import_yukicoder.main(["3584", "--output", str(self.root), *args], client=client or FakeClient())
        return code, out.getvalue(), err.getvalue()

    def test_missing_assets_get_directories_and_a_post_run_reminder(self):
        code, out, _ = self.run_import()
        self.assertEqual(code, 0)
        for name in ("editorial", "tests/test_in", "tests/test_out"):
            self.assertEqual((self.directory / name / ".gitkeep").read_bytes(), b"")
        self.assertIn("手動補完リマインド", out)
        for label in ("解説:", "想定解:", "バリデータ:", "テスト:"):
            self.assertIn(label, out)
        self.assertNotIn("チェッカー:", out)

    def test_downloaded_sources_count_as_complete_despite_empty_manual_stubs(self):
        code, out, _ = self.run_import("--with-assets", client=AssetClient())
        self.assertEqual(code, 0)
        self.assertIn("必須の補完項目はありません", out)
        self.assertFalse((self.directory / "editorial").exists())
        self.assertIn("任意:", out)

    def test_dry_run_plans_destinations_and_reminders_without_writing(self):
        code, out, _ = self.run_import("--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("MANUAL CREATE 3584_camouflage_mole/editorial/.gitkeep", out)
        self.assertIn("実行後の予定", out)
        self.assertIn("解説:", out)
        self.assertFalse(self.root.exists())

    def test_default_repository_uses_existing_editorial_layout(self):
        repository = Path(self.temporary.name) / "repository"
        repository.mkdir()
        (repository / "README.md").write_text("# Repository\n")
        archive = repository / "problems/yukicoder"
        with patch.object(import_yukicoder, "ROOT", repository), redirect_stdout(io.StringIO()):
            self.assertEqual(import_yukicoder.main(["3584", "--output", str(archive)], client=FakeClient()), 0)
        destination = repository / "editorials/yukicoder/3584_camouflage_mole"
        self.assertTrue((destination / ".gitkeep").exists())
        self.assertFalse((archive / "3584_camouflage_mole/editorial").exists())

    def test_linked_editorial_body_is_recognized_and_broken_link_is_pending(self):
        self.run_import()
        html = self.directory / "editorial/editorial.html"
        html.write_text("<h1>解説</h1><p>数学的な説明があります。</p>")
        (self.directory / "editorial.md").write_text("# 解説\n\n[本文](editorial/editorial.html)\n")
        _, statuses = build_manual_plan(self.root)
        self.assertFalse(any(item.startswith("解説:") for item in statuses[0].required))
        html.write_text("<html><head><title>空の原稿</title></head><body></body></html>")
        _, statuses = build_manual_plan(self.root)
        self.assertTrue(any(item.startswith("解説:") for item in statuses[0].required))

    def test_missing_test_partner_is_reported_by_name(self):
        self.run_import("--with-assets", client=AssetClient())
        (self.directory / "tests/test_out/01.txt").unlink()
        _, statuses = build_manual_plan(self.root)
        self.assertEqual(len(statuses[0].required), 1)
        self.assertIn("tests/test_out/", statuses[0].required[0])
        self.assertIn("01.txt", statuses[0].required[0])

    def test_special_judge_requires_manual_checker_until_code_is_added(self):
        client = AssetClient()
        client.html = client.html.replace("標準ジャッジ問題", "スペシャルジャッジ問題")
        code, out, _ = self.run_import("--with-assets", client=client)
        self.assertEqual(code, 0)
        self.assertTrue((self.directory / "checker/.gitkeep").exists())
        self.assertIn("チェッカー:", out)
        (self.directory / "checker/main.cpp").write_text("int main() { return 0; }\n")
        _, statuses = build_manual_plan(self.root)
        self.assertFalse(statuses[0].required)

    def test_manual_preparation_preserves_existing_files_on_repeat(self):
        self.run_import()
        before = snapshot(self.root)
        plan, _ = build_manual_plan(self.root)
        self.assertFalse(plan.changes)
        plan.apply()
        self.assertEqual(snapshot(self.root), before)

    def test_offline_check_is_read_only_and_prepare_dirs_can_restore_destinations(self):
        self.run_import()
        destination = self.directory / "editorial"
        (destination / ".gitkeep").unlink()
        destination.rmdir()
        before = snapshot(self.root)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(check_problem_assets.main(["--output", str(self.root)]), 0)
        self.assertEqual(snapshot(self.root), before)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(check_problem_assets.main(["--output", str(self.root), "--prepare-dirs"]), 0)
        self.assertTrue((destination / ".gitkeep").exists())

    def test_symlink_editorial_destination_is_rejected_without_writes(self):
        self.run_import()
        destination = self.directory / "editorial"
        (destination / ".gitkeep").unlink()
        destination.rmdir()
        outside = Path(self.temporary.name) / "outside"
        outside.mkdir()
        destination.symlink_to(outside, target_is_directory=True)
        before = snapshot(self.root)
        with self.assertRaises(ImportError):
            build_manual_plan(self.root)
        self.assertEqual(snapshot(self.root), before)
        self.assertFalse(list(outside.iterdir()))


if __name__ == "__main__":
    unittest.main()
