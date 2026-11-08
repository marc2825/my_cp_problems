"""Plan safe, repeatable file updates before writing anything."""

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path, PurePosixPath
from urllib.parse import quote

import yaml

from .api import ImportError

MANUAL_DIRS = ("solution", "validator", "tests", "tests/test_in", "tests/test_out")
MANUAL_FILES = ("solution/main.cpp", "solution/main.py", "validator/main.cpp")
EDITORIAL = """# 解説

## 方針

TODO

## 証明

TODO

## 計算量

TODO

## 実装上の注意

TODO

## 想定誤解法

TODO
"""
DEFAULTS = {
    "platform": "yukicoder", "problem_no": None, "problem_id": None,
    "title": "", "url": "", "contest": "", "published_at": "",
    "time_limit_ms": None, "memory_limit_mb": None, "author": "",
    "difficulty": None, "tags": [], "judge_type": None,
}
AUTO_KEYS = frozenset(DEFAULTS) - {"difficulty", "tags", "judge_type"}


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    loader.flatten_mapping(node)
    result = {}
    for k, v in node.value:
        key = loader.construct_object(k, deep=deep)
        if key in result:
            raise ImportError(f"metadata.yml のキーが重複しています: {key}")
        result[key] = loader.construct_object(v, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


class MetadataDumper(yaml.SafeDumper):
    pass


MetadataDumper.add_representer(type(None), lambda d, v: d.represent_scalar("tag:yaml.org,2002:null", ""))


def check_path(path, directory=False):
    for ancestor in (path, *path.parents):
        if ancestor.is_symlink():
            raise ImportError(f"既存のシンボリックリンクを変更しません: {ancestor}")
    if path.exists() and (not path.is_dir() if directory else not path.is_file()):
        raise ImportError(f"想定外の種類のパスです: {path}")


def read_file(path):
    check_path(path)
    return path.read_bytes() if path.exists() else None


def slug(title):
    # Japanese/mixed-language titles are not translated or transliterated.
    if not title.isascii():
        return ""
    return re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:80].rstrip("_")


def problem_directory(root, no, title):
    root = Path(root).absolute()
    check_path(root, directory=True)
    matches = sorted(p for p in root.iterdir() if p.name == str(no) or p.name.startswith(f"{no}_")) if root.exists() else []
    if len(matches) > 1:
        raise ImportError(f"No.{no} の既存ディレクトリが複数あります。整理してください: {matches}")
    if matches:
        check_path(matches[0], directory=True)
        return matches[0]
    suffix = slug(title)
    return root / (f"{no}_{suffix}" if suffix else str(no))


def merge_metadata(existing, fetched):
    if existing is not None:
        try:
            old = yaml.load(existing.decode("utf-8"), Loader=UniqueLoader)
        except (yaml.YAMLError, UnicodeError, TypeError, ValueError) as exc:
            raise ImportError(f"metadata.yml を安全に読み取れません: {exc}") from exc
        if not isinstance(old, dict) or any(not isinstance(k, str) for k in old):
            raise ImportError("metadata.yml は文字列キーの YAML mapping にしてください")
    else:
        old = {}
    for key in ("platform", "problem_no", "problem_id"):
        if old.get(key) is not None and old[key] != fetched[key]:
            raise ImportError(f"既存 metadata.yml の {key} が取得した問題と一致しません")
    merged = dict(old)
    merged.pop("intended_complexity", None)
    for key, value in DEFAULTS.items():
        merged.setdefault(key, value)
    for key in AUTO_KEYS:
        value = fetched.get(key)
        # Missing optional data must not erase previously imported values.
        if value is not None and value != "":
            merged[key] = value
    difficulty = merged.get("difficulty")
    if difficulty is None or (isinstance(difficulty, str) and not difficulty.strip()):
        if fetched.get("difficulty") is not None:
            merged["difficulty"] = fetched["difficulty"]
    old_source = merged.get("source", {})
    if not isinstance(old_source, dict):
        raise ImportError("metadata.yml の source は mapping にしてください")
    source = dict(old_source)
    source.update({k: v for k, v in fetched.get("source", {}).items() if v is not None})
    if "asset_urls" in fetched.get("source", {}):
        if not isinstance(old_source.get("asset_urls", {}), dict):
            raise ImportError("metadata.yml の source.asset_urls は mapping にしてください")
        source["asset_urls"] = {**old_source.get("asset_urls", {}), **fetched["source"]["asset_urls"]}
    if source:
        merged["source"] = source
    if merged == old:
        return existing, merged  # Preserve formatting/comments and byte identity.
    content = "# 自動項目と手動項目の区分は tools/README.md を参照してください。\n"
    content += yaml.dump(merged, Dumper=MetadataDumper, allow_unicode=True, sort_keys=False, width=120)
    return content.encode("utf-8"), merged


