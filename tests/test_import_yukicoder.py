"""Offline tests; fixtures are synthetic and no network access is used."""

import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from import_yukicoder import main
from yukicoder.api import Client, ImportError, Unavailable
from yukicoder.archive import slug
from yukicoder.markdown import to_markdown
from yukicoder.html import to_html
from yukicoder.parser import parse_page
from bs4 import BeautifulSoup

PROBLEM = {
    "No": 3584, "ProblemId": 13242, "Title": "Camouflage Mole", "AuthorId": 17084,
    "TesterIds": "16208", "Date": "2026-07-10T21:20:00+09:00", "ContestId": 600,
    "Level": 1.5, "Tags": "public tag", "ProblemType": 0,
}
# The separate wrappers match a layout found on the actual public pages.
PAGE = r'''<html><div id="content" data-problem-id="13242">
<h3>No.3584 Camouflage Mole</h3>
<div class="problem-header-main">実行時間制限 : 1ケース 2.000秒 / メモリ制限 : 1024 MB / 標準ジャッジ問題</div>
<a href="/contests/600">contest</a>
<div>問題文最終更新日: 2026-08-29 00:42:22</div>
<div class="wrapper">
<div><h4>問題文</h4><p>十分な長さのテスト用問題文です。\(A_i \le N\) を保持する。</p>
<p>\[
\sum_{i=1}^{N} A_i
\]</p></div>
<div><h4>制約</h4><ul><li>\(1 \le N \le 100\)</li></ul></div>
<div><h4>入力</h4><pre>$N$</pre></div>
<div><h4>出力</h4><p>答えを出力する。</p></div></div>
<div><h4>サンプル</h4><div><h5>サンプル1</h5><h6>入力</h6><pre>4
 5

</pre><h6>出力</h6><pre>1</pre></div></div>
<form><input value="secret"/></form><div class="modal"><h5>UI modal</h5></div>
</div></html>'''


class FakeClient(Client):
    def __init__(self):
        super().__init__(interval=0)
        self.values = {
            "/api/v1/problems/no/3584": copy.deepcopy(PROBLEM),
            "/api/v1/user/id/17084": {"Id": 17084, "Name": "marc2825"},
            "/api/v1/contest/id/600": {"Id": 600, "Name": "yukicoder contest 504"},
            "/api/v1/problems": [copy.deepcopy(PROBLEM)],
        }
        self.html = PAGE

    def json(self, path):
        value = self.values.get(path, Unavailable("HTTP 404"))
        if isinstance(value, Exception):
            raise value
        return copy.deepcopy(value)

    def text(self, path):
        if isinstance(self.html, Exception):
            raise self.html
        return self.html


