"""Download visible editorials, registered solutions, validators, and full tests."""

import io
import re
import stat
import zipfile
from dataclasses import dataclass, field
from html import escape
from pathlib import PurePosixPath
from urllib.parse import quote

from bs4 import BeautifulSoup

from .api import BASE_URL, ImportError, Unavailable
from .html import MATHJAX, STYLE


@dataclass
class Assets:
    files: dict[str, bytes] = field(default_factory=dict)
    urls: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def add(self, name, data, path):
        self.files[name] = data
        self.urls[name] = BASE_URL + path


def extension(language):
    name = language.lower()
    for prefixes, suffix in (
        (("c++", "cpp", "c_cpp"), "cpp"), (("python", "pypy"), "py"),
        (("c#", "csharp", "cs"), "cs"), (("java script", "javascript", "node"), "js"),
        (("typescript",), "ts"), (("java",), "java"), (("rust",), "rs"),
        (("golang", "go"), "go"), (("ruby",), "rb"), (("kotlin",), "kt"),
        (("swift",), "swift"), (("haskell",), "hs"), (("scala",), "scala"),
        (("php",), "php"), (("perl",), "pl"),
    ):
        if name.startswith(prefixes):
            return suffix
    if name == "c" or re.match(r"c(?:89|99|11|17|23)(?:\D|$)", name):
        return "c"
    return "txt"


def editorial_content(html, problem_id):
    soup = BeautifulSoup(html, "html.parser")
    content = soup.find(id="content")
    if content is None or content.get("data-problem-id") != str(problem_id):
        raise ImportError("解説ページの問題 ID を確認できません (ログイン画面／HTML 変更)")
    if "現在解説は表示することはできません" in content.get_text():
        raise Unavailable("解説・想定解の閲覧にはログイン済み Cookie が必要です")
    if not content.get_text(strip=True):
        raise ImportError("解説ページが空です")
    return content


def solution_ids(content):
    """Only follow submissions under the registered-solution heading."""
    heading = next((h for h in content.find_all(re.compile(r"^h[1-6]$"))
                    if h.get_text(strip=True).startswith("想定解")), None)
    if heading is None:
        return []
    result = []
    for node in heading.next_elements:
        if not getattr(node, "name", None):
            continue
        if content not in node.parents:
            break
        if re.fullmatch(r"h[1-6]", node.name) and int(node.name[1]) <= int(heading.name[1]):
            break
        match = re.fullmatch(r"/submissions/(\d+)", node.get("href", "")) if node.name == "a" else None
        if match and int(match[1]) not in result:
            result.append(int(match[1]))
    return result


def editorial_document(content, metadata):
    # Work on a clone: solution discovery still needs the original DOM.
    content = BeautifulSoup(str(content), "html.parser").find(id="content")
    for node in content.select("script, form, input, button, textarea, iframe, .modal, #ai_questions"):
        if node.parent is not None:
            node.decompose()
    # Private UI attributes (including CSRF tokens) are not archive content.
    for node in [content, *content.find_all(True)]:
        for key in list(node.attrs):
            if key.startswith("on") or key.startswith("data-"):
                del node.attrs[key]
    title = escape(f"No.{metadata['problem_no']} {metadata['title']} 解説")
    url = f"{BASE_URL}/problems/no/{metadata['problem_no']}/editorial"
    return (f'<!doctype html>\n<html lang="ja"><head><meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<base href="{url}"><title>{title}</title>\n<style>{STYLE}</style>\n{MATHJAX}\n'
            f'</head><body><main><h1>{title}</h1>\n{content}\n</main></body></html>\n').encode("utf-8")


def submission_info(html, problem_id, submission_id):
    soup = BeautifulSoup(html, "html.parser")
    content = soup.find(id="content")
    if (content is None or content.get("data-problem-id") != str(problem_id)
            or content.get("data-submission-id") != str(submission_id)):
        raise ImportError(f"提出 {submission_id} の問題 ID／提出 ID を確認できません")
    language = None
    user_id = None
    for row in content.select(".submission-info-table tr"):
        cells = row.find_all("td", recursive=False)
        if len(cells) < 2:
            continue
        label = cells[0].get_text(strip=True)
        if label == "言語":
            language = cells[1].get_text(" ", strip=True)
        if label == "ユーザー":
            link = cells[1].find("a", href=re.compile(r"^/users/\d+$"))
            if link:
                user_id = int(link["href"].rsplit("/", 1)[1])
    if language is None or user_id is None:
        raise ImportError(f"提出 {submission_id} の言語／ユーザーを確認できません")
    return extension(language), user_id