def judge_kind(metadata):
    """Use an explicit manual setting first, then the public header value."""
    value = metadata.get("judge_type")
    if value is None or (isinstance(value, str) and not value.strip()):
        value = metadata.get("source", {}).get("judge_type")
    if not isinstance(value, str):
        return None
    value = value.strip().lower()
    if value in ("special", "special_judge", "spj", "特殊ジャッジ", "スペシャルジャッジ"):
        return "special"
    if value in ("standard", "標準ジャッジ"):
        return "standard"
    return None


LANGUAGES = {".c": "C", ".cc": "C++", ".cpp": "C++", ".cxx": "C++", ".cs": "C#", ".go": "Go",
             ".hs": "Haskell", ".java": "Java", ".js": "JavaScript", ".kt": "Kotlin", ".ml": "OCaml",
             ".nim": "Nim", ".py": "Python", ".rb": "Ruby", ".rs": "Rust", ".ts": "TypeScript"}
ROOT_FILES = {"statement.md": "問題文", "statement.html": "問題文（HTML 版。ダウンロードしてブラウザで開く）",
              "editorial.md": "解説", "editorial.html": "解説（yukicoder から取得した HTML）",
              "editorial.source.md": "解説（yukicoder から取得した元ソース）"}


def archive_files(directory, planned=None):
    """Map each file a problem directory will contain to its size in bytes."""
    sizes = {}
    if directory.exists():
        for path in directory.rglob("*"):
            if path.is_file() and not path.is_symlink():
                sizes[path.relative_to(directory).as_posix()] = path.stat().st_size
    for path, content in (planned or {}).items():
        sizes[path.relative_to(directory).as_posix()] = len(content)
    return {name: size for name, size in sizes.items()
            if not any(part.startswith(".") for part in name.split("/"))}


def describe(name):
    if name in ROOT_FILES:
        return ROOT_FILES[name]
    path = PurePosixPath(name)
    language = LANGUAGES.get(path.suffix.lower())
    suffix = f"（{language}）" if language else ""
    if path.parts[0] == "solution":
        if path.stem.startswith("brute"):
            return "愚直解" + suffix
        if path.stem.isdigit():
            return f"登録済み想定解（提出 {path.stem}" + (f"・{language}）" if language else "）")
        return "想定解" + suffix
    if path.parts[0] == "validator":
        return "入力検証" + suffix
    if path.parts[0] == "checker":
        return "チェッカー" + suffix
    return ""


