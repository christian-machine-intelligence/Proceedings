#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
OUT_DIR="$REPO_DIR/_site"

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

# ---------- Site assets: the design's CSS, scripts, engravings, footer scenes and fonts ----------
# assets/ holds site.css, field.js, engrave.js, footer/, art/ and the open-licence fonts (Doves Italic,
# Ysabeau Office, Paper Mono). Doves Type itself is licensed only for icmi-proceedings.com and is never
# committed: CI checks it out of the private brand repo into .brand/ (see the workflow), and a local build
# takes it from $DOVES_FONTS_DIR. Without it the site still builds and falls back to Georgia.
cp -R "$REPO_DIR/assets/." "$OUT_DIR/"
mkdir -p "$OUT_DIR/fonts"
doves_found=0
for dir in "${DOVES_FONTS_DIR:-}" "$REPO_DIR/.brand/fonts/web"; do
  [ -n "$dir" ] || continue
  for f in "$dir"/DovesType-*.woff2; do
    [ -f "$f" ] || continue
    cp "$f" "$OUT_DIR/fonts/"
    doves_found=1
  done
done
if [ "$doves_found" = 0 ]; then
  # In CI, stop: a deploy without Doves Type would replace the live site with fallback fonts. Set
  # ALLOW_FALLBACK_FONTS=1 to build anyway (for example to test the build without the secret).
  if [ -n "${GITHUB_ACTIONS:-}" ] && [ -z "${ALLOW_FALLBACK_FONTS:-}" ]; then
    echo "::error::Doves Type not found. Set the BRAND_DEPLOY_KEY or BRAND_READ_TOKEN secret (README, Fonts). Nothing was deployed."
    exit 1
  fi
  echo "WARNING: Doves Type fonts not found (set DOVES_FONTS_DIR, or provide .brand/fonts/web); using fallback fonts"
fi

# ---------- Render every page: papers, homepage, papers index, Primer, About, Fundraising ----------
# scripts/render-site.py runs pandoc over the Markdown and sets it in the page templates (scripts/templates/).
# Paper metadata for the homepage and the papers index is extracted from the papers themselves.
python3 "$SCRIPT_DIR/render-site.py" "$REPO_DIR" "$OUT_DIR"

# ---------- Generate PDFs ----------
# SKIP_PDF=1 skips this step (for local builds without LaTeX); CI never sets it.
if [ -n "${SKIP_PDF:-}" ]; then
  echo "SKIP_PDF set: skipping PDF generation"
else
TEX_TEMPLATE="$SCRIPT_DIR/icmi-template.tex"
for md in "$REPO_DIR"/ICMI-*.md; do
  [ -f "$md" ] || continue
  basename="$(basename "$md" .md)"
  tex="$REPO_DIR/$basename.tex"
  pdf="$REPO_DIR/$basename.pdf"

  # Regenerate .tex from .md with conference-style template
  echo "Generating $basename.tex ..."
  bash "$SCRIPT_DIR/md-to-tex.sh" "$md" "$tex"

  # Compile PDF (twice for cross-references)
  echo "Compiling $basename.pdf ..."
  (cd "$REPO_DIR" && pdflatex -interaction=nonstopmode "$tex" >/dev/null 2>&1; \
   pdflatex -interaction=nonstopmode "$tex" >/dev/null 2>&1) || true

  # Copy PDF to site output
  if [ -f "$pdf" ]; then
    cp "$pdf" "$OUT_DIR/$basename.pdf"
  else
    echo "WARNING: Failed to generate $basename.pdf"
  fi

  # Clean up auxiliary files
  rm -f "$REPO_DIR/$basename.aux" "$REPO_DIR/$basename.log" "$REPO_DIR/$basename.out" \
        "$REPO_DIR/$basename.toc" "$REPO_DIR/$basename.nav" "$REPO_DIR/$basename.snm"
done
fi

# ---------- Cross-link bibliography entries ----------
echo "Cross-linking bibliography references ..."
python3 "$SCRIPT_DIR/crosslink-bibliography.py" "$OUT_DIR"

# Copy favicon files
for fav in "$REPO_DIR"/favicon*.png; do
  [ -f "$fav" ] && cp "$fav" "$OUT_DIR/"
done

# Copy image assets referenced by papers
for img in "$REPO_DIR"/*.png "$REPO_DIR"/*.jpg "$REPO_DIR"/*.svg; do
  [ -f "$img" ] && [[ "$(basename "$img")" != favicon* ]] && cp "$img" "$OUT_DIR/"
done

# Copy CNAME if it exists
if [ -f "$REPO_DIR/CNAME" ]; then
  cp "$REPO_DIR/CNAME" "$OUT_DIR/CNAME"
fi

echo "Site built in $OUT_DIR/"
