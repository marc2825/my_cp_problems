"""Extract only the public statement and header, never the surrounding UI."""

import re
from decimal import Decimal

from bs4 import BeautifulSoup

from .api import ImportError
from .html import to_html
from .markdown import table_markdown, to_markdown


def parse_page(html, no, problem_id):
    soup = BeautifulSoup(html, "html.parser")
    content = soup.find(id="content")
    if content is None:
        raise ImportError("公開ページに #content がありません (ログイン画面／HTML 変更)")
    actual_id = content.get("data-problem-id")
    if actual_id is not None and str(problem_id) != actual_id:
        raise ImportError("公開ページと API の ProblemId が一致しません")
    title = content.find(re.compile(r"^h[1-6]$"))
    if title is None or not re.match(rf"No\.\s*{no}(?:\s|$)", title.get_text(" ", strip=True)):
        raise ImportError("公開ページの問題番号を確認できません")

    # Semantic headings locate sections even when the site inserts wrapper divs.
    heading = next((h for h in content.find_all(re.compile(r"^h[1-6]$"))
                    if h.get_text(strip=True) in ("問題文", "Problem Statement")), None)
    if heading is None:
        raise ImportError("問題文見出しがありません (非公開／HTML 変更)")
    section = heading.parent
    if section is content or section.name not in ("div", "section", "article"):
        raise ImportError("問題文の区切りを確認できません (HTML 変更)")
    headings = content.find_all(heading.name)
    blocks = []
    for h in headings[headings.index(heading):]:
        container = h.parent
        if h.find_parent("form") or h.find_parent(class_="modal"):
            break
        if container is content or container.name not in ("div", "section", "article"):
            raise ImportError("問題文セクションの区切りが変更されています")
        blocks.append(container)
    # Refuse an empty/truncated statement before it can replace an existing archive.
    text = " ".join(b.get_text(" ", strip=True) for b in blocks)
    if len(text) < 20 or not section.get_text(strip=True).removeprefix(heading.get_text(strip=True)).strip():
        raise ImportError("問題文が空または不完全です")
    section_names = [b.find(re.compile(r"^h[1-6]$")).get_text(strip=True) for b in blocks]
    if not any(n in section_names for n in ("入力", "入力形式", "Input")) or not any(
            n in section_names for n in ("出力", "出力形式", "Output")):
        raise ImportError("入力／出力セクションを確認できません (HTML 変更)")

    header = " ".join(str(s) for s in title.find_all_next(string=True)
                      if s.find_parent("div", class_="problem-header-main"))
    if not header.strip():
        # A semantic-text fallback for older headers; exclude the statement itself.
        header = content.get_text(" ", strip=True).split(heading.get_text(strip=True), 1)[0]
    header = re.sub(r"\s+", " ", header)
    tl = re.search(r"実行時間制限\s*[:：]\s*(?:1ケース\s*)?([0-9]+(?:\.[0-9]+)?)\s*秒", header)
    ml = re.search(r"メモリ制限\s*[:：]\s*(\d+)\s*MB", header, re.I)
    judge_type = None
    if re.search(r"(?:スペシャル|特殊)ジャッジ問題", header):
        judge_type = "special"
    elif "標準ジャッジ問題" in header:
        judge_type = "standard"
    updated = re.search(r"問題文最終更新日\s*[:：]\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", content.get_text(" ", strip=True))
    contest_link = content.find("a", href=re.compile(r"^/contests/\d+$"))
    result = {
        "time_limit_ms": int(Decimal(tl[1]) * 1000) if tl else None,
        "memory_limit_mb": int(ml[1]) if ml else None,
        "judge_type": judge_type,
        "statement_updated_at": updated[1] if updated else None,
        "contest_id": int(contest_link["href"].rsplit("/", 1)[1]) if contest_link else None,
    }
    warnings = []
    for key in ("time_limit_ms", "memory_limit_mb"):
        if result[key] is None:
            warnings.append(f"{key} を公開 HTML から取得できませんでした")
    if judge_type is None:
        warnings.append("ジャッジ形式を公開 HTML から確認できませんでした。既存値・手動設定があれば使用します")
    if any(b.find("img") for b in blocks):
        warnings.append("問題文の画像は公開 URL へのリンクとして保存しました。オフライン保存は手動で行ってください")
    base_url = f"https://yukicoder.me/problems/no/{no}"
    if any(b.find(["svg", "math"]) or any(table_markdown(t, base_url) is None for t in b.find_all("table"))
           for b in blocks):
        warnings.append("複雑な表／SVG／MathML は HTML として保持しました。GitHub 上の表示を確認してください")
    page_title = re.sub(rf"^No\.\s*{no}\s*", "", title.get_text(" ", strip=True))
    return (to_markdown(blocks, base_url),
            to_html(blocks, no, problem_id, page_title), result, warnings)