def readme(metadata, files):
    no, title = metadata["problem_no"], metadata["title"]
    source = metadata.get("source", {})
    url = metadata.get("url") or f"https://yukicoder.me/problems/no/{no}"
    lines = [f"# No.{no} {title}", "", f"- 問題ページ: [yukicoder No.{no}]({url})"]
    contest = metadata.get("contest")
    if contest:
        url = source.get("contest_url")
        lines.append(f"- コンテスト: [{contest}]({url})" if url else f"- コンテスト: {contest}")
    published = metadata.get("published_at")
    if published:
        try:
            moment = datetime.fromisoformat(str(published))
            if moment.utcoffset() == timedelta(hours=9):
                published = moment.strftime("%Y-%m-%d %H:%M JST")
        except ValueError:
            pass
        lines.append(f"- 公開日時: {published}")
    if metadata.get("author"):
        lines.append(f"- 作問者: {metadata['author']}")
    difficulty = metadata.get("difficulty")
    if isinstance(difficulty, (int, float)) and not isinstance(difficulty, bool):
        lines.append(f"- 難易度: ★{difficulty:g}")
    elif isinstance(difficulty, str) and difficulty.strip():
        lines.append(f"- 難易度: {difficulty.strip()}")
    if metadata.get("time_limit_ms") is not None:
        lines.append(f"- 実行時間制限: {metadata['time_limit_ms'] / 1000:g} 秒")
    if metadata.get("memory_limit_mb") is not None:
        lines.append(f"- メモリ制限: {metadata['memory_limit_mb']} MB")

    # Only non-empty files are linked; empty placeholders are still to be filled.
    names = [name for name, size in files.items() if size and name not in ("README.md", "metadata.yml")
             and not name.startswith("tests/")]
    groups = list(ROOT_FILES) + ["solution/", "validator/", "checker/"]

    def order(name):
        rank = next((i for i, key in enumerate(groups) if name == key or (key.endswith("/") and name.startswith(key))),
                    len(groups))
        return rank, name

    rows = [(name, describe(name)) for name in sorted(names, key=order)]
    tests = [name for name in files if name.startswith("tests/test_in/")]
    if not tests:
        tests = [name for name in files if name.startswith("tests/") and name.endswith(".in")]
    if tests:
        rows.append(("tests/", f"テストケース（{len(tests)} 件）"))
    if "metadata.yml" in files:
        rows.append(("metadata.yml", "メタデータ"))
    lines += ["", "## ファイル", "", "| ファイル | 内容 |", "| --- | --- |"]
    lines += [f"| [{name}]({quote(name, safe='/')}) | {text} |" for name, text in rows]
    lines.append("")
    return "\n".join(lines).encode("utf-8")


def digest(content):
    return hashlib.sha256(content).hexdigest()


@dataclass
class Change:
    path: Path
    before: bytes | None
    after: bytes


@dataclass
class Plan:
    directory: Path
    new: bool
    changes: list[Change] = field(default_factory=list)
    preserved: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    directories: list[Path] = field(default_factory=list)

    def report(self):
        status = "NEW" if self.new else "EXISTING" if self.changes else "SKIP (変更なし)"
        print(f"{status} {self.directory.name}")
        for change in self.changes:
            action = "CREATE" if change.before is None else "UPDATE"
            print(f"  {action} {change.path.relative_to(self.directory)}")
        for name in self.preserved:
            print(f"  PRESERVE {name} (既存ファイル／手動変更を保持)")
        if self.unchanged:
            print(f"  UNCHANGED {len(self.unchanged)} files")

    def apply(self):
        # Preflight all paths and byte preconditions before making any changes.
        for path in self.directories:
            check_path(path, directory=True)
        for change in self.changes:
            if read_file(change.path) != change.before:
                raise ImportError(f"計画後にファイルが変更されました: {change.path}")
        for path in self.directories:
            path.mkdir(parents=True, exist_ok=True)
        for change in self.changes:
            if change.before is None:
                with change.path.open("xb") as stream:
                    stream.write(change.after)
            else:
                # Same-directory atomic replacement avoids partially written files.
                with tempfile.NamedTemporaryFile(dir=change.path.parent, delete=False) as stream:
                    temporary = Path(stream.name)
                    stream.write(change.after)
                try:
                    os.chmod(temporary, change.path.stat().st_mode & 0o777)
                    os.replace(temporary, change.path)
                finally:
                    temporary.unlink(missing_ok=True)


def load_state(directory):
    state_path = directory / ".import-state.json"
    state_bytes = read_file(state_path)
    try:
        state = json.loads(state_bytes) if state_bytes is not None else {"version": 1, "files": {}}
    except ValueError as exc:
        raise ImportError(".import-state.json が壊れています。上書きせず停止します") from exc
    if not isinstance(state, dict) or state.get("version") != 1 or not isinstance(state.get("files"), dict):
        raise ImportError(".import-state.json の形式を確認してください")
    return state_path, state_bytes, state


