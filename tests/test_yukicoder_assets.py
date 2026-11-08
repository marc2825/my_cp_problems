"""Offline checks for authenticated archives; all credentials and pages are synthetic."""

import io
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import Mock

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from import_yukicoder import main
from test_import_yukicoder import FakeClient, snapshot
from yukicoder.api import Client, ImportError, SameOriginRedirect, Unavailable
from yukicoder.assets import extension, unpack_tests


EDITORIAL = r'''<html><head><meta name="csrf-token" content="private-token"></head>
<div id="content" data-problem-id="13242">
<h4>解説</h4><div class="editorial"><p>数学的な解説。\(N\)</p><pre>  a\n b</pre></div>
<form><input value="private-token"><button>保存</button></form>
<script>privateCode()</script><div id="ai_questions">private discussion</div>
<h4>想定解</h4><table><tr><td><a href="/submissions/10">10</a></td></tr>
<tr><td><a href="/submissions/11">11</a></td></tr></table>
<h4>その他</h4><a href="/submissions/99">未登録の提出</a></div></html>'''


def submission(sid, language="C++17", user=17084, pid=13242):
    return f'''<div id="content" data-problem-id="{pid}" data-submission-id="{sid}">
<table class="submission-info-table"><tr><td>ユーザー</td><td><a href="/users/{user}">name</a></td></tr>
<tr><td>言語</td><td>{language}<br>(compiler version)</td></tr></table></div>'''


