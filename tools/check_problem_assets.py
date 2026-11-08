#!/usr/bin/env python3
"""Check missing archive assets and optionally prepare manual destinations offline."""

import argparse
import sys
from pathlib import Path

from yukicoder.api import ImportError
from yukicoder.index import build_index_plan, report_index_plan
from yukicoder.manual import build_manual_plan, report_manual_plan, report_reminders

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "problems/yukicoder", help="問題データの保存先")
    parser.add_argument("--prepare-dirs", action="store_true", help="不足資料の保存先を作成 (.gitkeep を配置)")
    parser.add_argument("--dry-run", action="store_true", help="保存先の作成計画とリマインドだけ表示")
    args = parser.parse_args(argv)
    repository_root = ROOT if args.output.absolute() == ROOT / "problems/yukicoder" else None
    try:
        plan, statuses = build_manual_plan(args.output, repository_root=repository_root)
        if args.prepare_dirs or args.dry_run:
            report_manual_plan(plan)
        if args.prepare_dirs and not args.dry_run:
            plan.apply()
        if args.prepare_dirs:
            index_plan = build_index_plan(args.output, repository_root=repository_root, problem_plans=[plan])
            report_index_plan(index_plan)
            if not args.dry_run:
                index_plan.apply()
        report_reminders(statuses, dry_run=args.dry_run)
    except (ImportError, OSError, UnicodeError) as exc:
        print(f"ERROR MANUAL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
