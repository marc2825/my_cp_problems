#!/usr/bin/env python3
"""Convert editorials/yukicoder/*/editorial.html to editorial.md without network access."""

import argparse
import sys
from pathlib import Path

from yukicoder.api import ImportError
from yukicoder.editorial import build_editorial_plan, report_editorial_plan

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="変換計画のみ。ファイルを書き込みません")
    args = parser.parse_args(argv)
    try:
        plan = build_editorial_plan(ROOT / "editorials" / "yukicoder", ROOT / "problems" / "yukicoder")
        report_editorial_plan(plan)
        if not args.dry_run:
            plan.apply()
    except (ImportError, OSError, UnicodeError) as exc:
        print(f"ERROR EDITORIAL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
