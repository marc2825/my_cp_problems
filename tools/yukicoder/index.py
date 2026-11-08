"""Generate the archive index and record actual updates in Japan time."""

import json
import re
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from urllib.parse import quote

import yaml

from .api import ImportError, positive_int
from .archive import Change, Plan, UniqueLoader, check_path, read_file, readme_plan

JST = timezone(timedelta(hours=9), "JST")


def current_timestamp():
    return datetime.now(JST).isoformat(timespec="seconds")


def markdown_text(value):
    text = escape(str(value).replace("\n", " ").replace("\r", " "), quote=False)
    return re.sub(r"([\\`*_\[\]|])", r"\\\1", text)


def replace_block(text, name, body):
    start = f"<!-- BEGIN AUTO:{name} -->"
    end = f"<!-- END AUTO:{name} -->"
    block = f"{start}\n{body.rstrip()}\n{end}"
    if start not in text and end not in text:
        return text.rstrip() + "\n\n" + block + "\n"
    if text.count(start) != 1 or text.count(end) != 1 or text.index(start) >= text.index(end):
        raise ImportError(f"README の自動更新マーカーが不正です: {name}")
    first = text.index(start)
    last = text.index(end) + len(end)
    return text[:first] + block + text[last:]


def load_catalog(archive_root, problem_plans):
    overrides = {change.path: change.after for plan in problem_plans for change in plan.changes
                 if change.path.name == "metadata.yml"}
    paths = set(archive_root.glob("*/metadata.yml")) | set(overrides)
    catalog = []
    numbers = set()
    for path in sorted(paths):
        data = overrides.get(path)
        if data is None:
            data = read_file(path)
        try:
            metadata = yaml.load(data.decode("utf-8"), Loader=UniqueLoader)
        except (yaml.YAMLError, UnicodeError, TypeError, ValueError) as exc:
            raise ImportError(f"問題一覧用の metadata.yml を読み込めません: {path}") from exc
        if (not isinstance(metadata, dict) or metadata.get("platform") != "yukicoder"
                or not positive_int(metadata.get("problem_no"))
                or not isinstance(metadata.get("title"), str) or not metadata["title"].strip()
                or not isinstance(metadata.get("source", {}), dict)):
            raise ImportError(f"問題一覧用のメタデータが不正です: {path}")
        no = metadata["problem_no"]
        if path.parent.name != str(no) and not path.parent.name.startswith(f"{no}_"):
            raise ImportError(f"問題一覧のフォルダ名と問題番号が一致しません: {path}")
        if no in numbers:
            raise ImportError(f"問題一覧に問題番号が重複しています: No.{no}")
        numbers.add(no)
        catalog.append((path.parent, metadata))
    return sorted(catalog, key=lambda item: item[1]["problem_no"])


def display_timestamp(timestamp):
    if timestamp is None:
        return "未記録"
    return datetime.fromisoformat(timestamp).astimezone(JST).strftime("%Y-%m-%d %H:%M:%S JST")


def index_body(catalog, index_root, timestamp):
    lines = [f"最終自動更新: **{display_timestamp(timestamp)}**", "",
             f"保存済み問題: **{len(catalog)} 問**", "", "## yukicoder", "",
             "| No. | 問題 | 難易度 | コンテスト |", "| --- | --- | --- | --- |"]
    for directory, metadata in catalog:
        no = metadata["problem_no"]
        relative = quote((directory / "README.md").relative_to(index_root).as_posix(), safe="/")
        source = metadata.get("source", {})
        difficulty = metadata.get("difficulty")
        if difficulty is None or (isinstance(difficulty, str) and not difficulty.strip()):
            difficulty = source.get("level")
        level = f"★{difficulty:g}" if isinstance(difficulty, (int, float)) and not isinstance(difficulty, bool) else (
            markdown_text(difficulty) if difficulty is not None else "未設定")
        contest = markdown_text(metadata.get("contest") or "未設定")
        if positive_int(source.get("contest_id")):
            contest = f"[{contest}](https://yukicoder.me/contests/{source['contest_id']})"
        lines.append(f"| [{no}](https://yukicoder.me/problems/no/{no}) | "
                     f"[{markdown_text(metadata['title'])}]({relative}) | {level} | {contest} |")
    if not catalog:
        lines += ["", "保存済みの問題はありません。"]
    return "\n".join(lines)


