# Proceedings

Proceedings of the Institute for a Christian Machine Intelligence

## About

This repository contains the working paper series of the Institute for a Christian Machine Intelligence (ICMI). Working papers are pre-publication research documents exploring the intersection of Christian theology and machine intelligence.

## File Naming Convention

All working papers follow the format:

```
ICMI-[ID]-[short-title].[ext]
```

- **ID**: Zero-padded three-digit sequence number (e.g., `001`, `002`) for the main series, or a single letter (e.g., `A`, `B`) for earlier papers
- **short-title**: Lowercase, hyphen-separated summary of the paper's subject
- **ext**: `.md` for Markdown

Each paper is authored in Markdown. The site build (GitHub Actions) automatically generates HTML pages and PDFs from the `.md` source.

Examples:
- `ICMI-001-attention-prayer-paradigm.md`
- `ICMI-A-biblical-render.md`

## Working Paper Format

Every working paper should include:

1. **Title and designation**: The paper title followed by its ICMI Working Paper number (e.g., "ICMI Working Paper No. 1")
2. **Abstract**: A concise summary of the paper's argument and contributions
3. **Numbered sections**: Introduction, body sections, proposed experiments (where applicable), and conclusion
4. **Biblical citations**: References to scripture should use the English Standard Version (ESV) unless otherwise noted, with book, chapter, and verse specified inline (e.g., Psalm 46:10, ESV)
5. **Technical citations**: All technical claims must be supported by inline citations in author-date format (e.g., Vaswani et al., 2017). Every entry in the bibliography must appear at least once in the body text.
6. **Bibliography**: A complete list of references at the end of the paper, alphabetized by first author's surname

## Technical Architecture

### Overview

