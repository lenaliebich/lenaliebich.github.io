#!/usr/bin/env python3
"""Build assets/cv/Liebich-CV.pdf from the rendered CV page.

The PDF is generated from docs/cv.html, so it always matches the website.
Page numbers are stamped in a second pass: Chrome's CLI cannot render CSS
page counters, and Paged.js does not finish laying out before headless
Chrome snapshots the page.

Run `quarto render` first, then:  python3 tools/make-cv-pdf.py
Requires Google Chrome and pypdf. The page is served by a throwaway local
server on docs/, not by `quarto preview`, which can hand back a stale copy.
The PDF is written to assets/cv/ and mirrored into docs/assets/cv/.
"""
import functools, http.server, os, re, shutil, subprocess, sys, tempfile, threading, urllib.request

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC     = os.path.join(ROOT, "docs", "cv.html")
TMP     = os.path.join(ROOT, "docs", "_cvprint.html")
TMPOVL  = os.path.join(ROOT, "docs", "_cvnums.html")
OUT     = os.path.join(ROOT, "assets", "cv", "Liebich-CV.pdf")
DOCSOUT = os.path.join(ROOT, "docs", "assets", "cv", "Liebich-CV.pdf")
CHROME  = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

NAME    = "LENA LIEBICH"
INST    = "HARVARD BUSINESS SCHOOL AI INSTITUTE, DIGITAL RESKILLING LAB"
ADDR    = "Cotting House 300, Boston, MA 02163"
EMAIL   = "lliebich@hbs.edu"
SITE    = "lenaliebich.github.io"

# Inline so the icons survive in the PDF; they inherit the text colour
ICON_MAIL = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
             'stroke-linecap="round" stroke-linejoin="round">'
             '<rect x="2.5" y="4.5" width="19" height="15" rx="2.5"/>'
             '<path d="M3.2 6.6 12 13.1l8.8-6.5"/></svg>')
ICON_SITE = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
             'stroke-linecap="round" stroke-linejoin="round">'
             '<circle cx="12" cy="12" r="9.2"/><path d="M2.8 12h18.4"/>'
             '<path d="M12 2.8c2.5 2.7 3.8 5.8 3.8 9.2S14.5 18.5 12 21.2'
             'c-2.5-2.7-3.8-5.8-3.8-9.2S9.5 5.5 12 2.8z"/></svg>')

# Real anchors: without them a reader guesses where the address ends and clips it
CONTACT = (f'<a href="mailto:{EMAIL}">{ICON_MAIL}{EMAIL}</a>'
           f'<span class="sep">&middot;</span>'
           f'<a href="https://{SITE}">{ICON_SITE}{SITE}</a>')
STAMP   = "Last updated: September 2026"

TEAL, TEAL_DK, TEAL_TINT = "#0f766e", "#0a544e", "#eaf3f1"

