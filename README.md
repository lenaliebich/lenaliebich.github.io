# Academic website

Personal academic site built with [Quarto](https://quarto.org), published with
GitHub Pages from the `docs/` folder.

## Local workflow

```bash
quarto preview          # live-reloading local site at http://localhost:4200
quarto render           # build the static site into docs/
```

`quarto preview` watches the files and refreshes the browser on every save.
Nothing is published until you commit and push.

## Publishing

```bash
quarto render
git add -A
git commit -m "Update site"
git push
```

GitHub Pages rebuilds within a minute or two.

## Layout

| Path | What it is |
|---|---|
| `_quarto.yml` | Site config: title, navbar, theme, footer |
| `index.qmd` | Landing page / about |
| `research.qmd` | Research focus + publications, work in progress, policy papers |
| `cv.qmd` | Web CV |
| `bib/refs.bib` | BibTeX references for inline citations |
| `assets/styles.scss` | Custom styling |
| `assets/img/` | Photos and images |
| `assets/cv/` | CV PDF |
| `assets/files/` | Paper PDFs, slides, posters |
| `docs/` | Rendered output — committed, served by GitHub Pages |
