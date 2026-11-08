"""Keep the public statement HTML in a standalone browser-readable document."""

from html import escape


STYLE = """body { margin: 0; background: #f6f7f9; color: #222;
  font-family: system-ui, sans-serif; line-height: 1.8; }
main { max-width: 960px; margin: 2rem auto; padding: 2rem;
  background: white; border: 1px solid #ddd; border-radius: 8px; }
h1 { font-size: 1.6rem; line-height: 1.5; }
h4 { font-size: 1.25rem; border-bottom: 1px solid #ddd; padding-bottom: .3rem; }
h5 { font-size: 1.1rem; } h6 { font-size: 1rem; margin: 1rem 0 .5rem; }
.block { margin: 2rem 0; } .sample { margin: 2rem 0; }
pre { background: #f4f5f6; border: 1px solid #ddd; border-radius: 4px;
  padding: 1rem; overflow-x: auto; white-space: pre;
  font-family: ui-monospace, monospace; line-height: 1.5; }
code { font-family: ui-monospace, monospace; }
table { border-collapse: collapse; } th, td { border: 1px solid #ccc; padding: .5rem; }
img, svg { max-width: 100%; } a { color: #0969da; }
@media (max-width: 640px) { main { margin: 0; padding: 1rem; border-radius: 0; } }
"""

# Pinned MathJax 3 configuration, per the official v3.2 documentation.
# Keep pre enabled: yukicoder input-format blocks can contain TeX like $N$.
MATHJAX = r"""<script>
window.MathJax = {
  tex: {
    inlineMath: [['$', '$'], ['\\(', '\\)']],
    displayMath: [['$$', '$$'], ['\\[', '\\]']],
    processEscapes: true
  },
  options: {
    skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'code', 'annotation', 'annotation-xml']
  },
  svg: { fontCache: 'global' }
};
</script>
<script id="MathJax-script" defer src="https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-svg.js"></script>"""


def to_html(blocks, no, problem_id, title):
    url = f"https://yukicoder.me/problems/no/{no}"
    heading = escape(f"No.{no} {title}")
    # No Markdown round-trip: keep tags, classes, styles, whitespace, tables,
    # images and TeX directly from the parsed public statement sections.
    body = "\n\n".join(str(block) for block in blocks)
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<base href="{url}">
<title>{heading}</title>
<style>
{STYLE}</style>
{MATHJAX}
</head>
<body>
<main id="content" data-problem-id="{problem_id}">
<h1>{heading}</h1>
<p><a href="{url}">yukicoder の公開ページ</a></p>
{body}
</main>
</body>
</html>
"""
