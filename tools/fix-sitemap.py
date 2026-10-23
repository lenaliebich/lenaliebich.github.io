"""List the home page in docs/sitemap.xml as "/" rather than "/index.html".

Quarto writes every page into the sitemap under its file name, but each page's
canonical URL (canonical-url: true in _quarto.yml) gives the home page as "/".
A sitemap that disagrees with the canonical URL sends search engines two
addresses for one page, so this rewrites the one entry after every render.

Run automatically by Quarto as a post-render script; see _quarto.yml.
"""
import os

path = os.path.join(os.environ.get("QUARTO_PROJECT_OUTPUT_DIR", "docs"), "sitemap.xml")
if os.path.exists(path):
    with open(path, encoding="utf-8") as fh:
        sitemap = fh.read()
    fixed = sitemap.replace("/index.html</loc>", "/</loc>")
    if fixed != sitemap:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(fixed)
