#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATE="$SCRIPT_DIR/site-template.html"
OUT_DIR="$REPO_DIR/_site"

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

# ---------- Build individual paper pages ----------
for md in "$REPO_DIR"/ICMI-*.md; do
  [ -f "$md" ] || continue
  basename="$(basename "$md" .md)"
  echo "Building $basename.html ..."
  pandoc "$md" \
    --from markdown \
    --to html5 \
    --template "$TEMPLATE" \
    --standalone \
    --mathjax \
    --wrap=none \
    -o "$OUT_DIR/$basename.html"
done

# ---------- Generate PDFs ----------
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

# ---------- Build index page ----------
echo "Building index.html ..."

NUMBERED_ITEMS=""
LETTER_ITEMS=""

# Collect papers and split into numbered (ICMI-NNN) and letter (ICMI-X) groups
numbered_papers=()
letter_papers=()
for md in "$REPO_DIR"/ICMI-*.md; do
  [ -f "$md" ] || continue
  bn="$(basename "$md" .md)"
  if [[ "$bn" =~ ^ICMI-[0-9] ]]; then
    numbered_papers+=("$md")
  else
    letter_papers+=("$md")
  fi
done

# Helper: extract metadata and build an <li> for a paper
build_paper_item() {
  local md="$1"
  local basename="$(basename "$md" .md)"

  # Extract title from first H1
  local title="$(grep -m1 '^# ' "$md" | sed 's/^# //')"

  # Extract paper number: try numeric "Working Paper No. N", then letter "Working Paper X"
  local paper_num="$(grep -m1 'Working Paper No\.' "$md" | sed 's/.*Working Paper No\. *//' | sed 's/[^0-9]//g')"
  if [ -z "$paper_num" ]; then
    paper_num="$(grep -m1 'Working Paper [A-Z]' "$md" | sed 's/.*Working Paper *//' | sed 's/[^A-Za-z]//g')"
  fi

  # Build display label
  local paper_label
  if [[ "$paper_num" =~ ^[0-9]+$ ]]; then
    paper_label="Working Paper No. ${paper_num}"
  else
    paper_label="Working Paper ${paper_num}"
  fi

  # Extract author: try "**Author:** ..." line first, then fall back to line after "Working Paper"
  local author="$(grep -m1 '^\*\*Author:\*\*' "$md" | sed 's/^\*\*Author:\*\* *//' | sed 's/[[:space:]]*$//' || true)"
  if [ -z "$author" ]; then
    author="$(awk '/Working Paper/{getline; print; exit}' "$md" | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')"
  fi
  # Strip "with research assistance from Claude (Anthropic)" and trailing comma
  author="$(echo "$author" | sed 's/,[[:space:]]*with research assistance from Claude (Anthropic)//' | sed 's/with research assistance from Claude (Anthropic)//')"

  # Extract date
  local paper_date="$(grep -m1 '^\*\*Date:\*\*' "$md" | sed 's/^\*\*Date:\*\* *//' | sed 's/[[:space:]]*$//' || true)"

  local date_html=""
  if [ -n "$paper_date" ]; then
    date_html="<span class=\"paper-date\">${paper_date}</span>"
  fi

  echo "
    <li>
      <span class=\"paper-number\">${paper_label}</span>
      <div class=\"paper-title\"><a href=\"${basename}.html\">${title}</a></div>
      <div class=\"paper-author\">${author}${date_html:+ &middot; }${date_html} &middot; <a href=\"${basename}.pdf\" class=\"paper-pdf\">PDF</a></div>
    </li>"
}

