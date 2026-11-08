"""Convert saved editorial HTML into GitHub-readable Markdown, keeping the HTML."""

import re
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

import yaml
from bs4 import BeautifulSoup

from .api import ImportError
from .archive import Change, Plan, UniqueLoader, check_path, read_file
from .markdown import safe_url, to_markdown

MARKER = ("<!-- editorial.html から自動生成。修正は editorial.html で行い、"
          "tools/convert_editorials.py を再実行してください -->")


def problem_title(problems_root, name):
    path = problems_root / name / "metadata.yml"
    data = read_file(path)
    if data is None:
        return None
    try:
        metadata = yaml.load(data.decode("utf-8"), Loader=UniqueLoader)
    except (yaml.YAMLError, UnicodeError, ValueError) as exc:
        raise ImportError(f"metadata.yml を読み込めません: {path}") from exc
    title = metadata.get("title") if isinstance(metadata, dict) else None
    return title.strip() if isinstance(title, str) and title.strip() else None


def editorial_markdown(html, directory, title=None):
    match = re.match(r"(\d+)", directory.name)
    if match is None:
        raise ImportError(f"フォルダ名から問題番号を読み取れません: {directory.name}")
    no = int(match[1])
    base_url = f"https://yukicoder.me/problems/no/{no}/editorial"
    soup = BeautifulSoup(html, "html.parser")
    body = to_markdown([soup.body or soup], base_url)
    # Prefer an image saved next to the HTML over the external copy.
    for image in soup.find_all("img"):
        url = safe_url(image.get("src", ""), base_url)
        name = PurePosixPath(unquote(urlsplit(url).path)).name if url else ""
        if name and (directory / name).is_file():
            body = body.replace(f"](<{url}>)", f"](<{name}>)")
    heading = f"# No.{no} {title}" if title else f"# No.{no}"
    links = f"[問題ページ](https://yukicoder.me/problems/no/{no}) · [HTML 版](editorial.html)"
    return f"{MARKER}\n\n{heading}\n\n{links}\n\n{body}"


def build_editorial_plan(editorials_root, problems_root):
    editorials_root = Path(editorials_root).absolute()
    problems_root = Path(problems_root).absolute()
    check_path(editorials_root, directory=True)
    plan = Plan(editorials_root, False)
    for html_path in sorted(editorials_root.glob("*/editorial.html")):
        directory = html_path.parent
        name = f"{directory.name}/editorial.md"
        try:
            html = read_file(html_path).decode("utf-8")
        except UnicodeError as exc:
            raise ImportError(f"editorial.html が UTF-8 ではありません: {html_path}") from exc
        content = editorial_markdown(html, directory, problem_title(problems_root, directory.name)).encode("utf-8")
        path = directory / "editorial.md"
        before = read_file(path)
        if before == content:
            plan.unchanged.append(name)
        elif before is not None and not before.startswith(MARKER.encode("utf-8")):
            plan.preserved.append(name)  # Hand-written Markdown is never replaced.
        else:
            plan.changes.append(Change(path, before, content))
    return plan


def report_editorial_plan(plan):
    for change in plan.changes:
        action = "CREATE" if change.before is None else "UPDATE"
        print(f"EDITORIAL {action} {change.path.relative_to(plan.directory)}")
    for name in plan.preserved:
        print(f"EDITORIAL PRESERVE {name} (手書きの Markdown を保持)")
    if not plan.changes:
        print(f"EDITORIAL SKIP (変更なし: {len(plan.unchanged)} 件)")