PRINT_CSS = f"""
<style>
@page {{ size: A4; margin: 17mm 16mm 17mm 16mm; }}

@media print {{
  /* Site chrome has no place in a CV */
  .navbar, .nav-footer, #quarto-search, .quarto-title-block .subtitle,
  header#title-block-header, .kw-legend, .kw-topic, .kw-method,
  details.abstract > summary {{ display: none !important; }}

  html, body {{ background: #fff !important; font-size: 9.6pt; line-height: 1.36; }}
  body {{ color: #1f2328 !important; font-family: "Spectral", Georgia, serif; }}
  main {{ max-width: none !important; padding: 0 !important; margin: 0 !important; }}
  a {{ color: inherit; border-bottom: none !important; text-decoration: none; }}

  /* Masthead */
  .cvpdf-stamp {{ text-align: right; font-family: "IBM Plex Sans", sans-serif;
                 font-size: 7.8pt; color: #6b7280; margin-bottom: 5pt; }}
  .cvpdf-head {{ text-align: center; margin: 0 0 13pt; padding-bottom: 9pt;
                border-bottom: 1pt solid {TEAL_DK}; }}
  .cvpdf-head .n {{ font-size: 16pt; font-weight: 600; letter-spacing: .08em; color: {TEAL_DK}; }}
  .cvpdf-head .i {{ font-size: 9.4pt; letter-spacing: .05em; margin-top: 4pt; }}
  .cvpdf-head .d {{ font-size: 9.2pt; margin-top: 2pt; color: #444; }}
  .cvpdf-head .c {{ font-family: "IBM Plex Sans", sans-serif; font-size: 8.8pt;
                   margin-top: 3pt; color: #444; }}
  .cvpdf-head .c a {{ color: #444 !important; text-decoration: none !important;
                     white-space: nowrap; }}
  .cvpdf-head .c .sep {{ margin: 0 6pt; color: #9aa0a6; }}
  .cvpdf-head .c svg {{ width: 8.4pt; height: 8.4pt; vertical-align: -1pt;
                       margin-right: 2.8pt; stroke: {TEAL_DK}; }}

  /* Section headings keep the site's grey rule plus teal tab */
  h2 {{
    font-size: 11.5pt !important; font-weight: 600; color: #1f2328 !important;
    margin: 13pt 0 5pt !important; padding-bottom: 2.5pt !important;
    border-bottom: .6pt solid #d9d6d0 !important; position: relative;
    break-after: avoid;
  }}
  h2::after {{
    content: "" !important; display: block !important; position: absolute;
    left: 0; bottom: -.6pt; width: 26pt; height: 1.4pt; background: {TEAL};
  }}

  /* Entries: institution and role left, location over years right */
  .cv-entry {{
    grid-template-columns: 1fr auto !important; gap: .9rem !important;
    padding: 4.5pt 0 !important; border-bottom: none !important; break-inside: avoid;
  }}
  .cv-what p:nth-of-type(n+3) {{ color: #4b5563 !important; font-size: 9pt !important; }}
  .cv-meta {{ font-family: "IBM Plex Sans", sans-serif; font-size: 8.4pt !important;
             color: #4b5563 !important; text-align: right; white-space: nowrap; }}
  .cv-meta .cv-date {{ color: #1f2328 !important; }}
  .cv-row {{ grid-template-columns: 6.5rem 1fr !important; padding: 2.5pt 0 !important;
            border-bottom: none !important; }}
  .cv-label {{ font-family: "IBM Plex Sans", sans-serif; font-size: 8.4pt !important;
              color: #4b5563 !important; }}
  h3 {{ font-size: 10pt !important; margin: 8pt 0 1pt !important; color: #4b5563 !important;
       break-after: avoid; }}
  .cv-entry ul {{ margin: 1pt 0 0 !important; }}
  li {{ margin-bottom: 0 !important; }}

  /* Numbered publications with indented abstracts */
  main {{ counter-reset: pubnum; }}
  .pub {{ counter-increment: pubnum; border-bottom: none !important;
         padding: 5pt 0 !important; break-inside: auto; }}
  .pub-title::before {{ content: "[" counter(pubnum) "] "; font-weight: 600; color: {TEAL}; }}
  .pub-title {{ font-weight: 600; }}
  .pub-venue, .pub-meta {{ color: #4b5563 !important; }}
  details.abstract {{ margin: 2.5pt 0 0 !important; }}
  details.abstract > p {{
    font-size: 8.7pt !important; color: #4b5563 !important; margin: 2pt 0 0 !important;
    padding-left: 9pt !important; border-left: 1pt solid #dbe7e4 !important;
    text-align: justify;
  }}
  details.abstract > p::before {{ content: "Abstract: "; font-style: italic; }}

  /* Link chips: visible, teal, matching the site's squared tags */
  .pub .badge-link {{
    display: inline-block !important;
    font-family: "IBM Plex Sans", sans-serif !important;
    font-size: 7.6pt !important; font-weight: 500 !important;
    letter-spacing: .05em !important; text-transform: uppercase !important;
    color: {TEAL_DK} !important; background: {TEAL_TINT} !important;
    border: .5pt solid rgba(15, 118, 110, .45) !important;
    border-radius: 2px !important; padding: 1.2pt 4.5pt !important;
    margin: 3pt 3pt 0 0 !important;
  }}
}}
</style>
"""

def chrome_pdf(url, out, budget=15000):
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--virtual-time-budget={budget}", f"--print-to-pdf={out}", url],
                   check=True, capture_output=True, timeout=240)

class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass

def serve_docs():
    # Our own server on a free port, so every run prints the files just written
    handler = functools.partial(NoCacheHandler, directory=os.path.join(ROOT, "docs"))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"