The site uses a custom bash build pipeline (no static site generator). Markdown files are the single source of truth, producing both HTML pages and two-column PDF papers. The site is deployed to GitHub Pages at [icmi-proceedings.com](https://icmi-proceedings.com).

### Directory Structure

```
Proceedings/
├── ICMI-*.md                    # Source papers (markdown, single source of truth)
├── ICMI-*.tex                   # Generated LaTeX (do NOT edit directly)
├── CNAME                        # GitHub Pages custom domain
├── favicon.png, og-image.jpg    # Site assets
├── scripts/
│   ├── build-site.sh            # Main build orchestrator
│   ├── md-to-tex.sh             # Markdown → LaTeX converter
│   ├── site-template.html       # Pandoc HTML template (paper pages)
│   ├── icmi-template.tex        # Pandoc LaTeX template (PDF output)
│   ├── crosslink-bibliography.py  # Post-processor: hyperlinks between papers
│   └── serve.py                 # Local dev server (port 8787)
├── _site/                       # Generated output (gitignored)
│   ├── index.html               # Landing page (generated inline by build script)
│   ├── ICMI-*.html              # Paper HTML pages
│   └── ICMI-*.pdf               # Paper PDFs
└── .github/workflows/
    └── build-site.yml           # CI/CD: build + deploy to GitHub Pages
```

### Build Pipeline

The build is driven by `scripts/build-site.sh`. On every push to `main`, GitHub Actions runs the full pipeline:

```
ICMI-*.md (markdown source)
    │
    ├──→ pandoc + site-template.html ──→ _site/ICMI-*.html
    │
    └──→ md-to-tex.sh ──→ ICMI-*.tex ──→ pdflatex (×2) ──→ _site/ICMI-*.pdf

Metadata extraction (title, author, abstract, date, paper number)
    │
    └──→ index.html (generated inline in build-site.sh, not from a template)

Post-processing:
    crosslink-bibliography.py ──→ hyperlinks ICMI cross-references in HTML
    Asset copying ──→ favicons, images, CNAME → _site/
```

**Key points:**
- `.tex` files are regenerated on every build from `.md` via `md-to-tex.sh` — never edit them directly
- `pdflatex` runs twice per paper for cross-references
- The index page is generated directly in `build-site.sh` using heredocs, not from a pandoc template
- `crosslink-bibliography.py` scans HTML output and converts plain-text references like "ICMI Working Paper No. 1" into hyperlinks

### Templates

**`scripts/site-template.html`** — Pandoc HTML5 template for individual paper pages. Uses `$variable$` syntax for metadata injection (title, abstract, PDF link, OG tags). Includes embedded CSS and JavaScript for:
- PDF download link injection after the "Working Paper" line
- Article outline generation from h2 headings
- MathJax for math rendering

**`scripts/icmi-template.tex`** — Pandoc LaTeX template for two-column conference-style PDFs. Custom section formatting, abstract styling, headers/footers with paper number and page numbers.

### Styling

All CSS is embedded inline (no external stylesheets):
- **Font**: Crimson Pro (Google Fonts), serif fallbacks
- **Layout**: Single-column, `max-width: 42rem`, responsive at 600px breakpoint
- **Index page styles**: Written directly in `build-site.sh` heredoc
- **Paper page styles**: In `site-template.html`

### Local Development

```bash
# Build the site
bash scripts/build-site.sh

# Serve locally
python3 scripts/serve.py        # serves _site/ on http://localhost:8787
```

**Build dependencies**: pandoc, pdflatex (texlive), Python 3.

### Deployment

GitHub Actions (`.github/workflows/build-site.yml`) triggers on push to `main`:
1. Installs pandoc + texlive on Ubuntu
2. Runs `build-site.sh`
3. Deploys `_site/` to GitHub Pages via `actions/deploy-pages@v4`

### Adding New Pages

To add a non-paper page (e.g., a VirtueBench visualizer):
1. Create the HTML/JS/CSS files in the repo root or a subdirectory
2. Add a copy step in `build-site.sh` to include the files in `_site/`
3. Optionally link from the index page by editing the heredoc section in `build-site.sh`

Static assets (images, JS, CSS files) placed in the repo root are not automatically copied to `_site/` — only `*.png`, `*.jpg`, `*.svg`, and favicon files are. You must add explicit copy commands for other file types.

## Contributing

To propose a new working paper:

1. Claim the next available number in the sequence
2. Create a `.md` file following the naming convention above
3. Ensure all citations (biblical and technical) are verified for accuracy
4. Submit a pull request for review

## Current Papers

| No. | Title | Authors |
|-----|-------|---------|
| 001 | [Attention Is All You Need: The Prayer Paradigm of the Transformer](ICMI-001-attention-prayer-paradigm.md) | Tim Hwang |
| 002 | ["The Lord Is My Strength and My Shield": Imprecatory Psalm Injection and Cardinal Virtue Simulation in Large Language Models](ICMI-002-imprecatory-psalms-virtue-bench.md) | Christopher McCaffery |
| 003 | [Toward a Theology of Machine Temptation: Four Models for VirtueBench V2](ICMI-003-temptation-taxonomy-virtuebench.md) | Tim Hwang |
| 004 | [Courage and Practical Preservation in Frontier Assistant Models](ICMI-004-courage-practical-preservation.md) | Henry Zhu |
| 005 | ["The Letter Killeth, but the Spirit Giveth Life": Biblical Text Framing and the Degradation of Constraint Compliance in Large Language Models](ICMI-005-biblical-framing-constraint-compliance.md) | Tim Hwang |
| 006 | [What the Models Already Know: 67 Billion Tokens of Christian Moral Reasoning in the Pretraining Corpus](ICMI-006-christian-tokens.md) | Tim Hwang |

## Earlier Papers

| ID | Title | Authors |
|----|-------|---------|
| A | ["Let His Praise Be Continually in My Mouth": Measuring the Effect of Psalm Injection on LLM Ethical Alignment](ICMI-A-psalm-injection-alignment.md) | Tim Hwang |
| B | ["The Fear of the Lord Is the Beginning of Knowledge": Comparing Proverbs and Psalms Injection Effects on LLM Ethical Alignment](ICMI-B-proverbs-psalms-comparison.md) | Tim Hwang |
| C | [Investigating the Utilitarianism Anomaly: Control Experiments for Psalm-Induced Performance Gains](ICMI-C-utilitarianism-anomaly.md) | Tim Hwang |
| D | [biblical-render: Design and Validation of a Biblical Text Style Transfer Tool](ICMI-D-biblical-render.md) | Tim Hwang |
| E | [Virtue Under Pressure: Testing the Cardinal Virtues in Language Models Through Temptation](ICMI-E-virtue-under-pressure.md) | Tim Hwang |

