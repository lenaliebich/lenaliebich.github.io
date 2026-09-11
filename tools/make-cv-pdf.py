#!/usr/bin/env python3
"""Build assets/cv/Liebich-CV.pdf from the rendered CV page.

The PDF is generated from docs/cv.html, so it always matches the website.
Run `quarto render` first, then:  python3 tools/make-cv-pdf.py
Requires Google Chrome and a running `quarto preview` (default port 4200).
"""
import os, re, subprocess, sys, urllib.request

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC    = os.path.join(ROOT, "docs", "cv.html")
TMP    = os.path.join(ROOT, "docs", "_cvprint.html")
OUT    = os.path.join(ROOT, "assets", "cv", "Liebich-CV.pdf")
PORT   = os.environ.get("PREVIEW_PORT", "4200")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

NAME   = "LENA LIEBICH"
INST   = "HARVARD BUSINESS SCHOOL AI INSTITUTE, DIGITAL RESKILLING LAB"
ADDR   = "Cotting House 300, Boston, MA 02163"
CONTACT= "lliebich@hbs.edu &middot; lenaliebich.github.io"

PRINT_CSS = """
<style>
@page { size: A4; margin: 18mm 16mm 16mm 16mm; }

@media print {
  /* Site chrome has no place in a CV */
  .navbar, .nav-footer, #quarto-search, .quarto-title-block .subtitle,
  header#title-block-header, .kw-legend, .kw-topic, .kw-method,
  details.abstract > summary { display: none !important; }

  html, body { background: #fff !important; font-size: 9.6pt; line-height: 1.35; }
  body { color: #000 !important; }
  main { max-width: none !important; padding-top: 0 !important; margin-top: 0 !important; }
  a { color: #000 !important; border-bottom: none !important; text-decoration: none; }

  /* Doumi-style masthead */
  .cvpdf-head { text-align: center; margin: 0 0 14pt; }
  .cvpdf-head .n { font-size: 16pt; font-weight: 600; letter-spacing: .08em; }
  .cvpdf-head .i { font-size: 9.6pt; letter-spacing: .05em; margin-top: 4pt; }
  .cvpdf-head .d { font-size: 9.4pt; margin-top: 2pt; }
  .cvpdf-head .c { font-size: 9.4pt; margin-top: 2pt; }
  .cvpdf-stamp { text-align: right; font-size: 8pt; color: #444; margin-bottom: 6pt; }

  h2 {
    font-size: 11.5pt !important; font-weight: 600; margin: 13pt 0 5pt !important;
    padding-bottom: 2pt !important; border-bottom: .6pt solid #000 !important;
    break-after: avoid;
  }
  h2::after { display: none !important; }

  /* Entries: content left, dates right — as in the model CV */
  .cv-entry {
    grid-template-columns: 1fr 7.2rem !important;
    gap: .4rem !important; padding: 4.5pt 0 !important;
    border-bottom: none !important; break-inside: avoid;
  }
  .cv-entry > p:first-child { order: 2; text-align: right; }
  .cv-entry .cv-what { order: 1; }
  .cv-date  { color: #000 !important; font-size: 9.2pt !important; }
  .cv-where { color: #222 !important; }
  .cv-entry ul { margin: 1pt 0 0 !important; }
  li { margin-bottom: 0 !important; }

  /* Numbered publications with indented abstracts */
  main { counter-reset: pubnum; }
  .pub {
    counter-increment: pubnum; border-bottom: none !important;
    padding: 4pt 0 !important; break-inside: auto;
  }
  .pub-title::before { content: "[" counter(pubnum) "] "; font-weight: 600; }
  .pub-title { font-weight: 600; }
  .pub-venue, .pub-meta { color: #222 !important; }
  details.abstract { margin: 2pt 0 0 !important; }
  details.abstract > p {
    font-size: 8.8pt !important; color: #222 !important; margin: 2pt 0 0 !important;
    padding-left: 10pt !important; border-left: none !important; text-align: justify;
  }
  details.abstract > p::before { content: "Abstract: "; font-style: italic; }
  .badge-link {
    border: none !important; text-transform: none !important;
    font-size: 8.6pt !important; letter-spacing: 0 !important;
    padding: 0 !important; margin-right: .6rem !important; color: #222 !important;
  }
}
</style>
"""

def main():
    if not os.path.exists(SRC):
        sys.exit("docs/cv.html not found — run `quarto render` first.")
    html = open(SRC, encoding="utf-8").read()

    # Abstracts must be open or the browser will not print them
    html = html.replace('<details class="abstract">', '<details class="abstract" open>')

    # A "download this PDF" button has no place inside the PDF itself
    html = re.sub(r'<p>\s*<a[^>]*Liebich-CV\.pdf[^>]*>.*?</a>\s*</p>', '', html, flags=re.S)

    head = (f'<div class="cvpdf-stamp">Last updated: September 2026</div>'
            f'<div class="cvpdf-head">'
            f'<div class="n">{NAME}</div>'
            f'<div class="i">{INST}</div>'
            f'<div class="d">{ADDR}</div>'
            f'<div class="c">{CONTACT}</div>'
            f'</div>')
    html = html.replace("</head>", PRINT_CSS + "</head>", 1)
    html = re.sub(r'(<main[^>]*>)', r'\1' + head, html, count=1)

    open(TMP, "w", encoding="utf-8").write(html)
    try:
        url = f"http://127.0.0.1:{PORT}/_cvprint.html"
        urllib.request.urlopen(url, timeout=10).read()
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        subprocess.run([CHROME, "--headless=new", "--disable-gpu",
                        "--no-pdf-header-footer", "--virtual-time-budget=10000",
                        f"--print-to-pdf={OUT}", url],
                       check=True, capture_output=True, timeout=180)
        print(f"wrote {OUT} ({os.path.getsize(OUT)//1024} KB)")
    finally:
        if os.path.exists(TMP):
            os.remove(TMP)

if __name__ == "__main__":
    main()