def overlay_html(n):
    rows = "\n".join(
        f'<div class="pg"><span>Page {i} of {n}</span></div>' for i in range(1, n + 1))
    return f"""<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400&display=swap" rel="stylesheet">
<style>
@page {{ size: A4; margin: 0; }}
body {{ margin: 0; font-family: "IBM Plex Sans", sans-serif; }}
.pg {{ width: 210mm; height: 296.6mm; position: relative; break-after: page; }}
.pg:last-child {{ break-after: auto; }}
.pg span {{ position: absolute; bottom: 9.5mm; left: 0; right: 0;
           text-align: center; font-size: 7.8pt; color: #6b7280; }}
</style></head><body>{rows}</body></html>"""

def main():
    if not os.path.exists(SRC):
        sys.exit("docs/cv.html not found - run `quarto render` first.")
    html = open(SRC, encoding="utf-8").read()

    # Policy work is listed in the PDF, but its abstracts are left out
    pol = re.search(r'<section id="policy-work-pre-phd" class="level2">.*?'
                    r'(?=<section id="[^"]+" class="level2">|</main>)', html, flags=re.S)
    if pol:
        trimmed = re.sub(r'<details class="abstract">.*?</details>', "", pol.group(0), flags=re.S)
        html = html[:pol.start()] + trimmed + html[pol.end():]

    # Abstracts must be open or the browser will not print them
    html = html.replace('<details class="abstract">', '<details class="abstract" open>')
    # A "download this PDF" button has no place inside the PDF itself
    html = re.sub(r'<p>\s*<a[^>]*Liebich-CV\.pdf[^>]*>.*?</a>\s*</p>', "", html, flags=re.S)

    head = (f'<div class="cvpdf-stamp">{STAMP}</div>'
            f'<div class="cvpdf-head">'
            f'<div class="n">{NAME}</div><div class="i">{INST}</div>'
            f'<div class="d">{ADDR}</div><div class="c">{CONTACT}</div></div>')
    html = html.replace("</head>", PRINT_CSS + "</head>", 1)
    html = re.sub(r"(<main[^>]*>)", r"\1" + head, html, count=1)
    open(TMP, "w", encoding="utf-8").write(html)

    server, base_url = serve_docs()
    try:
        from pypdf import PdfReader, PdfWriter
        base_path = os.path.join(tempfile.gettempdir(), "_cv_base.pdf")
        ovl_path = os.path.join(tempfile.gettempdir(), "_cv_ovl.pdf")

        url = f"{base_url}/_cvprint.html"
        urllib.request.urlopen(url, timeout=10).read()
        chrome_pdf(url, base_path)

        n = len(PdfReader(base_path).pages)
        open(TMPOVL, "w", encoding="utf-8").write(overlay_html(n))
        ovl_url = f"{base_url}/_cvnums.html"
        urllib.request.urlopen(ovl_url, timeout=10).read()
        chrome_pdf(ovl_url, ovl_path)

        base, ovl = PdfReader(base_path), PdfReader(ovl_path)
        if len(ovl.pages) != n:
            print(f"warning: overlay has {len(ovl.pages)} pages, content has {n}; "
                  "page numbers not stamped", file=sys.stderr)
            writer = PdfWriter(clone_from=base_path)
        else:
            writer = PdfWriter()
            for i, page in enumerate(base.pages):
                page.merge_page(ovl.pages[i])
                writer.add_page(page)
            # Merging leaves the streams uncompressed; squeeze them back down
            for page in writer.pages:
                try:
                    page.compress_content_streams()
                except Exception:
                    pass
            try:
                writer.compress_identical_objects()
            except Exception:
                pass

        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "wb") as fh:
            writer.write(fh)
        # quarto render copied the old PDF into docs/; keep the published copy in step
        os.makedirs(os.path.dirname(DOCSOUT), exist_ok=True)
        shutil.copyfile(OUT, DOCSOUT)
        print(f"wrote {OUT} ({os.path.getsize(OUT)//1024} KB, {n} pages) and docs/ copy")
    finally:
        server.shutdown()
        if not os.environ.get("KEEP_TMP"):
            for f in (TMP, TMPOVL):
                if os.path.exists(f):
                    os.remove(f)

if __name__ == "__main__":
    main()
