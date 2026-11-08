"""Small HTML converter; keep TeX for GitHub math and preserve code whitespace."""

import copy
import re
from urllib.parse import urljoin, urlsplit

from bs4 import Comment, NavigableString, Tag

MATH = re.compile(r"(\\\(.*?\\\)|\\\[.*?\\\]|\$\$.*?\$\$|(?<!\\)\$[^\n$]+?\$)", re.S)


def github_math(tex):
    """Rewrite TeX delimiters into the $...$ / $$...$$ forms GitHub renders."""
    if tex.startswith(("\\[", "$$")):
        lines = [line.strip() for line in tex[2:-2].splitlines() if line.strip()]
        # Display math renders reliably only as its own block.
        return "\n\n$$\n" + "\n".join(lines) + "\n$$\n\n"
    inner = tex[2:-2] if tex.startswith("\\(") else tex[1:-1]
    # Inline math must stay on one line without padding inside the dollars.
    return "$" + re.sub(r"\s+", " ", inner).strip() + "$"


def text_markdown(text):
    parts = MATH.split(text)
    for i in range(0, len(parts), 2):
        plain = re.sub(r"\s+", " ", parts[i])
        # Escape Markdown punctuation only outside TeX.
        parts[i] = re.sub(r"([\\`*_\[\]<>#])", r"\\\1", plain)
    for i in range(1, len(parts), 2):
        parts[i] = github_math(parts[i])
    return "".join(parts)


def safe_url(value, base_url):
    url = urljoin(base_url, value)
    return url if urlsplit(url).scheme in ("https", "http") else ""


def fenced(text):
    runs = [len(x) for x in re.findall(r"`+", text)]
    fence = "`" * max(3, max(runs, default=0) + 1)
    # Preserve sample contents, including spaces and blank lines.
    return f"\n\n{fence}text\n{text}" + ("" if text.endswith("\n") else "\n") + f"{fence}\n\n"


def table_markdown(node, base_url):
    """Convert a plain grid to a GitHub table; None when HTML must be kept."""
    rows = node.find_all("tr")
    if not rows or any(row.find_parent("table") is not node for row in rows):
        return None
    grid = []
    for row in rows:
        cells = row.find_all(["th", "td"], recursive=False)
        if not cells or any(cell.get(attr, "1") != "1" for cell in cells for attr in ("colspan", "rowspan")):
            return None
        texts = ["".join(render(c, base_url) for c in cell.children).strip() for cell in cells]
        if any("\n" in text for text in texts):
            return None
        grid.append([text.replace("|", "\\|") for text in texts])
    if len({len(row) for row in grid}) != 1:
        return None
    header, *body = grid
    lines = ["| " + " | ".join(header) + " |", "|" + " --- |" * len(header)]
    lines += ["| " + " | ".join(row) + " |" for row in body]
    return "\n\n" + "\n".join(lines) + "\n\n"


def render(node, base_url):
    if isinstance(node, Comment):
        return ""
    if isinstance(node, NavigableString):
        return text_markdown(str(node))
    if not isinstance(node, Tag) or node.name in ("script", "style", "button", "input", "textarea"):
        return ""
    tag = node.name
    if tag == "pre":
        return fenced(node.get_text())
    if tag == "code":
        value = node.get_text()
        fence = "`" * (max([len(x) for x in re.findall(r"`+", value)], default=0) + 1)
        padding = " " if value.startswith(("`", " ")) or value.endswith(("`", " ")) else ""
        return f"{fence}{padding}{value}{padding}{fence}"
    if tag == "img":
        url = safe_url(node.get("src", ""), base_url)
        alt = text_markdown(node.get("alt", "画像"))
        return f"![{alt}](<{url}>)" if url else alt
    if tag == "br":
        return "  \n"
    if tag == "hr":
        return "\n\n---\n\n"
    if tag in ("ul", "ol"):
        items = []
        for i, item in enumerate(node.find_all("li", recursive=False), 1):
            content = "".join(render(c, base_url) for c in item.children).strip()
            prefix = f"{i}. " if tag == "ol" else "- "
            items.append(prefix + content.replace("\n", "\n" + " " * len(prefix)))
        return "\n\n" + "\n".join(items) + "\n\n"
    if tag == "table" and (table := table_markdown(node, base_url)) is not None:
        return table
    if tag in ("table", "svg", "math"):
        # Complex tables/diagrams cannot reliably be reduced to plain Markdown.
        # Keep HTML, with absolute public resource URLs, instead of dropping content.
        copied = copy.deepcopy(node)
        for element in copied.find_all(["script", "style", "iframe", "object", "embed"]):
            element.decompose()
        for element in [copied, *copied.find_all(True)]:
            for attr in list(element.attrs):
                if attr.lower().startswith("on"):
                    del element[attr]
            for attr in ("src", "href", "xlink:href"):
                if attr in element.attrs:
                    element[attr] = safe_url(element[attr], base_url)
        return "\n\n" + str(copied) + "\n\n"
    body = "".join(render(c, base_url) for c in node.children)
    if re.fullmatch(r"h[1-6]", tag):
        # The original h4/h5/h6 become level 2/3/4 below the problem title.
        level = max(2, int(tag[1]) - 2)
        return "\n\n" + "#" * level + " " + body.strip() + "\n\n"
    if tag in ("p", "div", "section", "article", "dl", "dt", "dd", "figure", "figcaption"):
        return "\n\n" + body.strip() + "\n\n" if body.strip() else ""
    if tag in ("strong", "b", "em", "i", "del", "s"):
        marker = {"strong": "**", "b": "**", "em": "*", "i": "*", "del": "~~", "s": "~~"}[tag]
        return marker + body.strip() + marker
    if tag == "a":
        url = safe_url(node.get("href", ""), base_url)
        return f"[{body.strip()}](<{url}>)" if url else body
    if tag == "blockquote":
        return "\n\n" + "\n".join("> " + line for line in body.strip().splitlines()) + "\n\n"
    if tag in ("sup", "sub"):
        return f"<{tag}>{body}</{tag}>"
    return body


def to_markdown(blocks, base_url):
    result = "\n\n".join(render(block, base_url).strip() for block in blocks)
    # Protect complete code blocks and TeX before normalizing HTML indentation.
    preserved = []

    def protect(match):
        preserved.append(match[0])
        return f"\x00PRESERVE{len(preserved) - 1}\x00"

    pattern = re.compile(r"(?m)^(`{3,})text\n[\s\S]*?^\1[ \t]*(?=\n|$)|" + MATH.pattern)
    result = pattern.sub(protect, result)
    result = re.sub(r"\n[ \t]*\n(?:[ \t]*\n)*", "\n\n", result).strip()
    for i, original in enumerate(preserved):
        result = result.replace(f"\x00PRESERVE{i}\x00", original)
    return result.rstrip("\n") + "\n"
