#!/usr/bin/env bash
set -euo pipefail

# Generate .tex from .md and .pdf from .tex for ICMI papers.
# Skips files that already exist (never overwrites).

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATE="$SCRIPT_DIR/icmi-template.tex"

generated=0

cd "$REPO_DIR"

# --- Step 1: Generate missing .tex files from .md ---
for md in ICMI-*.md; do
    [ -f "$md" ] || continue
    tex="${md%.md}.tex"
    if [ -f "$tex" ]; then
        echo "SKIP $tex (already exists)"
        continue
    fi
    echo "GENERATING $tex from $md"
    pandoc "$md" \
        --from markdown \
        --to latex \
        --template "$TEMPLATE" \
        --standalone \
        --wrap=none \
        -o "$tex"
    generated=$((generated + 1))
done

# --- Step 2: Generate missing .pdf files from .tex ---
for tex in ICMI-*.tex; do
    [ -f "$tex" ] || continue
    pdf="${tex%.tex}.pdf"
    if [ -f "$pdf" ]; then
        echo "SKIP $pdf (already exists)"
        continue
    fi
    echo "GENERATING $pdf from $tex"
    # Run pdflatex twice to resolve cross-references
    pdflatex -interaction=nonstopmode -halt-on-error "$tex" >/dev/null 2>&1
    pdflatex -interaction=nonstopmode -halt-on-error "$tex" >/dev/null 2>&1
    # Clean up auxiliary files
    base="${tex%.tex}"
    rm -f "$base.aux" "$base.log" "$base.out" "$base.toc" "$base.nav" "$base.snm"
    generated=$((generated + 1))
done

if [ "$generated" -gt 0 ]; then
    echo "Generated $generated file(s)."
else
    echo "Nothing to generate — all files up to date."
fi
