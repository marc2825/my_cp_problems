#!/usr/bin/env python3
"""Archive yukicoder problems, optionally including accessible supporting assets."""

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from yukicoder.api import Client, ImportError, Unavailable, positive_int, problem_level
from yukicoder.archive import build_plan
from yukicoder.assets import fetch_assets
from yukicoder.index import build_index_plan, report_index_plan
from yukicoder.manual import build_manual_plan, report_manual_plan, report_reminders
from yukicoder.parser import parse_page

ROOT = Path(__file__).resolve().parents[1]


def positive_arg(value):
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("正の整数を指定してください") from None
    if number <= 0:
        raise argparse.ArgumentTypeError("正の整数を指定してください")
    return number


def warn(no, message):
    print(f"WARNING No.{no}: {message}", file=sys.stderr)


def fetch_problem(client, no):
    data = client.problem(no)
    if data.get("WIP"):
        raise Unavailable("作問中の問題は対象外です")
    date = data.get("Date")
    if date is not None:
        try:
            published = datetime.fromisoformat(date)
            if published.tzinfo is None:
                raise ValueError("timezone missing")
        except (TypeError, ValueError) as exc:
            raise ImportError("API の Date が RFC 3339 の日時ではありません") from exc
        if published > datetime.now(timezone.utc):
            raise Unavailable("公開予定日時が未来の問題は対象外です")
    metadata = {
        "platform": "yukicoder", "problem_no": no, "problem_id": data["ProblemId"],
        "title": data["Title"], "url": f"https://yukicoder.me/problems/no/{no}",
        "published_at": date,
        "source": {"api_url": f"https://yukicoder.me/api/v1/problems/no/{no}"},
    }
    if date is None:
        warn(no, "公開日時を取得できませんでした。既存値があれば保持します")
    source = metadata["source"]
    level = problem_level(data)
    if level is not None:
        metadata["difficulty"] = level
        source["level"] = level
    else:
        warn(no, "★の数 (API の Level) を取得できませんでした。既存値があれば保持します")
    for api_key, key in (("AuthorId", "author_id"), ("TesterIds", "tester_ids"),
                         ("ProblemType", "problem_type"), ("EpsMode", "eps_mode"),
                         ("Eps", "eps"), ("EnablePureJudge", "enable_pure_judge"),
                         ("AllowedLangs", "allowed_langs")):
        if api_key in data:
            source[key] = data[api_key]
    if positive_int(data.get("AuthorId")):
        try:
            metadata["author"] = client.user(data["AuthorId"])["Name"]
        except ImportError as exc:
            warn(no, f"作者名を取得できませんでした: {exc}")
    else:
        warn(no, "API の AuthorId を取得できませんでした")

    statement = None
    statement_html = None
    page_info = {}
    try:
        html = client.text(f"/problems/no/{no}")
        body, statement_html, page_info, warnings = parse_page(html, no, data["ProblemId"])
        statement = f"# No.{no} {data['Title']}\n\n" + body
        for message in warnings:
            warn(no, message)
    except Unavailable:
        # A private or deleted page must not create a misleading partial archive.
        raise
    except ImportError as exc:
        warn(no, f"問題文／制限の取得に失敗しました。既存ファイルを保持しメタデータのみ取り込みます: {exc}")
    for key in ("time_limit_ms", "memory_limit_mb"):
        metadata[key] = page_info.get(key)
    if page_info.get("statement_updated_at"):
        source["statement_updated_at"] = page_info["statement_updated_at"]
    if page_info.get("judge_type"):
        source["judge_type"] = page_info["judge_type"]
    contest_id = data.get("ContestId") or page_info.get("contest_id")
    if positive_int(contest_id):
        source["contest_id"] = contest_id
        source["contest_url"] = f"https://yukicoder.me/contests/{contest_id}"
        try:
            contest = client.contest(contest_id)
            metadata["contest"] = contest["Name"]
            source["contest_start_at"] = contest.get("Date")
            source["contest_end_at"] = contest.get("EndDate")
        except ImportError as exc:
            warn(no, f"コンテスト情報を取得できませんでした: {exc}")
    return metadata, statement, statement_html