def unpack_tests(data):
    files = {}
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for entry in archive.infolist():
                path = PurePosixPath(entry.filename)
                if entry.is_dir() and entry.filename in ("test_in/", "test_out/"):
                    continue
                if (len(path.parts) != 2 or path.parts[0] not in ("test_in", "test_out")
                        or path.name in (".", "..") or "\\" in entry.filename
                        or str(path) != entry.filename or entry.is_dir()
                        or stat.S_ISLNK(entry.external_attr >> 16)):
                    raise ImportError("テスト ZIP に不正なパスが含まれています")
                name = "tests/" + entry.filename
                if name in files:
                    raise ImportError("テスト ZIP に重複したパスが含まれています")
                files[name] = archive.read(entry)
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, ValueError, OSError) as exc:
        raise ImportError("テスト ZIP を読み込めません (認証／ダウンロード失敗)") from exc
    if not files:
        raise ImportError("テスト ZIP に入出力ファイルがありません")
    return files


def fetch_tests(client, problem_id):
    path = f"/api/v1/problems/{problem_id}/testcase.zip"
    try:
        return {name: (data, path) for name, data in unpack_tests(client.data(path)).items()}
    except Unavailable:
        # The test tab uses these same list/download APIs with the browser session.
        # Some accounts can use them even when the bulk-download API is unavailable.
        files = {}
        for which in ("in", "out"):
            list_path = f"/api/v1/problems/{problem_id}/file/{which}"
            names = client.json(list_path)
            if (not isinstance(names, list) or any(not isinstance(n, str)
                    or not re.fullmatch(r"[A-Za-z0-9_.]+", n) or n in (".", "..") for n in names)
                    or len(names) != len(set(names))):
                raise ImportError("テスト一覧 API のファイル名を確認できません")
            for name in names:
                file_path = list_path + "/" + quote(name, safe="")
                files[f"tests/test_{which}/{name}"] = client.data(file_path), file_path
        if not files:
            raise ImportError("テスト一覧が空です")
        return files


def fetch_assets(client, metadata, solution_user=None):
    result = Assets()
    no, pid = metadata["problem_no"], metadata["problem_id"]
    path = f"/problems/no/{no}/editorial"
    content = None
    try:
        content = editorial_content(client.text(path), pid)
        result.add("editorial.html", editorial_document(content, metadata), path)
    except ImportError as exc:
        # API/edit tokens can read the original editorial, but cannot log into HTML pages.
        if client.token:
            try:
                api_path = f"/api/v1/problems/{pid}/editorial"
                data = client.json(api_path)
                if (not isinstance(data, dict) or not isinstance(data.get("content"), str)
                        or not isinstance(data.get("isMarkdown"), bool) or not data["content"].strip()):
                    raise ImportError("解説 API の本文／形式を確認できません")
                name = "editorial.source.md" if data["isMarkdown"] else "editorial.html"
                result.add(name, data["content"].encode("utf-8"), api_path)
            except ImportError as api_exc:
                result.errors.append(f"解説: {api_exc}")
        else:
            result.errors.append(f"解説: {exc}")
    if content is None:
        result.errors.append("想定解: 一覧の閲覧にはログイン済み Cookie が必要です")
    else:
        ids = solution_ids(content)
        if not ids:
            result.notes.append("想定解の登録はありません")
        for sid in ids:
            try:
                submission_path = f"/submissions/{sid}"
                suffix, user_id = submission_info(client.text(submission_path), pid, sid)
                if solution_user is not None and user_id != solution_user:
                    continue
                source_path = submission_path + "/source"
                source = client.data(source_path)
                if not source.strip() or re.match(br"\s*(?:<!doctype\s+html|<html(?:\s|>))", source, re.I):
                    raise ImportError(f"提出 {sid} のソースが空またはログイン画面です")
                result.add(f"solution/{sid}.{suffix}", source, source_path)
            except ImportError as exc:
                result.errors.append(f"想定解 {sid}: {exc}")
    try:
        path = f"/api/v1/problems/{pid}/validator"
        data = client.json(path)
        if not isinstance(data, dict) or not isinstance(data.get("source"), str) or not isinstance(data.get("langId"), str):
            raise ImportError("バリデータ API の形式が変更されています")
        if data["source"]:
            if not data["langId"]:
                raise ImportError("バリデータの言語が空です")
            result.add(f"validator/main.{extension(data['langId'])}", data["source"].encode("utf-8"), path)
        else:
            result.notes.append("バリデータは未登録です")
    except ImportError as exc:
        result.errors.append(f"バリデータ: {exc}")
    try:
        for name, (data, path) in fetch_tests(client, pid).items():
            result.add(name, data, path)
    except ImportError as exc:
        result.errors.append(f"テスト: {exc}")
    return result
