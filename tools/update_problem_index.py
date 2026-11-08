#!/usr/bin/env python3
"""Refresh problem READMEs, the problem index and update timestamp without network access."""

import argparse
import sys
from pathlib import Path

from yukicoder.api import ImportError
from yukicoder.index import build_index_plan, build_readme_plans, report_index_plan, report_readme_plans
from yukicoder.manual import build_manual_plan, report_manual_plan, report_reminders

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "problems" / "yukicoder", help="問題データの保存先")
    parser.add_argument("--dry-run", action="store_true", help="変更計画のみ。ファイルを書き込みません")
    args = parser.parse_args(argv)
    repository_root = ROOT if args.output.absolute() == ROOT / "problems" / "yukicoder" else None
    try:
        manual_plan, statuses = build_manual_plan(args.output, repository_root=repository_root)
        report_manual_plan(manual_plan)
        if not args.dry_run:
            manual_plan.apply()
        readme_plans = build_readme_plans(args.output, [manual_plan])
        report_readme_plans(readme_plans)
        if not args.dry_run:
            for readme_plan in readme_plans:
                readme_plan.apply()
        plan = build_index_plan(args.output, repository_root=repository_root,
                                problem_plans=[manual_plan, *readme_plans])
        report_index_plan(plan)
        if not args.dry_run:
            plan.apply()
        report_reminders(statuses, dry_run=args.dry_run)
    except (ImportError, OSError, UnicodeError) as exc:
        print(f"ERROR INDEX: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
