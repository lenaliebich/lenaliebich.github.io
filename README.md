# Academic website

Personal academic site built with [Quarto](https://quarto.org), live at
<https://lenaliebich.github.io>.

The repository **must** be named `lenaliebich.github.io`. That name is what
makes GitHub serve the site from the domain root, and the site assumes a root
path in three places: `site-url` in `_quarto.yml`, the generated
`docs/sitemap.xml` and `docs/robots.txt`, and the `/cv.html` link Quarto writes
into the About page. Renaming the repo breaks all three.

## One-time GitHub Pages setup

In the repository on GitHub: **Settings → Pages → Build and deployment**, set
*Source* to **Deploy from a branch**, then branch `main` and folder **`/docs`**.
No Actions workflow is needed — the rendered site is committed.

## Local workflow

```bash
quarto preview          # live-reloading local preview; prints the URL it picks
quarto render           # build the static site into docs/
```

`quarto preview` watches the files and refreshes the browser on every save.
Nothing is published until you commit and push.

## Publishing

```bash
quarto render                   # always render before committing
python3 tools/make-cv-pdf.py    # only if cv.qmd or _publications.qmd changed
git add -A
git commit -m "Update site"
git push
```

`docs/` is the published site, so a commit without a fresh `quarto render`
publishes stale pages. GitHub Pages rebuilds within a minute or two.

## Layout

| Path | What it is |
|---|---|
| `_quarto.yml` | Site config: title, navbar, theme, footer |
| `index.qmd` | Landing page / about |
| `research.qmd` | Research focus + publications, work in progress, policy papers |
| `cv.qmd` | Web CV |
| `_publications.qmd` | Publication list, included by both `research.qmd` and `cv.qmd` |
| `assets/styles.scss` | Custom styling |
| `assets/img/` | Web-sized photos (`originals/` is local-only, not committed) |
| `assets/cv/` | CV PDF |
| `assets/files/` | Paper PDFs, slides, posters |
| `tools/make-cv-pdf.py` | Builds the CV PDF from the rendered CV page |
| `docs/` | Rendered output — committed, served by GitHub Pages |

Publications are written by hand in `_publications.qmd`; there is no BibTeX
file. To switch to citations, add a `.bib` file and point `bibliography:` at it
in `_quarto.yml`.

## Regenerating the CV PDF

The PDF at `assets/cv/Liebich-CV.pdf` is generated from the rendered CV page,
so it always matches the website:

```bash
quarto render
python3 tools/make-cv-pdf.py
```

Requires Google Chrome and `pypdf` (`pip3 install --user pypdf`).
The script serves `docs/` itself, so `quarto preview` does not need to be
running, and it also updates the published copy in `docs/assets/cv/`.