def main(argv=None, client=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("problem_no", nargs="?", type=positive_arg, help="公開問題番号")
    parser.add_argument("--user", type=positive_arg, help="作問者のユーザー ID")
    parser.add_argument("--dry-run", action="store_true", help="取得と変更計画のみ。ファイルを書き込みません")
    parser.add_argument("--output", type=Path, default=ROOT / "problems" / "yukicoder", help="保存先のルートディレクトリ")
    parser.add_argument("--with-assets", action="store_true", help="解説・登録済み想定解・バリデータ・全テストも取得")
    parser.add_argument("--cookie-file", type=Path, help="ログイン済み Cookie (Netscape 形式)。ファイルは更新しません")
    parser.add_argument("--token-env", help="API キー／編集トークンを格納した環境変数名 (例: YUKICODER_API_TOKEN)")
    parser.add_argument("--solution-user", type=positive_arg, help="想定解を提出ユーザー ID で絞り込む (--with-assets 用)")
    args = parser.parse_args(argv)
    if (args.problem_no is None) == (args.user is None):
        parser.error("問題番号 または --user のいずれか一方を指定してください")
    if not args.with_assets and (args.cookie_file or args.token_env or args.solution_user):
        parser.error("--cookie-file / --token-env / --solution-user は --with-assets と併用してください")
    if args.token_env and not os.environ.get(args.token_env, "").strip():
        parser.error("--token-env で指定した環境変数が未設定または空です")
    try:
        token = os.environ[args.token_env].strip() if args.token_env else None
        client = client or Client(cookie_file=args.cookie_file, token=token)
        numbers = client.authored_problems(args.user) if args.user else [args.problem_no]
    except (ImportError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"{'DRY RUN: ' if args.dry_run else ''}{len(numbers)} problem(s)")
    complete = failed = skipped = partial = 0
    problem_plans = []
    for no in numbers:
        try:
            metadata, statement, statement_html = fetch_problem(client, no)
            assets = fetch_assets(client, metadata, args.solution_user) if args.with_assets else None
            if assets is not None:
                for message in assets.errors:
                    warn(no, message)
                for message in assets.notes:
                    print(f"  No.{no}: {message}")
                if assets.urls:
                    metadata["source"]["asset_urls"] = assets.urls
            plan = build_plan(args.output, metadata, statement, statement_html,
                              asset_files=assets.files if assets else None)
            plan.report()
            if not args.dry_run:
                plan.apply()
            problem_plans.append(plan)
            complete += 1
            if statement is None or (assets is not None and assets.errors):
                partial += 1
                if statement is None:
                    print(f"  PARTIAL No.{no}: statement.md / statement.html は未取得")
                if assets is not None and assets.errors:
                    print(f"  PARTIAL No.{no}: 追加資料の取得失敗 {len(assets.errors)} 件")
        except Unavailable as exc:
            print(f"SKIP No.{no}: {exc}", file=sys.stderr)
            skipped += 1
        except (ImportError, OSError, UnicodeError) as exc:
            print(f"ERROR No.{no}: {exc}", file=sys.stderr)
            failed += 1
    if problem_plans:
        try:
            repository_root = ROOT if args.output.absolute() == ROOT / "problems" / "yukicoder" else None
            manual_plan, statuses = build_manual_plan(args.output, repository_root=repository_root, problem_plans=problem_plans)
            report_manual_plan(manual_plan)
            if not args.dry_run:
                manual_plan.apply()
            index_plan = build_index_plan(args.output, repository_root=repository_root, problem_plans=[*problem_plans, manual_plan])
            report_index_plan(index_plan)
            if not args.dry_run:
                index_plan.apply()
            report_reminders(statuses, dry_run=args.dry_run)
        except (ImportError, OSError, UnicodeError) as exc:
            print(f"ERROR INDEX: {exc}", file=sys.stderr)
            failed += 1
    print(f"{'DRY RUN ' if args.dry_run else ''}done: imported={complete}, partial={partial}, skipped={skipped}, failed={failed}")
    return 1 if failed or skipped or partial else 0


if __name__ == "__main__":
    sys.exit(main())