# Build numbered papers in reverse order (newest first)
for (( i=${#numbered_papers[@]}-1; i>=0; i-- )); do
  NUMBERED_ITEMS+="$(build_paper_item "${numbered_papers[$i]}")"
done

# Build letter papers in forward order (A, B, C, D, E)
for md in "${letter_papers[@]}"; do
  LETTER_ITEMS+="$(build_paper_item "$md")"
done

# Write index as a standalone HTML file (no pandoc needed)
cat > "$OUT_DIR/index.html" <<'HEADER'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Proceedings of the Institute for a Christian Machine Intelligence</title>
  <link rel="icon" type="image/png" sizes="32x32" href="favicon-32.png">
  <link rel="apple-touch-icon" sizes="180x180" href="favicon.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,400;0,600;0,700;1,400;1,600&display=swap" rel="stylesheet">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Crimson Pro', Georgia, 'Times New Roman', serif;
      font-size: 19px;
      line-height: 1.7;
      color: #000;
      background: #fff;
      padding: 3rem 1.5rem;
      max-width: 42rem;
      margin: 0 auto;
    }
    a { color: #000; }
    a:hover { text-decoration: none; }
    header {
      margin-bottom: 3rem;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid #000;
    }
    header .site-title {
      font-size: 3.2rem;
      font-weight: 700;
      line-height: 1.1;
      letter-spacing: -0.02em;
    }
    header .site-subtitle {
      font-size: 1.15rem;
      font-weight: 400;
      margin-top: 0.35rem;
      line-height: 1.4;
    }
    .paper-list { list-style: none; }
    .paper-list li { margin-bottom: 2.5rem; }
    .paper-list .paper-number {
      font-size: 0.9rem;
      font-weight: 600;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      display: block;
      margin-bottom: 0.15rem;
    }
    .paper-list .paper-title {
      font-size: 1.4rem;
      font-weight: 600;
      line-height: 1.35;
    }
    .paper-list .paper-title a { text-decoration: none; }
    .paper-list .paper-title a:hover { text-decoration: underline; }
    .paper-list .paper-author {
      font-size: 1.05rem;
      color: #444;
      margin-top: 0.15rem;
    }
    .section-heading {
      font-size: 1.6rem;
      font-weight: 600;
      margin-top: 3rem;
      margin-bottom: 1.5rem;
      padding-top: 2rem;
      border-top: 1px solid #ccc;
    }
    footer {
      margin-top: 4rem;
      padding-top: 1.5rem;
      border-top: 1px solid #000;
      font-size: 0.9rem;
      text-align: center;
    }
    footer a { color: #000; }
    @media (max-width: 600px) {
      body { font-size: 17px; padding: 2rem 1rem; }
      header .site-title { font-size: 2rem; }
    }
  </style>
</head>
<body>
  <header>
    <div class="site-title">Proceedings</div>
    <div class="site-subtitle">of the Institute for a Christian Machine Intelligence</div>
  </header>
  <main>
    <ul class="paper-list">
HEADER

# Append numbered papers (Working Paper series)
echo "$NUMBERED_ITEMS" >> "$OUT_DIR/index.html"

# Append earlier papers section if any letter papers exist
if [ -n "$LETTER_ITEMS" ]; then
  cat >> "$OUT_DIR/index.html" <<'SECTION'
    </ul>
    <h2 class="section-heading">Earlier Papers</h2>
    <ul class="paper-list">
SECTION
  echo "$LETTER_ITEMS" >> "$OUT_DIR/index.html"
fi

cat >> "$OUT_DIR/index.html" <<'FOOTER'
    </ul>
  </main>
  <footer>
    <a href="https://github.com/christian-machine-intelligence">GitHub</a>
  </footer>
</body>
</html>
FOOTER

# ---------- Cross-link bibliography entries ----------
echo "Cross-linking bibliography references ..."
python3 "$SCRIPT_DIR/crosslink-bibliography.py" "$OUT_DIR"

# Copy favicon files
for fav in "$REPO_DIR"/favicon*.png; do
  [ -f "$fav" ] && cp "$fav" "$OUT_DIR/"
done

# Copy CNAME if it exists
if [ -f "$REPO_DIR/CNAME" ]; then
  cp "$REPO_DIR/CNAME" "$OUT_DIR/CNAME"
fi

echo "Site built in $OUT_DIR/"
