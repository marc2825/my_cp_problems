"""Prepare manual destinations and report missing archive content after a run."""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote

from bs4 import BeautifulSoup

from .archive import Change, EDITORIAL, Plan, check_path, judge_kind, read_file
from .index import load_catalog


@dataclass
class ManualStatus:
    no: int
    directory: Path
    required: list[str] = field(default_factory=list)
    optional: list[str] = field(default_factory=list)


class ArchiveView:
    """Read the final planned content, including new files in dry-run mode."""

    def __init__(self, plans):
        self.files = {change.path: change.after for plan in plans for change in plan.changes}

    def read(self, path):
        return self.files[path] if path in self.files else read_file(path)

    def files_under(self, directory):
        paths = {p for p in directory.rglob("*") if p.is_file()}
        paths.update(p for p in self.files if p.is_relative_to(directory))
        return sorted(p for p in paths if not p.name.startswith("."))

    def has_code(self, directory):
        return any((self.read(p) or b"").strip() for p in self.files_under(directory)
                   if p.suffix.lower() not in (".md", ".json", ".yml", ".yaml"))


def has_editorial(view, directory, manual_directory, scope):
    def written(data, path):
        if not data or not data.strip():
            return False
        text = data.decode("utf-8", errors="replace")
        if path.suffix == ".html":
            soup = BeautifulSoup(text, "html.parser")
            for element in soup.select("head, script, style"):
                element.decompose()
            text = soup.get_text(" ", strip=True)
        return bool(text.strip()) and not re.search(r"TODO|FIXME|未記入|現在解説は表示することはできません", text)

    for path in (directory / "editorial.html", directory / "editorial.source.md",
                 manual_directory / "editorial.html", manual_directory / "editorial.md"):
        if written(view.read(path), path):
            return True
    data = view.read(directory / "editorial.md")
    if not data or not data.strip() or data.strip() == EDITORIAL.encode("utf-8").strip():
        return False
    text = data.decode("utf-8", errors="replace")
    for target in re.findall(r"\]\(([^)]+)\)", text):
        if target.startswith(("https:", "http:", "#", "mailto:")):
            continue
        path = Path(os.path.abspath(directory / unquote(target.split("#", 1)[0].strip("<>"))))
        if path.is_relative_to(scope):
            linked = view.read(path)
            if written(linked, path):
                return True
    body = re.sub(r"!?\[[^\]]*\]\([^)]*\)", "", text)
    body = re.sub(r"(?m)^#+[^\n]*", "", body).strip()
    return bool(body) and not re.search(r"TODO|FIXME|未記入", body)


def test_inventory(view, directory):
    inputs, outputs = set(), set()
    for path in view.files_under(directory / "tests"):
        relative = path.relative_to(directory / "tests")
        if len(relative.parts) >= 2 and relative.parts[0] in ("test_in", "test_out"):
            names = inputs if relative.parts[0] == "test_in" else outputs
            names.add("/".join(relative.parts[1:]))
        elif path.suffix in (".in", ".out"):
            names = inputs if path.suffix == ".in" else outputs
            names.add(relative.with_suffix("").as_posix())
    return inputs, outputs


def build_manual_plan(archive_root, *, repository_root=None, problem_plans=()):
    archive_root = Path(archive_root).absolute()
    repository_root = Path(repository_root).absolute() if repository_root else None
    scope = repository_root or archive_root
    view = ArchiveView(problem_plans)
    plan = Plan(scope, not archive_root.exists())
    statuses = []

    def prepare(directory):
        check_path(directory, directory=True)
        plan.directories.append(directory)
        if not view.files_under(directory):
            path = directory / ".gitkeep"
            before = view.read(path)
            if before is None:
                plan.changes.append(Change(path, None, b""))

    for directory, metadata in load_catalog(archive_root, problem_plans):
        status = ManualStatus(metadata["problem_no"], directory)
        statuses.append(status)
        for name in ("statement.md", "statement.html"):
            if not (view.read(directory / name) or b"").strip():
                status.required.append(f"問題文: {name} が未取得。インポーターを再実行するか手動で保存")
        manual_editorial = (repository_root / "editorials/yukicoder" / directory.name
                            if repository_root else directory / "editorial")
        if not has_editorial(view, directory, manual_editorial, scope):
            prepare(manual_editorial)
            status.required.append(f"解説: {manual_editorial / 'editorial.html'} に本文を保存し、"
                                   "convert_editorials.py で Markdown 版を作って editorial.md からリンクする"
                                   "（--with-assets での取得も可）")
        for section, label in (("solution", "想定解"), ("validator", "バリデータ")):
            prepare(directory / section)
            if not view.has_code(directory / section):
                status.required.append(f"{label}: {directory / section}/ の空ファイルへ記入、または --with-assets で取得")
        for which in ("in", "out"):
            prepare(directory / f"tests/test_{which}")
        inputs, outputs = test_inventory(view, directory)
        if not inputs and not outputs:
            status.required.append(f"テスト: {directory / 'tests/test_in'}/ と tests/test_out/ に入出力を追加（--with-assets で全件取得も可）")
        for missing, which in ((inputs - outputs, "out"), (outputs - inputs, "in")):
            if missing:
                names = ", ".join(sorted(missing)[:5])
                extra = f" ほか {len(missing) - 5} 件" if len(missing) > 5 else ""
                status.required.append(f"テストの片側が不足: tests/test_{which}/ に {names}{extra} を追加")
        if judge_kind(metadata) == "special":
            prepare(directory / "checker")
            if not view.has_code(directory / "checker"):
                status.required.append(f"チェッカー: {directory / 'checker'}/ に特殊ジャッジのコードを手動追加")
        elif judge_kind(metadata) is None:
            status.required.append("ジャッジ形式: metadata.yml の judge_type に standard / special を記入")
        if not metadata.get("tags"):
            status.optional.append("metadata.yml の tags（分類）")
        if not any(p.stem.startswith("brute") for p in view.files_under(directory / "solution")
                   if (view.read(p) or b"").strip()):
            status.optional.append("solution/brute.*（愚直解）")
    return plan, statuses


def report_manual_plan(plan):
    for change in plan.changes:
        print(f"MANUAL CREATE {change.path.relative_to(plan.directory)}")


def report_reminders(statuses, *, dry_run=False):
    print("手動補完リマインド" + ("（dry-run: 実行後の予定）" if dry_run else ""))
    pending = [status for status in statuses if status.required]
    if not pending:
        print("  必須の補完項目はありません。")
    for status in pending:
        print(f"  No.{status.no}:")
        for item in status.required:
            print(f"    - {item}")
    optional = {}
    for status in statuses:
        for item in status.optional:
            optional[item] = optional.get(item, 0) + 1
    for item, count in optional.items():
        print(f"  任意: {item} が未追加（{count} 問）")