def state_bytes_after(state, hashes):
    return (json.dumps({**state, "files": hashes}, indent=2, sort_keys=True) + "\n").encode("utf-8")


def readme_plan(directory, metadata):
    """Regenerate README.md offline from metadata and the files on disk."""
    plan = Plan(directory, False)
    state_path, state_bytes, state = load_state(directory)
    hashes = dict(state["files"])
    path = directory / "README.md"
    before = read_file(path)
    content = readme(metadata, archive_files(directory))
    if before == content:
        plan.unchanged.append("README.md")
    elif before is not None and hashes.get("README.md") != digest(before):
        plan.preserved.append("README.md")
    else:
        plan.changes.append(Change(path, before, content))
        hashes["README.md"] = digest(content)
        plan.changes.append(Change(state_path, state_bytes, state_bytes_after(state, hashes)))
    return plan


def build_plan(root, fetched, statement, statement_html=None, asset_files=None):
    asset_files = asset_files or {}
    directory = problem_directory(root, fetched["problem_no"], fetched["title"])
    plan = Plan(directory, not directory.exists())
    plan.directories = [directory]
    state_path, state_bytes, state = load_state(directory)
    hashes = dict(state["files"])

    def add(name, content, managed=False, allow_empty=False):
        path = directory / name
        before = read_file(path)
        if before == content:
            plan.unchanged.append(name)
            if managed and hashes.get(name) == digest(content):
                hashes[name] = digest(content)
            return
        placeholder = allow_empty and before == b"" and name not in hashes
        if before is not None and not placeholder and (not managed or hashes.get(name) != digest(before)):
            plan.preserved.append(name)
            return
        plan.changes.append(Change(path, before, content))
        if managed:
            hashes[name] = digest(content)

    metadata_path = directory / "metadata.yml"
    metadata_before = read_file(metadata_path)
    metadata_after, metadata = merge_metadata(metadata_before, fetched)
    manual_dirs = MANUAL_DIRS + (("checker",) if judge_kind(metadata) == "special" else ())
    plan.directories += [directory / name for name in manual_dirs]
    for path in plan.directories:
        check_path(path, directory=True)
    if metadata_before != metadata_after:
        plan.changes.append(Change(metadata_path, metadata_before, metadata_after))
    else:
        plan.unchanged.append("metadata.yml")
    if statement is not None:
        add("statement.md", statement.encode("utf-8"), managed=True)
    if statement_html is not None:
        add("statement.html", statement_html.encode("utf-8"), managed=True)
    add("editorial.md", EDITORIAL.encode("utf-8"))
    for name in MANUAL_FILES:
        if name not in asset_files:
            add(name, b"")
    for name, content in sorted(asset_files.items()):
        relative = PurePosixPath(name)
        if (relative.is_absolute() or ".." in relative.parts or "\\" in name
                or str(relative) != name or len(relative.parts) > 3
                or not (name in ("editorial.html", "editorial.source.md")
                        or (len(relative.parts) == 2 and relative.parts[0] in ("solution", "validator"))
                        or (len(relative.parts) == 3 and relative.parts[:2] in (("tests", "test_in"), ("tests", "test_out"))))):
            raise ImportError(f"追加資料の保存先が不正です: {name}")
        parent = directory / relative.parent
        check_path(parent, directory=True)
        if parent not in plan.directories:
            plan.directories.append(parent)
        add(name, content, managed=True, allow_empty=name.startswith("validator/"))
    for name in manual_dirs:
        if name in ("solution", "validator", "tests"):
            continue
        path = directory / name
        if not any(n.startswith(name + "/") for n in asset_files) and (not path.exists() or not any(path.iterdir())):
            add(f"{name}/.gitkeep", b"")
    planned = {change.path: change.after for change in plan.changes}
    add("README.md", readme(metadata, archive_files(directory, planned)), managed=True)
    # Keep last-generation hashes for edited files, so edits remain detectable.
    after_state = state_bytes_after(state, hashes)
    if state_bytes != after_state:
        plan.changes.append(Change(state_path, state_bytes, after_state))
    else:
        plan.unchanged.append(".import-state.json")
    return plan
