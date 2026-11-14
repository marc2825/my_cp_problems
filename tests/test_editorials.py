"""Editorial HTML is converted offline and hand-written Markdown is preserved."""

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from yukicoder.archive import EDITORIAL
from yukicoder.editorial import MARKER, build_editorial_plan

HTML = r'''<div class="block">
<h4 class="shadow">解説</h4>
<h5>想定解</h5>
<p>答えは \(\binom{N}{4}\) です。</p>
\[
x = 1
\]
<p><img src="https://i.example.com/abc/figure.png" alt="図"> <img src="/public/other.png" alt="外部"></p>
<p><a href="/submissions/1">提出</a></p>
</div>'''


class EditorialTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.editorials = root / "editorials"
        self.problems = root / "problems"
        self.directory = self.editorials / "3584_camouflage_mole"
        self.directory.mkdir(parents=True)
        (self.directory / "editorial.html").write_text(HTML)
        (self.directory / "figure.png").write_bytes(b"png")
        (self.problems / "3584_camouflage_mole").mkdir(parents=True)
        (self.problems / "3584_camouflage_mole/metadata.yml").write_text(
            yaml.safe_dump({"platform": "yukicoder", "problem_no": 3584, "title": "Camouflage Mole"}))
        self.output = self.directory / "editorial.md"

    def convert(self):
        plan = build_editorial_plan(self.editorials, self.problems)
        plan.apply()
        return plan

    def test_html_is_converted_to_github_markdown_and_kept(self):
        self.convert()
        markdown = self.output.read_text()
        self.assertTrue(markdown.startswith(MARKER + "\n\n# No.3584 Camouflage Mole\n"))
        self.assertIn("[HTML 版](editorial.html)", markdown)
        self.assertIn("## 解説\n\n### 想定解", markdown)
        self.assertIn(r"答えは $\binom{N}{4}$ です。", markdown)
        self.assertIn("\n$$\nx = 1\n$$\n", markdown)
        self.assertIn("![図](<figure.png>)", markdown)  # Local copy wins.
        self.assertIn("![外部](<https://yukicoder.me/public/other.png>)", markdown)
        self.assertIn("[提出](<https://yukicoder.me/submissions/1>)", markdown)
        self.assertEqual((self.directory / "editorial.html").read_text(), HTML)

    def test_rerun_is_stable_and_follows_html_changes(self):
        self.convert()
        self.assertEqual(self.convert().changes, [])
        (self.directory / "editorial.html").write_text(HTML.replace("想定解", "別解"))
        self.assertEqual(len(self.convert().changes), 1)
        self.assertIn("### 別解", self.output.read_text())

    def test_hand_written_markdown_is_preserved(self):
        self.output.write_text("# 手書きの解説\n")
        plan = self.convert()
        self.assertEqual(plan.preserved, ["editorials/3584_camouflage_mole/editorial.md"])
        self.assertEqual(self.output.read_text(), "# 手書きの解説\n")

    def test_template_problem_editorial_is_linked_once(self):
        problem = self.problems / "3584_camouflage_mole/editorial.md"
        problem.write_text(EDITORIAL)
        self.convert()
        self.assertEqual(problem.read_text(),
                         "# 解説\n\n[解説を読む](../../editorials/3584_camouflage_mole/editorial.md)"
                         "（[HTML 版](../../editorials/3584_camouflage_mole/editorial.html)）\n")
        self.assertEqual(self.convert().changes, [])

    def test_hand_written_problem_editorial_is_not_linked(self):
        problem = self.problems / "3584_camouflage_mole/editorial.md"
        problem.write_text(EDITORIAL.replace("TODO", "自分で書いた方針", 1))
        before = problem.read_bytes()
        self.convert()
        self.assertEqual(problem.read_bytes(), before)

    def test_title_falls_back_to_problem_number(self):
        (self.problems / "3584_camouflage_mole/metadata.yml").unlink()
        self.convert()
        self.assertIn("\n# No.3584\n", self.output.read_text())


if __name__ == "__main__":
    unittest.main()