def snapshot(root):
    return {str(p.relative_to(root)): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in root.rglob("*") if p.is_file()}


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "archive"
        self.client = FakeClient()

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main([*args, "--output", str(self.root)], client=self.client)
        return code, out.getvalue(), err.getvalue()

    @property
    def directory(self):
        return self.root / "3584_camouflage_mole"

    def test_import_and_repeat_are_byte_and_mtime_identical(self):
        self.assertEqual(self.run_cli("3584")[0], 0)
        directory = self.directory
        self.assertTrue((directory / "tests/test_in/.gitkeep").exists())
        self.assertTrue((directory / "tests/test_out/.gitkeep").exists())
        self.assertFalse((directory / "tests/manual").exists())
        self.assertFalse((directory / "solution/.gitkeep").exists())
        self.assertFalse((directory / "validator/.gitkeep").exists())
        for name in ("solution/main.cpp", "solution/main.py", "validator/main.cpp"):
            self.assertEqual((directory / name).read_bytes(), b"")
        self.assertFalse((directory / "wrong").exists())
        self.assertFalse((directory / "generator").exists())
        self.assertFalse((directory / "checker").exists())
        self.assertTrue((directory / "statement.html").exists())
        metadata = yaml.safe_load((directory / "metadata.yml").read_text())
        self.assertEqual(metadata["time_limit_ms"], 2000)
        self.assertEqual(metadata["memory_limit_mb"], 1024)
        self.assertEqual(metadata["author"], "marc2825")
        self.assertEqual(metadata["difficulty"], 1.5)
        self.assertEqual(metadata["source"]["level"], 1.5)
        self.assertNotIn("intended_complexity", metadata)
        self.assertEqual(metadata["tags"], [])
        before = snapshot(self.root)
        code, out, _ = self.run_cli("3584")
        self.assertEqual(code, 0)
        self.assertNotIn("UPDATE", out)
        self.assertEqual(before, snapshot(self.root))
        self.assertFalse((directory / "wrong").exists())
        self.assertFalse((directory / "generator").exists())
        self.assertFalse((directory / "checker").exists())

        self.assertFalse((directory / "tests/manual").exists())

    def test_checker_is_created_only_for_confirmed_special_judge(self):
        self.client.html = PAGE.replace("標準ジャッジ問題", "スペシャルジャッジ問題")
        code, out, _ = self.run_cli("3584", "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("CREATE checker/.gitkeep", out)
        self.assertFalse(self.root.exists())
        self.assertEqual(self.run_cli("3584")[0], 0)
        self.assertTrue((self.directory / "checker/.gitkeep").is_file())
        metadata = yaml.safe_load((self.directory / "metadata.yml").read_text())
        self.assertIsNone(metadata["judge_type"])
        self.assertEqual(metadata["source"]["judge_type"], "special")
        # An empty checker/ is not linked until it contains code.
        self.assertNotIn("checker/", (self.directory / "README.md").read_text())
        (self.directory / "checker/main.cpp").write_text("int main() {}\n")
        self.assertEqual(self.run_cli("3584")[0], 0)
        self.assertIn("| [checker/main.cpp](checker/main.cpp) | チェッカー（C++） |",
                      (self.directory / "README.md").read_text())

    def test_unknown_judge_does_not_create_checker(self):
        self.client.html = PAGE.replace("標準ジャッジ問題", "")
        code, out, err = self.run_cli("3584")
        self.assertEqual(code, 0)
        self.assertFalse((self.directory / "checker").exists())
        self.assertNotIn("checker/", (self.directory / "README.md").read_text())
        self.assertIn("ジャッジ形式", err)

    def test_manual_special_judge_overrides_public_standard(self):
        self.run_cli("3584")
        path = self.directory / "metadata.yml"
        metadata = yaml.safe_load(path.read_text())
        metadata["judge_type"] = "special"
        path.write_text(yaml.safe_dump(metadata, allow_unicode=True))
        self.assertEqual(self.run_cli("3584")[0], 0)
        self.assertTrue((self.directory / "checker/.gitkeep").is_file())
        self.assertEqual(yaml.safe_load(path.read_text())["judge_type"], "special")

    def test_manual_standard_overrides_public_special(self):
        self.run_cli("3584")
        path = self.directory / "metadata.yml"
        metadata = yaml.safe_load(path.read_text())
        metadata["judge_type"] = "standard"
        path.write_text(yaml.safe_dump(metadata, allow_unicode=True))
        self.client.html = PAGE.replace("標準ジャッジ問題", "スペシャルジャッジ問題")
        self.assertEqual(self.run_cli("3584")[0], 0)
        self.assertFalse((self.directory / "checker").exists())
        self.assertNotIn("checker/", (self.directory / "README.md").read_text())

    def test_dry_run_creates_nothing_and_reports_updates(self):
        code, out, _ = self.run_cli("--user", "17084", "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("NEW 3584_camouflage_mole", out)
        self.assertIn("CREATE statement.md", out)
        self.assertIn("CREATE statement.html", out)
        self.assertFalse(self.root.exists())
        self.run_cli("3584")
        before = snapshot(self.root)
        self.client.html = PAGE.replace("答えを出力する。", "新しい答えを出力する。")
        code, out, _ = self.run_cli("3584", "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("UPDATE statement.md", out)
        self.assertIn("UPDATE statement.html", out)
        self.assertEqual(before, snapshot(self.root))

    def test_all_manual_files_and_metadata_values_survive_refresh(self):
        self.run_cli("3584")
        paths = ["editorial.md", "solution/main.cpp", "solution/main.py", "solution/brute.cpp",
                 "validator/main.cpp", "checker/main.cpp", "tests/01.in"]
        for name in paths:
            (self.directory / name).parent.mkdir(parents=True, exist_ok=True)
            (self.directory / name).write_text("manual content: " + name)
        metadata_path = self.directory / "metadata.yml"
        metadata = yaml.safe_load(metadata_path.read_text())
        manual = {"difficulty": "hard", "tags": ["DP", "数え上げ"],
                  "judge_type": "special", "notes": {"custom": "keep"}}
        metadata.update(manual)
        metadata_path.write_text(yaml.safe_dump(metadata, allow_unicode=True))
        before = {p: (self.directory / p).read_bytes() for p in paths}
        self.client.html = PAGE.replace("2.000秒", "3.000秒")
        self.assertEqual(self.run_cli("3584")[0], 0)
        after = yaml.safe_load(metadata_path.read_text())
        self.assertEqual(after["time_limit_ms"], 3000)
        for key, value in manual.items():
            self.assertEqual(after[key], value)
        for name, content in before.items():
            self.assertEqual((self.directory / name).read_bytes(), content)
        readme = (self.directory / "README.md").read_text()
        self.assertIn("| [solution/brute.cpp](solution/brute.cpp) | 愚直解（C++） |", readme)
        self.assertIn("| [tests/](tests/) | テストケース（1 件） |", readme)
        self.assertIn("- 難易度: hard", readme)

    def test_empty_difficulty_is_filled_when_level_becomes_available(self):
        problem = self.client.values["/api/v1/problems/no/3584"]
        problem.pop("Level")
        self.assertEqual(self.run_cli("3584")[0], 0)
        path = self.directory / "metadata.yml"
        self.assertIsNone(yaml.safe_load(path.read_text())["difficulty"])
        before = snapshot(self.root)
        problem["Level"] = 2.5
        code, out, _ = self.run_cli("3584", "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("UPDATE metadata.yml", out)
        self.assertEqual(before, snapshot(self.root))
        self.assertEqual(self.run_cli("3584")[0], 0)
        self.assertEqual(yaml.safe_load(path.read_text())["difficulty"], 2.5)

    def test_existing_numeric_difficulty_is_preserved_and_api_level_is_recorded(self):
        self.run_cli("3584")
        path = self.directory / "metadata.yml"
        metadata = yaml.safe_load(path.read_text())
        metadata["difficulty"] = 0
        path.write_text(yaml.safe_dump(metadata, allow_unicode=True))
        self.client.values["/api/v1/problems/no/3584"]["Level"] = 3.5
        self.assertEqual(self.run_cli("3584")[0], 0)
        metadata = yaml.safe_load(path.read_text())
        self.assertEqual(metadata["difficulty"], 0)
        self.assertEqual(metadata["source"]["level"], 3.5)

    def test_legacy_intended_complexity_is_removed_and_does_not_reappear(self):
        self.run_cli("3584")
        path = self.directory / "metadata.yml"
        metadata = yaml.safe_load(path.read_text())
        metadata["intended_complexity"] = "O(N)"
        path.write_text(yaml.safe_dump(metadata, allow_unicode=True))
        self.assertEqual(self.run_cli("3584")[0], 0)
        self.assertNotIn("intended_complexity", yaml.safe_load(path.read_text()))
        before = snapshot(self.root)
        self.assertEqual(self.run_cli("3584")[0], 0)
        self.assertEqual(before, snapshot(self.root))

    def test_manual_edits_to_generated_files_are_protected(self):
        self.run_cli("3584")
        for name in ("README.md", "statement.md", "statement.html"):
            (self.directory / name).write_text("hand edited " + name)
        self.client.html = PAGE.replace("2.000秒", "3.000秒")
        code, out, _ = self.run_cli("3584")
        self.assertEqual(code, 0)
        self.assertIn("PRESERVE README.md", out)
        self.assertIn("PRESERVE statement.md", out)
        self.assertIn("PRESERVE statement.html", out)
        self.assertEqual((self.directory / "statement.md").read_text(), "hand edited statement.md")
        self.assertEqual((self.directory / "statement.html").read_text(), "hand edited statement.html")

    def test_add_html_to_existing_archive_without_changing_markdown_or_manual_files(self):
        self.run_cli("3584")
        html_path = self.directory / "statement.html"
        html_path.unlink()
        state_path = self.directory / ".import-state.json"
        state = json.loads(state_path.read_text())
        del state["files"]["statement.html"]
        state_path.write_text(json.dumps(state))
        before = snapshot(self.root)
        code, out, _ = self.run_cli("3584", "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("CREATE statement.html", out)
        self.assertEqual(before, snapshot(self.root))
        self.assertEqual(self.run_cli("3584")[0], 0)
        for name, info in before.items():
            if not name.endswith(".import-state.json"):
                self.assertEqual(snapshot(self.root)[name], info)
        self.assertTrue(html_path.exists())

    def test_unmanaged_existing_html_is_not_overwritten(self):
        self.directory.mkdir(parents=True)
        html_path = self.directory / "statement.html"
        html_path.write_text("<html>My own statement</html>")
        code, out, _ = self.run_cli("3584")
        self.assertEqual(code, 0)
        self.assertIn("PRESERVE statement.html", out)
        self.assertEqual(html_path.read_text(), "<html>My own statement</html>")

    def test_unmanaged_existing_files_are_not_adopted(self):
        self.directory.mkdir(parents=True)
        (self.directory / "README.md").write_text("existing README")
        code, out, _ = self.run_cli("3584")
        self.assertEqual(code, 0)
        self.assertIn("PRESERVE README.md", out)
        self.assertEqual((self.directory / "README.md").read_text(), "existing README")

    def test_changed_title_reuses_existing_directory(self):
        self.run_cli("3584")
        self.client.values["/api/v1/problems/no/3584"]["Title"] = "A Different Title"
        self.assertEqual(self.run_cli("3584")[0], 0)
        self.assertEqual([p.name for p in self.root.iterdir() if p.is_dir()], [self.directory.name])

    def test_corrupt_metadata_and_identity_conflicts_do_not_change_files(self):
        self.run_cli("3584")
        for text in ("difficulty: [", "title: a\ntitle: b\n", "problem_no: 99\n"):
            (self.directory / "metadata.yml").write_text(text)
            before = snapshot(self.root)
            self.assertEqual(self.run_cli("3584")[0], 1)
            self.assertEqual(before, snapshot(self.root))

    def test_duplicate_directories_and_symlinks_are_rejected(self):
        self.run_cli("3584")
        other = self.root / "3584_other"
        other.mkdir()
        before = snapshot(self.root)
        self.assertEqual(self.run_cli("3584")[0], 1)
        self.assertEqual(before, snapshot(self.root))
        other.rmdir()
        target = Path(self.temporary.name) / "outside.cpp"
        target.write_text("keep")
        (self.directory / "editorial.md").unlink()
        (self.directory / "editorial.md").symlink_to(target)
        self.assertEqual(self.run_cli("3584")[0], 1)
        self.assertEqual(target.read_text(), "keep")

    def test_missing_optional_fields_preserve_existing_values(self):
        self.run_cli("3584")
        self.client.values["/api/v1/problems/no/3584"]["Date"] = None
        self.client.values["/api/v1/contest/id/600"] = ImportError("temporary failure")
        self.client.html = PAGE.replace("2.000秒", "unknown").replace("1024 MB", "unknown")
        code, _, err = self.run_cli("3584")
        self.assertEqual(code, 0)
        self.assertIn("WARNING", err)
        metadata = yaml.safe_load((self.directory / "metadata.yml").read_text())
        self.assertEqual(metadata["published_at"], PROBLEM["Date"])
        self.assertEqual(metadata["time_limit_ms"], 2000)
        self.assertEqual(metadata["contest"], "yukicoder contest 504")

    def test_changed_html_keeps_statement_and_imports_partial_metadata(self):
        self.run_cli("3584")
        before = (self.directory / "statement.md").read_bytes()
        before_html = (self.directory / "statement.html").read_bytes()
        self.client.html = "<html>unexpected login or changed page</html>"
        code, out, err = self.run_cli("3584")
        self.assertEqual(code, 1)
        self.assertIn("PARTIAL", out)
        self.assertIn("問題文", err)
        self.assertEqual((self.directory / "statement.md").read_bytes(), before)
        self.assertEqual((self.directory / "statement.html").read_bytes(), before_html)

    def test_no_statement_is_fabricated_after_network_failure(self):
        self.client.html = ImportError("network error")
        code, out, _ = self.run_cli("3584")
        self.assertEqual(code, 1)
        self.assertIn("PARTIAL", out)
        self.assertTrue((self.directory / "metadata.yml").exists())
        self.assertFalse((self.directory / "statement.md").exists())
        self.assertFalse((self.directory / "statement.html").exists())

    def test_private_missing_and_future_problems_make_no_files(self):
        for value in (Unavailable("HTTP 404"), {**PROBLEM, "WIP": True},
                      {**PROBLEM, "Date": "2099-01-01T00:00:00+09:00"}):
            self.client.values["/api/v1/problems/no/3584"] = value
            code, _, err = self.run_cli("3584", "--dry-run")
            self.assertEqual(code, 1)
            self.assertIn("SKIP No.3584", err)
            self.assertFalse(self.root.exists())

    def test_one_batch_failure_does_not_stop_other_problems(self):
        self.client.values["/api/v1/problems"] = [{**PROBLEM, "No": 1}, PROBLEM,
                                                   {**PROBLEM, "No": 2, "AuthorId": 99}]
        code, out, err = self.run_cli("--user", "17084")
        self.assertEqual(code, 1)
        self.assertIn("2 problem(s)", out)
        self.assertIn("SKIP No.1", err)
        self.assertTrue((self.directory / "statement.md").exists())

    def test_invalid_api_shape_is_reported(self):
        self.client.values["/api/v1/problems/no/3584"] = {"new_schema": True}
        code, _, err = self.run_cli("3584")
        self.assertEqual(code, 1)
        self.assertIn("API", err)
        self.assertFalse(self.root.exists())


class ParserTests(unittest.TestCase):
    def test_wrappers_math_samples_and_ui_exclusion(self):
        markdown, html, info, warnings = parse_page(PAGE, 3584, 13242)
        # GitHub renders only $...$ and $$...$$ delimiters.
        self.assertIn(r"$A_i \le N$", markdown)
        self.assertIn("\n\n$$\n\\sum_{i=1}^{N} A_i\n$$\n\n", markdown)
        self.assertIn(r"- $1 \le N \le 100$", markdown)
        self.assertNotIn(r"\(", markdown)
        self.assertIn("```text\n4\n 5\n\n```", markdown)
        self.assertIn("### サンプル1", markdown)
        self.assertNotIn("secret", markdown)
        self.assertNotIn("UI modal", markdown)
        saved = BeautifulSoup(html, "html.parser")
        self.assertEqual(saved.find("base")["href"], "https://yukicoder.me/problems/no/3584")
        self.assertEqual(saved.find("title").get_text(), "No.3584 Camouflage Mole")
        self.assertIn(r"\(A_i \le N\)", saved.find("main").get_text())
        self.assertIn("4\n 5\n\n", [p.get_text() for p in saved.find_all("pre")])
        self.assertNotIn("secret", html)
        self.assertNotIn("UI modal", html)
        self.assertIn("mathjax@3.2.2", html)
        self.assertEqual(info["memory_limit_mb"], 1024)
        self.assertEqual(warnings, [])

    def test_relative_image_links_and_complex_tables(self):
        html = '''<div><p><img src="/public/test.png" alt="図"/></p>
<table onclick="evil()"><tr><td rowspan="2">a</td></tr>
<tr><td><a href="/wiki">link</a></td></tr><script>evil()</script></table></div>'''
        markdown = to_markdown([BeautifulSoup(html, "html.parser").div], "https://yukicoder.me/problems/no/3584")
        self.assertIn("![図](<https://yukicoder.me/public/test.png>)", markdown)
        self.assertIn('rowspan="2"', markdown)
        self.assertIn('href="https://yukicoder.me/wiki"', markdown)
        self.assertNotIn("evil", markdown)

    def test_simple_tables_become_github_tables(self):
        html = """<div><table border="1"><thead><tr><th>&nbsp;状態&nbsp;</th><th>\\( a | b \\)</th></tr></thead>
<tbody><tr><td>状態 0</td><td><b>2</b></td></tr></tbody></table></div>"""
        markdown = to_markdown([BeautifulSoup(html, "html.parser").div], "https://yukicoder.me")
        self.assertEqual(markdown, "| 状態 | $a \\| b$ |\n| --- | --- |\n| 状態 0 | **2** |\n")

    def test_inline_math_is_kept_on_one_line(self):
        html = "<div><p>値 \\(\n  N +\n  1 \\) と $ M $</p></div>"
        markdown = to_markdown([BeautifulSoup(html, "html.parser").div], "https://yukicoder.me")
        self.assertEqual(markdown, "値 $N + 1$ と $M$\n")

    def test_code_fence_delimiter_and_whitespace_are_preserved(self):
        html = "<div><pre>```\n a  \n\n\n</pre></div>"
        markdown = to_markdown([BeautifulSoup(html, "html.parser").div], "https://yukicoder.me")
        self.assertIn("````text\n```\n a  \n\n\n````", markdown)

    def test_wrong_id_and_missing_input_sections_fail_closed(self):
        for html in (PAGE.replace('data-problem-id="13242"', 'data-problem-id="1"'),
                     PAGE.replace("<h4>入力</h4>", "<h4>other</h4>")):
            with self.assertRaises(ImportError):
                parse_page(html, 3584, 13242)

    def test_safe_slugs(self):
        self.assertEqual(slug("Make Ends Meet (Easy)"), "make_ends_meet_easy")
        self.assertEqual(slug("../bad: title/?*"), "bad_title")
        self.assertEqual(slug("日本語 title"), "")
        self.assertEqual(slug("/\\:*?"), "")

    def test_html_preserves_original_markup_and_escapes_title(self):
        fragment = '''<div class="block" style="text-align: center"><h4>問題文</h4>
<table><tr><td rowspan="2"><em>content</em></td></tr></table>
<img src="/public/test.png" alt="図"/><pre>  a\n\nb\n</pre></div>'''
        block = BeautifulSoup(fragment, "html.parser").div
        html = to_html([block], 3584, 13242, 'A <script>alert("x")</script> & B')
        saved = BeautifulSoup(html, "html.parser")
        self.assertEqual(str(saved.main.find("div")), str(block))
        self.assertEqual(saved.main.find("pre").get_text(), "  a\n\nb\n")
        self.assertEqual(saved.main.find("img")["src"], "/public/test.png")
        self.assertEqual(saved.title.get_text(), 'No.3584 A <script>alert("x")</script> & B')
        self.assertIsNone(saved.h1.find("script"))


class NetworkTests(unittest.TestCase):
    def test_network_errors_are_retried_without_authentication(self):
        with patch("yukicoder.api.urlopen", side_effect=URLError("DNS")) as mocked, patch("yukicoder.api.time.sleep"):
            with self.assertRaises(ImportError):
                Client(interval=0).text("/api/v1/problems")
            self.assertEqual(mocked.call_count, 3)
            request = mocked.call_args.args[0]
            self.assertFalse(request.has_header("Authorization"))
            self.assertFalse(request.has_header("Cookie"))

    def test_private_response_is_not_retried(self):
        error = HTTPError("https://yukicoder.me", 403, "Forbidden", {}, None)
        with patch("yukicoder.api.urlopen", side_effect=error) as mocked, patch("yukicoder.api.time.sleep"):
            with self.assertRaises(Unavailable):
                Client(interval=0).text("/api/v1/problems/no/1")
            self.assertEqual(mocked.call_count, 1)


if __name__ == "__main__":
    unittest.main()