def build_index_plan(archive_root, *, repository_root=None, problem_plans=()):
    archive_root = Path(archive_root).absolute()
    repository_root = Path(repository_root).absolute() if repository_root is not None else None
    index_root = repository_root / "problems" if repository_root else archive_root
    check_path(archive_root, directory=True)
    check_path(index_root, directory=True)
    index_path = index_root / "README.md"
    state_path = index_root / ".index-state.json"
    state_bytes = read_file(state_path)
    timestamp = None
    if state_bytes is not None:
        try:
            state = json.loads(state_bytes)
            if not isinstance(state, dict) or state.get("version") != 1:
                raise ValueError("invalid state version")
            timestamp = state["last_updated_at"]
            if not isinstance(timestamp, str) or datetime.fromisoformat(timestamp).tzinfo is None:
                raise ValueError("invalid timestamp")
        except (ValueError, TypeError, KeyError) as exc:
            raise ImportError(".index-state.json が不正です。既存の一覧と更新日時を保持します") from exc
    catalog = load_catalog(archive_root, problem_plans)
    index_before = read_file(index_path)
    try:
        index_text = index_before.decode("utf-8") if index_before is not None else (
            "# 問題一覧\n\n"
            "[marc2825 の yukicoder プロフィール](https://yukicoder.me/users/17084) · "
            "[作問一覧](https://yukicoder.me/users/17084/problems)\n\n"
            "問題文・解説・想定解・バリデータ・テストは各問題の README から参照できます。\n\n"
            "<!-- BEGIN AUTO:PROBLEM_INDEX -->\n<!-- END AUTO:PROBLEM_INDEX -->\n")
        root_path = repository_root / "README.md" if repository_root else None
        root_before = read_file(root_path) if root_path else None
        root_text = root_before.decode("utf-8") if root_before is not None else None
    except UnicodeDecodeError as exc:
        raise ImportError("一覧またはルート README が UTF-8 ではありません") from exc

    def render(stamp):
        rendered = {index_path: replace_block(index_text, "PROBLEM_INDEX", index_body(catalog, index_root, stamp)).encode("utf-8")}
        if root_text is not None:
            body = (f"最終自動更新: **{display_timestamp(stamp)}**\n\n"
                    f"保存済み問題: **{len(catalog)} 問** · [問題一覧](problems/README.md)")
            rendered[root_path] = replace_block(root_text, "ARCHIVE_STATUS", body).encode("utf-8")
        return rendered

    before = {index_path: index_before}
    if root_text is not None:
        before[root_path] = root_before
    rendered = render(timestamp)
    changed = (timestamp is None or any(plan.changes for plan in problem_plans)
               or any(data != before[path] for path, data in rendered.items()))
    if changed:
        timestamp = current_timestamp()
        rendered = render(timestamp)
    state_after = (json.dumps({"version": 1, "last_updated_at": timestamp, "problem_count": len(catalog)},
                              ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    rendered[state_path] = state_after
    before[state_path] = state_bytes
    plan = Plan(repository_root or archive_root, not index_root.exists())
    plan.directories = [index_root]
    for path, data in rendered.items():
        if data != before[path]:
            plan.changes.append(Change(path, before[path], data))
        else:
            plan.unchanged.append(str(path.relative_to(plan.directory)))
    return plan


def build_readme_plans(archive_root, problem_plans=()):
    """Plan offline README refreshes so file lists follow manual additions."""
    return [readme_plan(directory, metadata)
            for directory, metadata in load_catalog(Path(archive_root).absolute(), problem_plans)]


def report_readme_plans(plans):
    for plan in plans:
        if plan.changes or plan.preserved:
            plan.report()


def report_index_plan(plan):
    if not plan.changes:
        print("INDEX SKIP (変更なし)")
    for change in plan.changes:
        action = "CREATE" if change.before is None else "UPDATE"
        print(f"INDEX {action} {change.path.relative_to(plan.directory)}")
