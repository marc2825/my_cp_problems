"""Read-only endpoints verified against /api/swagger.yaml and the site's UI."""

import json
import math
import time
import warnings
from http.cookiejar import LoadError, MozillaCookieJar
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, HTTPCookieProcessor, Request, build_opener, urlopen

BASE_URL = "https://yukicoder.me"


class ImportError(Exception):
    """A recoverable fetch, format, or archive error."""


class Unavailable(ImportError):
    """Missing, private, or otherwise inaccessible public resource."""


class SameOriginRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        if urlsplit(newurl)[:2] != urlsplit(BASE_URL)[:2]:
            raise ImportError("別ホストへのリダイレクトを拒否しました")
        return super().redirect_request(request, fp, code, msg, headers, newurl)


def positive_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def problem_level(data):
    """The public API's Level is the number of stars, including half stars."""
    value = data.get("Level")
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0:
        return value
    return None


def validate_problem(data, no=None):
    if not isinstance(data, dict):
        raise ImportError("問題 API の形式が変更されています (object が必要です)")
    if not positive_int(data.get("No")) or not positive_int(data.get("ProblemId")):
        raise ImportError("問題 API の No / ProblemId が不正です")
    if no is not None and data["No"] != no:
        raise ImportError("要求した問題番号と API の問題番号が一致しません")
    if not isinstance(data.get("Title"), str) or not data["Title"].strip():
        raise ImportError("問題 API の Title が不正です")
    return data


class Client:
    def __init__(self, timeout=30, interval=0.5, cookie_file=None, token=None):
        self.timeout = timeout
        self.interval = interval
        self.last_request = 0.0
        self.cache = {}
        self.token = token
        self.open = urlopen
        if cookie_file is not None or token:
            jar = MozillaCookieJar()
            if cookie_file is not None:
                try:
                    with warnings.catch_warnings():
                        # cookiejar warnings can echo malformed lines, including values.
                        warnings.simplefilter("ignore", UserWarning)
                        jar.load(str(cookie_file), ignore_discard=True)
                except (OSError, LoadError):
                    # Cookie parser errors can contain credentials; never print them.
                    raise ImportError("Cookie ファイルを読み込めません。Netscape 形式を指定してください") from None
            self.open = build_opener(SameOriginRedirect(), HTTPCookieProcessor(jar)).open

    def data(self, path):
        if not path.startswith("/") or path.startswith("//"):
            raise ImportError("取得先は yukicoder 内の絶対パスで指定してください")
        url = BASE_URL + path
        for attempt in range(3):
            time.sleep(max(0, self.interval - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            headers = {"User-Agent": "yukicoder-public-archive/1.0"}
            if self.token and path.startswith("/api/"):
                headers["Authorization"] = "Bearer " + self.token
            request = Request(url, headers=headers)
            try:
                with self.open(request, timeout=self.timeout) as response:
                    if response.url.split("/", 3)[:3] != url.split("/", 3)[:3]:
                        raise ImportError(f"別ホストへのリダイレクトを拒否しました: {url}")
                    return response.read()
            except HTTPError as exc:
                if exc.code in (401, 403, 404):
                    raise Unavailable(f"公開情報を取得できません (存在しない／非公開): {url} HTTP {exc.code}") from exc
                if exc.code != 429 and exc.code < 500:
                    raise ImportError(f"取得失敗: {url} HTTP {exc.code}") from exc
                error = f"HTTP {exc.code}"
            except (URLError, TimeoutError, OSError, HTTPException) as exc:
                error = str(exc)
            if attempt < 2:
                time.sleep(2 ** attempt)
        raise ImportError(f"3 回試行して取得失敗: {url}: {error}")

    def text(self, path):
        try:
            return self.data(path).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ImportError(f"UTF-8 でないレスポンス: {path}") from exc

    def json(self, path):
        if path not in self.cache:
            try:
                self.cache[path] = json.loads(self.text(path))
            except ValueError as exc:
                raise ImportError(f"API が JSON を返しません: {path}") from exc
        return self.cache[path]

    def problem(self, no):
        # Swagger explicitly allows replacing {ProblemId} with no/{ProblemNo}.
        return validate_problem(self.json(f"/api/v1/problems/no/{no}"), no)

    def authored_problems(self, user_id):
        self.user(user_id)  # Distinguish unknown users from users with zero problems.
        data = self.json("/api/v1/problems")
        if not isinstance(data, list):
            raise ImportError("公開問題一覧 API の形式が変更されています (array が必要です)")
        if any(not isinstance(p, dict) or not positive_int(p.get("AuthorId")) for p in data):
            raise ImportError("公開問題一覧 API の AuthorId が不正です")
        problems = [validate_problem(p) for p in data if p["AuthorId"] == user_id]
        return sorted({p["No"] for p in problems})

    def user(self, user_id):
        data = self.json(f"/api/v1/user/id/{user_id}")
        if not isinstance(data, dict) or data.get("Id") != user_id or not isinstance(data.get("Name"), str):
            raise ImportError("ユーザー API の Id / Name が不正です")
        return data

    def contest(self, contest_id):
        data = self.json(f"/api/v1/contest/id/{contest_id}")
        if not isinstance(data, dict) or data.get("Id") != contest_id or not isinstance(data.get("Name"), str):
            raise ImportError("コンテスト API の Id / Name が不正です")
        return data