def zip_data(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    return buffer.getvalue()


class AssetClient(FakeClient):
    def __init__(self):
        super().__init__()
        self.pages = {
            "/problems/no/3584/editorial": EDITORIAL,
            "/submissions/10": submission(10),
            "/submissions/11": submission(11, "PyPy3", 16208),
        }
        self.downloads = {
            "/submissions/10/source": b"int main() { return 0; }\n",
            "/submissions/11/source": b"print(1)\n",
            "/api/v1/problems/13242/testcase.zip": zip_data({
                "test_in/00.txt": b" 1\r\n\x00\xff\n", "test_out/00.txt": b"1\n",
                "test_in/01.txt": b"2\n", "test_out/01.txt": b"2\n",
            }),
        }
        self.values["/api/v1/problems/13242/validator"] = {"langId": "cpp17", "source": "// validator\n"}
        self.requests = []

    def text(self, path):
        self.requests.append(path)
        if path in self.pages:
            value = self.pages[path]
            if isinstance(value, Exception):
                raise value
            return value
        return super().text(path)

    def data(self, path):
        self.requests.append(path)
        value = self.downloads.get(path, Unavailable("HTTP 403"))
        if isinstance(value, Exception):
            raise value
        return value


class AssetImportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "archive"
        self.directory = self.root / "3584_camouflage_mole"
        self.client = AssetClient()

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(["3584", "--output", str(self.root), *args], client=self.client)
        return code, out.getvalue(), err.getvalue()

    def test_full_archive_preserves_bytes_and_repeats_without_writes(self):
        self.assertEqual(self.run_cli("--with-assets")[0], 0)
        self.assertEqual((self.directory / "tests/test_in/00.txt").read_bytes(), b" 1\r\n\x00\xff\n")
        self.assertEqual((self.directory / "solution/10.cpp").read_bytes(), self.client.downloads["/submissions/10/source"])
        self.assertEqual((self.directory / "solution/11.py").read_bytes(), b"print(1)\n")
        self.assertEqual((self.directory / "validator/main.cpp").read_bytes(), b"// validator\n")
        self.assertNotIn("/submissions/99", self.client.requests)
        saved = (self.directory / "editorial.html").read_text()
        self.assertIn(r"\(N\)", saved)
        self.assertNotIn("private-token", saved)
        self.assertNotIn("privateCode", saved)
        self.assertNotIn("private discussion", saved)
        self.assertNotIn('<form', saved)
        metadata = yaml.safe_load((self.directory / "metadata.yml").read_text())
        self.assertIn("solution/10.cpp", metadata["source"]["asset_urls"])
        self.assertFalse((self.directory / "tests/.gitkeep").exists())
        before = snapshot(self.root)
        self.assertEqual(self.run_cli("--with-assets")[0], 0)
        self.assertEqual(snapshot(self.root), before)

    def test_dry_run_downloads_and_plans_every_asset_without_writing(self):
        code, out, _ = self.run_cli("--with-assets", "--dry-run")
        self.assertEqual(code, 0)
        for name in ("editorial.html", "solution/10.cpp", "validator/main.cpp", "tests/test_out/01.txt"):
            self.assertIn("CREATE " + name, out)
        self.assertFalse(self.root.exists())

    def test_existing_manual_assets_survive_and_unedited_assets_refresh(self):
        self.run_cli("--with-assets")
        for name in ("editorial.html", "validator/main.cpp", "tests/test_in/00.txt", "solution/10.cpp"):
            (self.directory / name).write_bytes(b"manually edited\n")
        self.client.downloads["/submissions/11/source"] = b"print(2)\n"
        self.assertEqual(self.run_cli("--with-assets")[0], 0)
        for name in ("editorial.html", "validator/main.cpp", "tests/test_in/00.txt", "solution/10.cpp"):
            self.assertEqual((self.directory / name).read_bytes(), b"manually edited\n")
        self.assertEqual((self.directory / "solution/11.py").read_bytes(), b"print(2)\n")

    def test_upgrade_fills_empty_validator_but_preserves_existing_code(self):
        self.run_cli()
        (self.directory / "solution/main.cpp").write_bytes(b"my solution\n")
        (self.directory / "editorial.md").write_text("my editorial\n")
        self.assertEqual(self.run_cli("--with-assets")[0], 0)
        self.assertEqual((self.directory / "validator/main.cpp").read_bytes(), b"// validator\n")
        self.assertEqual((self.directory / "solution/main.cpp").read_bytes(), b"my solution\n")
        self.assertEqual((self.directory / "editorial.md").read_text(), "my editorial\n")

    def test_clearing_an_imported_validator_is_preserved_as_a_manual_edit(self):
        self.run_cli("--with-assets")
        path = self.directory / "validator/main.cpp"
        path.write_bytes(b"")
        code, out, _ = self.run_cli("--with-assets")
        self.assertEqual(code, 0)
        self.assertIn("PRESERVE validator/main.cpp", out)
        self.assertEqual(path.read_bytes(), b"")

    def test_user_filter_uses_registered_submission_owner(self):
        self.assertEqual(self.run_cli("--with-assets", "--solution-user", "17084")[0], 0)
        self.assertTrue((self.directory / "solution/10.cpp").exists())
        self.assertFalse((self.directory / "solution/11.py").exists())
        self.assertNotIn("/submissions/11/source", self.client.requests)

    def test_login_screen_and_forbidden_download_are_partial_not_success(self):
        self.client.pages["/problems/no/3584/editorial"] = EDITORIAL.replace("数学的な解説。", "現在解説は表示することはできません")
        self.client.downloads["/api/v1/problems/13242/testcase.zip"] = Unavailable("HTTP 403")
        code, out, err = self.run_cli("--with-assets")
        self.assertEqual(code, 1)
        self.assertIn("PARTIAL", out)
        self.assertIn("Cookie", err)
        self.assertTrue((self.directory / "statement.md").exists())
        self.assertTrue((self.directory / "validator/main.cpp").exists())
        self.assertFalse((self.directory / "editorial.html").exists())

    def test_token_can_fetch_editorial_source_without_html_session(self):
        self.client.token = "synthetic-secret"
        self.client.pages["/problems/no/3584/editorial"] = Unavailable("HTTP 403")
        self.client.values["/api/v1/problems/13242/editorial"] = {"content": "# Original editorial\n", "isMarkdown": True}
        code, out, err = self.run_cli("--with-assets")
        self.assertEqual(code, 1)  # Registered solutions still require the visible HTML list.
        self.assertIn("想定解", err)
        self.assertNotIn("synthetic-secret", out + err)
        self.assertEqual((self.directory / "editorial.source.md").read_text(), "# Original editorial\n")

    def test_wrong_problem_submission_is_not_saved(self):
        self.client.pages["/submissions/10"] = submission(10, pid=999)
        self.assertEqual(self.run_cli("--with-assets")[0], 1)
        self.assertFalse((self.directory / "solution/10.cpp").exists())
        self.assertTrue((self.directory / "solution/11.py").exists())

    def test_html_login_response_is_not_saved_as_source(self):
        self.client.downloads["/submissions/10/source"] = b"<!doctype html><html>Login</html>"
        self.assertEqual(self.run_cli("--with-assets")[0], 1)
        self.assertFalse((self.directory / "solution/10.cpp").exists())

    def test_invalid_zip_does_not_create_partial_test_files(self):
        self.client.downloads["/api/v1/problems/13242/testcase.zip"] = zip_data({"test_in/valid.txt": b"1\n", "../escape": b"evil"})
        self.assertEqual(self.run_cli("--with-assets")[0], 1)
        self.assertFalse((self.directory / "tests/test_in/valid.txt").exists())
        self.assertFalse((self.directory / "escape").exists())

    def test_test_tab_list_downloads_are_used_when_zip_is_forbidden(self):
        self.client.downloads["/api/v1/problems/13242/testcase.zip"] = Unavailable("HTTP 403")
        for which in ("in", "out"):
            self.client.values[f"/api/v1/problems/13242/file/{which}"] = ["01.txt"]
            self.client.downloads[f"/api/v1/problems/13242/file/{which}/01.txt"] = b" 12\r\n\n"
        self.assertEqual(self.run_cli("--with-assets")[0], 0)
        self.assertEqual((self.directory / "tests/test_in/01.txt").read_bytes(), b" 12\r\n\n")
        self.assertEqual((self.directory / "tests/test_out/01.txt").read_bytes(), b" 12\r\n\n")

    def test_list_download_failure_keeps_existing_tests_untouched(self):
        self.run_cli("--with-assets")
        before = (self.directory / "tests/test_in/00.txt").read_bytes()
        self.client.downloads["/api/v1/problems/13242/testcase.zip"] = Unavailable("HTTP 403")
        self.client.values["/api/v1/problems/13242/file/in"] = ["00.txt", "missing.txt"]
        self.client.downloads["/api/v1/problems/13242/file/in/00.txt"] = b"new\n"
        self.assertEqual(self.run_cli("--with-assets")[0], 1)
        self.assertEqual((self.directory / "tests/test_in/00.txt").read_bytes(), before)

    def test_symlink_asset_parent_is_rejected_before_any_writes(self):
        self.run_cli()
        outside = Path(self.temporary.name) / "outside"
        outside.mkdir()
        (self.directory / "tests/test_in/.gitkeep").unlink()
        (self.directory / "tests/test_in").rmdir()
        (self.directory / "tests/test_in").symlink_to(outside, target_is_directory=True)
        before = snapshot(self.root)
        self.assertEqual(self.run_cli("--with-assets")[0], 1)
        self.assertEqual(snapshot(self.root), before)
        self.assertEqual(list(outside.iterdir()), [])

    def test_unregistered_validator_is_not_reported_as_a_failure(self):
        self.client.values["/api/v1/problems/13242/validator"] = {"langId": "", "source": ""}
        self.assertEqual(self.run_cli("--with-assets")[0], 0)
        self.assertEqual((self.directory / "validator/main.cpp").read_bytes(), b"")


class AssetTransportTests(unittest.TestCase):
    def test_token_only_goes_to_api_and_downloads_are_binary(self):
        client = Client(interval=0, token="synthetic-secret")
        def download(request, timeout):
            response = Mock()
            response.url = request.full_url
            response.read.return_value = b"\x00\xff\r\n"
            response.__enter__ = Mock(return_value=response)
            response.__exit__ = Mock(return_value=False)
            return response
        client.open = Mock(side_effect=download)
        self.assertEqual(client.data("/api/v1/problems/1/testcase.zip"), b"\x00\xff\r\n")
        self.assertEqual(client.open.call_args.args[0].get_header("Authorization"), "Bearer synthetic-secret")
        client.data("/submissions/1/source")
        self.assertFalse(client.open.call_args.args[0].has_header("Authorization"))

    def test_redirect_refuses_external_host_before_following(self):
        from urllib.request import Request
        with self.assertRaises(ImportError):
            SameOriginRedirect().redirect_request(Request("https://yukicoder.me/api/1"), None, 302, "Found", {}, "https://example.com/leak")

    def test_cookie_parse_error_never_discloses_cookie_value(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cookies.txt"
            path.write_text("# Netscape HTTP Cookie File\nprivate-cookie-value\n")
            err = io.StringIO()
            with redirect_stderr(err):
                with self.assertRaises(ImportError) as raised:
                    Client(cookie_file=path)
            self.assertNotIn("private-cookie-value", str(raised.exception))
            self.assertNotIn("private-cookie-value", err.getvalue())

    def test_cookie_file_is_loaded_but_never_rewritten(self):
        from http.cookiejar import MozillaCookieJar
        from urllib.request import HTTPCookieProcessor, Request
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cookies.txt"
            path.write_text("# Netscape HTTP Cookie File\n.yukicoder.me\tTRUE\t/\tTRUE\t2147483647\tsession\tsynthetic-cookie\n")
            before = path.read_bytes(), path.stat().st_mtime_ns
            client = Client(cookie_file=path)
            handler = next(h for h in client.open.__self__.handlers if isinstance(h, HTTPCookieProcessor))
            self.assertIsInstance(handler.cookiejar, MozillaCookieJar)
            request = Request("https://yukicoder.me/problems/1/editorial")
            handler.cookiejar.add_cookie_header(request)
            self.assertEqual(request.get_header("Cookie"), "session=synthetic-cookie")
            self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), before)

    def test_invalid_zip_paths_and_html_payloads_are_rejected(self):
        for name in ("/test_in/a", "test_in/../a", "test_in\\a", "test_in//a", "other/a"):
            with self.subTest(name=name), self.assertRaises(ImportError):
                unpack_tests(zip_data({name: b"bad"}))
        with self.assertRaises(ImportError):
            unpack_tests(b"<html>Login</html>")

    def test_language_extensions_keep_unknown_languages_as_text(self):
        for language, suffix in (("C++23(gcc16)", "cpp"), ("PyPy3", "py"), ("cpp17", "cpp"), ("C11", "c"), ("C#", "cs"), ("NewLanguage", "txt")):
            self.assertEqual(extension(language), suffix)


if __name__ == "__main__":
    unittest.main()
