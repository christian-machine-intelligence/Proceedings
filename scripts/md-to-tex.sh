#!/usr/bin/env bash
# Convert a single ICMI paper .md to .tex using the conference-style template.
# Extracts metadata (title, author, paper number, date, abstract) and passes
# them to pandoc so they populate the template correctly.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE="$SCRIPT_DIR/icmi-template.tex"

md="$1"
tex="$2"

# --- Extract metadata ---
title="$(grep -m1 '^# ' "$md" | sed 's/^# //')"

# Try numeric "Working Paper No. N" first, then letter "Working Paper X"
paper_num="$(grep -m1 'Working Paper No\.' "$md" | sed 's/.*Working Paper No\. *//' | sed 's/[^0-9]//g' || true)"
if [ -z "$paper_num" ]; then
  paper_num="$(grep -m1 'Working Paper [A-Z]' "$md" | sed 's/.*Working Paper *//' | sed 's/[^A-Za-z]//g' || true)"
fi

# Compute label: "No. N" for numeric, just "X" for letter
if [[ "$paper_num" =~ ^[0-9]+$ ]]; then
  paper_label="No. ${paper_num}"
else
  paper_label="$paper_num"
fi

author="$(grep -m1 '^\*\*Author:\*\*' "$md" | sed 's/^\*\*Author:\*\* *//' | sed 's/[[:space:]]*$//' || true)"
if [ -z "$author" ]; then
  author="Institute for a Christian Machine Intelligence"
fi

paper_date="$(grep -m1 '^\*\*Date:\*\*' "$md" | sed 's/^\*\*Date:\*\* *//' | sed 's/[[:space:]]*$//' || true)"

# Extract abstract: text between "**Abstract.**" and the next "---" or "## ".
# Preserve paragraph breaks (empty source lines → \n\n) so pandoc below can
# render them as distinct LaTeX paragraphs in the abstract block.
abstract_md="$(awk '
  /^\*\*Abstract\.\*\*/ {
    sub(/^\*\*Abstract\.\*\* */, "")
    text = $0
    prev_blank = 0
    while ((getline line) > 0) {
      if (line ~ /^---/ || line ~ /^## /) break
      if (line == "") { prev_blank = 1; continue }
      if (prev_blank) { text = text "\n\n" line; prev_blank = 0 }
      else           { text = text " " line }
    }
    print text
    exit
  }
' "$md")"

# Convert abstract markdown to LaTeX so *italics*, **bold**, and paragraph
# breaks in the abstract render correctly. Without this, the raw markdown
# passed through --variable would surface as literal asterisks in the PDF.
if [ -n "$abstract_md" ]; then
  abstract="$(printf '%s\n' "$abstract_md" | pandoc --from markdown --to latex --wrap=none)"
else
  abstract=""
fi

# --- Create body-only markdown (strip header block) ---
# Remove everything before the first ## section heading
body_md="$(awk '
  BEGIN { found = 0 }
  /^## [0-9]+\./ { found = 1 }
  found { print }
' "$md")"

# --- Escape % signs for LaTeX ---
# Percent signs in markdown become LaTeX comments and truncate lines.
# The abstract is already LaTeX (converted via pandoc above, which emitted
# properly escaped \% already) so we only escape the body here.
body_md="$(echo "$body_md" | sed 's/%/\\%/g')"

# --- Run pandoc with metadata ---
# --shift-heading-level-by=-1 promotes ## to \section, ### to \subsection
# --number-sections is NOT used because papers have manual section numbers
echo "$body_md" | pandoc \
  --from markdown \
  --to latex \
  --template "$TEMPLATE" \
  --standalone \
  --wrap=none \
  --shift-heading-level-by=-1 \
  --metadata title="$title" \
  --metadata author="$author" \
  --metadata paper-number="$paper_num" \
  --metadata paper-label="$paper_label" \
  ${paper_date:+--metadata date="$paper_date"} \
  --variable abstract="$abstract" \
  -o "$tex"

# Post-process the generated .tex file (cross-platform sed -i)
sedi() { if [[ "$OSTYPE" == darwin* ]]; then sed -i '' "$@"; else sed -i "$@"; fi; }

# 1. Use unnumbered sections (papers have manual numbers like "1. Introduction")
sedi 's/\\section{/\\section*{/g; s/\\subsection{/\\subsection*{/g; s/\\subsubsection{/\\subsubsection*{/g' "$tex"

# 2. Replace longtable with tabular (longtable doesn't work in twocolumn mode)
sedi 's/\\begin{longtable}/\\begin{tabular}/g; s/\\end{longtable}/\\end{tabular}/g' "$tex"
# Remove longtable-specific commands
sedi '/\\endhead/d; /\\endfoot/d; /\\endlastfoot/d; /\\endfirsthead/d' "$tex"

# 2b. Wrap tabular in resizebox to prevent column overflow
sedi 's/\\begin{tabular}/\\resizebox{\\columnwidth}{!}{\\begin{tabular}/g' "$tex"
sedi 's/\\end{tabular}/\\end{tabular}}/g' "$tex"

# 3. Constrain image width to column width
sedi 's/\\includegraphics{/\\includegraphics[width=\\columnwidth]{/g' "$tex"
# Fix case where pandoc already added options
sedi 's/\\includegraphics\[width=\\columnwidth\]\[/\\includegraphics[width=\\columnwidth,/g' "$tex"
