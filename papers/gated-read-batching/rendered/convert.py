#!/usr/bin/env python3
"""Render a paper's MANUSCRIPT.md to a self-contained, print-ready HTML.

URENDER2. Instance of the UPDF1 recipe, de-hardcoded so both `encoder-crossover-190` and
`gated-read-batching` can use it. The LaTeX in submission/main.tex remains the source of
record; this script only re-renders the markdown manuscript so Chrome/LibreOffice can
produce a PDF/DOCX on a host with no TeX toolchain.

Content is preserved verbatim: no prose is rewritten, dropped, reordered or summarised.
The only injected material is (a) the byline lifted from submission/main.tex and (b) CSS.

Usage:  python3 convert.py            # writes <paper-dir-name>.html next to this script
"""
import html
import pathlib
import re
import sys

import markdown

HERE = pathlib.Path(__file__).resolve().parent
PAPER = HERE.parent                      # papers/<name>
MD = PAPER / "MANUSCRIPT.md"
TEX = PAPER / "submission" / "main.tex"
OUT = HERE / (PAPER.name + ".html")

CSS = r"""
@page { size: A4; margin: 18mm 17mm 20mm 17mm; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body {
  font-family: "DejaVu Serif", "Liberation Serif", Georgia, serif;
  font-size: 10.2pt; line-height: 1.42; color: #111; margin: 0;
  text-align: justify; hyphens: auto;
}
h1 {
  font-size: 16.5pt; line-height: 1.22; margin: 0 0 6pt 0; text-align: left;
  font-weight: 700; border-bottom: 2px solid #222; padding-bottom: 8pt;
}
p.byline {
  font-size: 11pt; margin: 8pt 0 12pt 0; text-align: left;
  font-family: "DejaVu Sans", "Liberation Sans", sans-serif;
}
p.byline .affil { font-size: 9pt; color: #444; display: block; margin-top: 2pt; }
h2 { font-size: 12.6pt; margin: 15pt 0 5pt 0; text-align: left; border-bottom: 1px solid #bbb; padding-bottom: 2pt; }
h3 { font-size: 11pt; margin: 11pt 0 4pt 0; text-align: left; }
h4 { font-size: 10.4pt; margin: 9pt 0 3pt 0; text-align: left; font-style: italic; }
p { margin: 0 0 6.5pt 0; }
ul, ol { margin: 0 0 6.5pt 0; padding-left: 16pt; }
li { margin: 0 0 3pt 0; }
hr { border: none; border-top: 1px solid #ccc; margin: 12pt 0; }
code {
  font-family: "DejaVu Sans Mono", "Liberation Mono", monospace;
  font-size: 0.855em; background: #f2f2f2; padding: 0 1.5pt;
  border-radius: 2px; word-break: break-word;
}
strong { font-weight: 700; }
table {
  width: 100%; border-collapse: collapse; margin: 6pt 0 10pt 0;
  font-family: "DejaVu Sans", "Liberation Sans", sans-serif;
  font-size: 7.9pt; line-height: 1.28; text-align: left; page-break-inside: auto;
}
thead { display: table-header-group; }
tr { page-break-inside: avoid; }
th, td { border: 0.6pt solid #8a8a8a; padding: 2.6pt 3.4pt; vertical-align: top; }
th { background: #ececec; font-weight: 700; }
td code, th code { background: transparent; font-size: 0.92em; }
blockquote { margin: 6pt 0 6pt 12pt; padding-left: 8pt; border-left: 2px solid #ccc; color: #333; }
"""


def byline() -> str:
    """Lift \\author{...} out of the LaTeX source so the render carries the same name."""
    if not TEX.exists():
        sys.stderr.write("FATAL: byline source %s missing\n" % TEX)
        raise SystemExit(2)
    tex = TEX.read_text(encoding="utf-8")
    m = re.search(r"\\author\{((?:[^{}]|\{[^{}]*\})*)\}", tex)
    if not m:
        sys.stderr.write("FATAL: no \\author{{...}} in %s\n" % TEX)
        raise SystemExit(2)
    name = m.group(1).strip().replace("---", "\u2014")
    if "AUTHOR SLOT" in name.upper() or not name:
        sys.stderr.write("FATAL: byline still a placeholder: %r\n" % name)
        raise SystemExit(2)
    return ('<p class="byline"><strong>%s</strong>'
            '<span class="affil">Byline carried into this render from '
            'submission/main.tex.</span></p>' % html.escape(name)), name


def split_title(md_text: str):
    """Return (title, body) where body no longer carries the leading H1 + rule."""
    lines = md_text.splitlines()
    title, i = None, 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i < len(lines) and lines[i].startswith("# "):
        title = lines[i][2:].strip()
        i += 1
        while i < len(lines) and (not lines[i].strip() or lines[i].strip() == "---"):
            i += 1
    return title or "Untitled", "\n".join(lines[i:])


def main() -> int:
    raw = MD.read_text(encoding="utf-8")
    title, body = split_title(raw)
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "sane_lists", "attr_list", "md_in_html"],
        output_format="html5",
    )
    rendered = md.convert(body)
    title_html = html.escape(title)
    byline_html, name = byline()

    page = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<title>{title_html}</title>
<meta name="author" content="{html.escape(name)}">
<style>{CSS}</style>
</head><body>
<h1>{title_html}</h1>
{byline_html}
{rendered}
</body></html>
"""
    OUT.write_text(page, encoding="utf-8")
    slot = page.upper().count("AUTHOR SLOT")
    print("paper:", PAPER.name)
    print("wrote %s %d bytes" % (OUT, OUT.stat().st_size))
    print("byline:", name)
    print("AUTHOR SLOT occurrences in HTML:", slot)
    print("name occurrences in HTML:", page.count(name))
    print("h1:", page.count("<h1"), "| h2:", page.count("<h2"), "| h3:", page.count("<h3"),
          "| table:", page.count("<table"), "| strong:", page.count("<strong"))
    if slot:
        sys.stderr.write("FATAL: AUTHOR SLOT survived into %s\n" % OUT)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
