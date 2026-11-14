#!/usr/bin/env python3
"""Remove .gitkeep files whose directories already contain other files (offline)."""

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {"__pycache__", "node_modules"}


def unnecessary_gitkeeps(root):
    """A .gitkeep is redundant once Git would keep its directory anyway."""
    root = Path(root)
    found = []
    for current, dirs, files in os.walk(root):
        # Hidden directories (.git, .venv, ...) and caches are never archive content.
        dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in SKIP_DIRS)
        if ".gitkeep" not in files:
            continue
        path = Path(current) / ".gitkeep"
        if path.is_symlink() or not path.is_file():
            continue
        others = (p for p in Path(current).rglob("*") if p != path and p.is_file()
                  and not any(part.startswith(".") and part != ".gitkeep" or part in SKIP_DIRS
                              for part in p.relative_to(current).parts[:-1]))
        if next(others, None) is not None:
            found.append(path)
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="削除対象の表示のみ。ファイルを削除しません")
    args = parser.parse_args(argv)
    paths = unnecessary_gitkeeps(ROOT)
    if not paths:
        print("GITKEEP SKIP (不要な .gitkeep はありません)")
    for path in paths:
        print(f"GITKEEP REMOVE {path.relative_to(ROOT)}")
        if not args.dry_run:
            path.unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())
