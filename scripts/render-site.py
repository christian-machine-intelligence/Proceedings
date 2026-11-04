#!/usr/bin/env python3
"""Render every HTML page of the site in the ICMI brand design.

Usage: render-site.py REPO_DIR OUT_DIR

The Markdown files stay the single source of truth. This script runs pandoc over them and sets the result
in the page templates under scripts/templates/ (a design page's CSS and markup, with {{placeholders}}):

  ICMI-*.md        -> ICMI-*.html   a paper page (paper.css)
  (all papers)     -> index.html    homepage: the latest paper, the recent list
  (all papers)     -> papers.html   the papers index
  literature-review.md -> primer.html (and review.html, a redirect to it)
  about.md, fundraising.md -> about.html, fundraising.html

Paper metadata (title, number, author, date, abstract) is read from each paper's Markdown with the same rules
the old build used. Standard library only; pandoc must be on PATH. The assets (site.css, field.js, art/, fonts/...)
are copied into OUT_DIR by build-site.sh before this runs, so the script can see which art exists.
"""
import glob
import os
import re
import struct
import subprocess
import sys

REPO, OUT = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
TPL = os.path.join(REPO, "scripts", "templates")
SITE = "https://icmi-proceedings.com"
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]


# ---------------------------------------------------------------- helpers
def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(name, text):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(text)


def pandoc(text, extra=()):
    cmd = ["pandoc", "--from", "markdown", "--to", "html5", "--wrap=none", "--no-highlight", *extra]
    r = subprocess.run(cmd, input=text, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit("pandoc failed: " + r.stderr)
    return r.stdout


def inline(md):
    """Markdown inline text -> HTML (smart quotes, <i> for emphasis, no wrapping <p>)."""
    h = pandoc(md).strip()
    h = re.sub(r"^<p>(.*)</p>$", r"\1", h, flags=re.S)
    return h.replace("<em>", "<i>").replace("</em>", "</i>")


def plain(h):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", h)).strip()


def esc(s):
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def unesc(s):
    return s.replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


def nbsp_last(h):
    """Bind the last two words with a no-break space so a line never ends on an orphan."""
    i = h.rfind(" ")
    if i > 0 and "<" not in h[i:] and ">" not in h[i:]:
        return h[:i] + "&nbsp;" + h[i + 1:]
    return h


def rows_of_text(html, fn):
    """Apply fn to the text between tags, but not inside <pre>, <code>, <script> or <style>."""
    out, skip = [], 0
    for part in re.split(r"(<[^>]+>)", html):
        if part.startswith("<"):
            m = re.match(r"<(/?)(pre|code|script|style)\b", part)
            if m:
                skip += -1 if m.group(1) else 1
            out.append(part)
        else:
            out.append(part if skip > 0 else fn(part))
    return "".join(out)


def tie_dashes(html):
    """A spaced em dash becomes a closed one, held to its neighbours: 'interior — and' -> 'interior—and' (no break before)."""
    def fn(t):
        return re.sub(r"(\S+) — (\S+)", r'<span class="nw">\1&mdash;\2</span>', t)
    return rows_of_text(html, fn)


def image_size(path):
    try:
        with open(path, "rb") as f:
            d = f.read(65536)
        if d[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", d[16:24])
        if d[:2] == b"\xff\xd8":
            i = 2
            while i < len(d):
                if d[i] != 0xFF:
                    i += 1
                    continue
                mk = d[i + 1]
                if mk in (0xC0, 0xC1, 0xC2):
                    h, w = struct.unpack(">HH", d[i + 5:i + 9])
                    return w, h
                i += 2 + struct.unpack(">H", d[i + 2:i + 4])[0]
    except (OSError, struct.error):
        pass
    return None


def blocks(html):
    """Split pandoc's top-level HTML into [(tag, html)] by tracking tag depth."""
    out, depth, start, tag0 = [], 0, None, None
    for m in re.finditer(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)\b[^>]*?(/?)>", html):
        close, tag, selfc = m.group(1), m.group(2).lower(), m.group(3)
        void = selfc or tag in ("hr", "img", "br", "col", "input")
        if depth == 0:
            if close:
                continue
            start, tag0 = m.start(), tag
            if void:
                out.append((tag, m.group(0)))
                start = None
            else:
                depth = 1
        elif not void:
            depth += -1 if close else 1
            if depth == 0:
                out.append((tag0, html[start:m.end()]))
                start = None
    return out


def exists(rel):
    return os.path.exists(os.path.join(OUT, rel))


# ---------------------------------------------------------------- paper metadata (the build's extraction rules)
def paper_meta(md_path):
    text = read(md_path)
    lines = text.split("\n")
    base = os.path.basename(md_path)[:-3]

    def grep1(pat):
        for ln in lines:
            if re.search(pat, ln):
                return ln
        return ""

    title_md = re.sub(r"^# *", "", grep1(r"^# ")).strip()
    # number: "Working Paper No. N", else "Working Paper X"
    num = re.sub(r"[^0-9]", "", re.sub(r".*Working Paper No\. *", "", grep1(r"Working Paper No\.")))
    if not num:
        num = re.sub(r"[^A-Za-z]", "", re.sub(r".*Working Paper *", "", grep1(r"Working Paper [A-Z]")))
    author = re.sub(r"^\*\*Author:\*\* *", "", grep1(r"^\*\*Author:\*\*")).strip()
    if not author:
        for i, ln in enumerate(lines):
            if "Working Paper" in ln and i + 1 < len(lines):
                author = lines[i + 1].strip()
                break
    author = re.sub(r",?\s*with research assistance from Claude \(Anthropic\)", "", author)
    author = re.sub(r",\s*Institute for a Christian Machine Intelligence\s*$", "", author).strip()
    date = re.sub(r"^\*\*Date:\*\* *", "", grep1(r"^\*\*Date:\*\*")).strip()
    code = grep1(r"^\*\*Code & Data:\*\*")
    code_links = re.findall(r"\[([^\]]*)\]\(([^)]*)\)", code)

    # abstract: the "**Abstract.**" paragraph, else the first paragraph under "## Abstract"
    abstract = ""
    for i, ln in enumerate(lines):
        if ln.startswith("**Abstract.**"):
            para = [ln[len("**Abstract.**"):].strip()]
            for nxt in lines[i + 1:]:
                if not nxt.strip():
                    break
                para.append(nxt.strip())
            abstract = " ".join(para)
            break
        if re.match(r"^## Abstract\s*$", ln):
            para = []
            for nxt in lines[i + 1:]:
                if not nxt.strip():
                    if para:
                        break
                    continue
                para.append(nxt.strip())
            abstract = " ".join(para)
            break

    is_num = num.isdigit()
    key = "%02d" % int(num) if is_num else num
    seed = (336 + 7 * (int(num) % 10)) if is_num else 455 + 7 * (ord(num[:1].upper()) - ord("A"))
    return {
        "base": base, "n": num, "key": key, "seed": seed, "is_num": is_num,
        "label": ("No. " + num) if is_num else num,
        "label_plain": ("No. " + num) if is_num else num,
        "kicker": ("Working paper No.&nbsp;" + num) if is_num else ("Working paper " + num),
        "title_md": title_md, "title": inline(title_md), "title_text": plain(inline(title_md)),
        "author": inline(author), "date": date, "abstract_md": abstract,
        "code_links": code_links,
        "href": base + ".html", "pdf": base + ".pdf",
    }


def sentences(h, limit=380):
    """First two sentences (or one, if two run long) of an HTML run, split outside tags."""
    out, depth, start, found = [], 0, 0, []
    for i, ch in enumerate(h):
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        elif depth == 0 and ch in ".?!" and i + 1 < len(h) and h[i + 1] == " " and i + 2 < len(h) and re.match(r"[A-Z“(\[]", h[i + 2]):
            if not re.search(r"(al|e\.g|i\.e|vs|cf|No|Fig|Eq)$", h[start:i]):
                found.append(i + 1)
                if len(found) == 2:
                    break
    if not found:
        return h
    cut = found[1] if len(found) > 1 and found[1] <= limit else found[0]
    return h[:cut]


# ---------------------------------------------------------------- page frame
LOCKUP = ('<a class="lockup" href="index.html" aria-label="Proceedings of the Institute for a Christian Machine Intelligence, home">'
          '<span class="mark"><svg width="40" height="40" viewBox="0 0 40 40" aria-hidden="true" focusable="false"><path d="M4 0h2v37h-2zM0 34h3v2h-3zM7 34h33v2h-33zM23 6h2v20h-2zM14 15h20v2h-20z" fill="#2E3236"/><path d="M0 0h2v33h-2zM0 37h2v3h-2zM3 38h37v2h-37z" fill="#B0222D"/></svg></span>'
          '<span class="name"><b>Proceedings</b><i>of the Institute for a Christian Machine Intelligence</i></span></a>')
NAV = [("about.html", "About"), ("papers.html", "Papers"), ("primer.html", "Primer"), ("fundraising.html", "Fundraising")]
SUPPORT = ('<section class="support-band" aria-label="Support the Institute">\n'
           '    <p>The Institute is actively fundraising to grow this research program into a durable, independent&nbsp;lab.</p>\n'
           '    <a class="btn ghost" href="fundraising.html">Learn how to support the Institute</a>\n  </section>')
FOOTER = '''<!-- the footer: one engraved scene over the waters, picked at random per load (footer/word.js, footer/scenes.json) -->
  <footer class="word">
    <canvas id="word" role="img"></canvas>
    <div class="top">
      <div class="close">
        <div class="lock"><svg width="56" height="56" viewBox="0 0 56 56" aria-hidden="true" focusable="false"><path d="M6 0h3v52h-3zM0 47h5v3h-5zM10 47h46v3h-46zM32 8h3v29h-3zM19 21h29v3h-29z" fill="#E8E8E2"/><path d="M0 0h3v46h-3zM0 51h3v5h-3zM4 53h52v3h-52z" fill="#E8524C"/></svg><span>Institute <i>for a</i> Christian<br>Machine Intelligence</span></div>
        <nav aria-label="Footer">
          <a href="about.html">About</a>
          <a href="papers.html">Papers</a>
          <a href="primer.html">Primer</a>
          <a href="fundraising.html">Fundraising</a>
          <a href="https://github.com/christian-machine-intelligence">GitHub</a>
        </nav>
      </div>
    </div>
    <div class="stage" aria-hidden="true"></div>
    <p class="verse" id="verse"></p>
    <div class="rubric"><h2>In the beginning<br>was the Word.</h2></div>
  </footer>'''
MATHJAX = ("<script>MathJax = { tex: { inlineMath: [['\\\\(','\\\\)']], displayMath: [['\\\\[','\\\\]']] } };</script>\n"
           '  <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js" async></script>')


def template(name):
    """A template file is a <style> block, then (optionally) '<!--main-->' and the page's <main> content."""
    t = read(os.path.join(TPL, name))
    if "<!--main-->" in t:
        style, main = t.split("<!--main-->", 1)
        return style.strip(), main.strip("\n")
    return t.strip(), ""


def fill(t, vals):
    for k, v in vals.items():
        t = t.replace("{{" + k + "}}", v)
    return t


def page(*, title, description, style, main, current=None, support=True, scripts=(), og_path="", og_image="og-image.jpg",
         og_type="website", extra_head="", extra_end=""):
    nav = "\n".join('      <a href="%s"%s>%s</a>' % (h, ' aria-current="page"' if h == current else "", t) for h, t in NAV)
    fonts = "".join('  <link rel="preload" href="fonts/DovesType-%s.woff2" as="font" type="font/woff2" crossorigin>\n' % w
                    for w in ("Headline", "Text") if exists("fonts/DovesType-%s.woff2" % w))
    d = esc(description)
    tags = ('  <meta property="og:type" content="%s">\n  <meta property="og:site_name" content="ICMI Proceedings">\n'
            '  <meta property="og:title" content="%s">\n  <meta property="og:description" content="%s">\n'
            '  <meta property="og:url" content="%s/%s">\n  <meta property="og:image" content="%s/%s">\n'
            '  <meta name="twitter:card" content="summary_large_image">\n  <meta name="twitter:title" content="%s">\n'
            '  <meta name="twitter:description" content="%s">\n  <meta name="twitter:image" content="%s/%s">\n'
            % (og_type, esc(title), d, SITE, og_path, SITE, og_image, esc(title), d, SITE, og_image))
    scr = "\n".join('  <script src="%s"%s></script>' % (s, "" if s.startswith("footer/") else " defer") for s in scripts)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{d}">
{tags}  <meta name="theme-color" content="#E8E8E2">
  <link rel="icon" type="image/png" sizes="32x32" href="favicon-32.png">
  <link rel="apple-touch-icon" sizes="180x180" href="favicon.png">
{fonts}  <link rel="stylesheet" href="site.css">
  <link rel="stylesheet" href="footer/word.css">
  {style}
{extra_head}</head>
<body>
  <header class="site">
    {LOCKUP}
    <nav class="main" aria-label="Main">
{nav}
    </nav>
  </header>

  <main>
{main}
  </main>

  {SUPPORT if support else ""}
  {FOOTER}

{scr}
{extra_end}</body>
</html>
'''


def art_fields(m, kind):
    """The engraving (band or tile) for a paper, or None if the paper has none yet."""
    k = m["key"]
    if exists("art/%s/%s.jpg" % (kind, k)) and exists("art/field/%s-%s.png" % (kind, k)):
        return k
    return None


def fallback_canvas(m, current=False):
    return '<canvas class="paper-field" data-n="%s"%s aria-hidden="true"></canvas>' % (m["n"], " data-current" if current else "")


# ---------------------------------------------------------------- paper pages
def code_label(text, url, first):
    slug = url.rstrip("/").split("/")[-1]
    generic = text.strip().lower() in ("link", "github", "code", "code & data", "") or text.strip() == slug
    if first:
        return "Code and data: " + slug
    return slug if generic else text.strip()


def convert_figures(h):
    def fig(mm):
        img, cap = mm.group(1), mm.group(2)
        src = re.search(r'src="([^"]+)"', img)
        dim = image_size(os.path.join(REPO, src.group(1))) if src and not src.group(1).startswith("http") else None
        attrs = re.sub(r"\s*/?$", "", img)
        if dim:
            attrs += ' width="%d" height="%d" style="--w:%dpx"' % (dim[0], dim[1], dim[0])
        cap_html = ""
        if cap:
            cap = cap.replace("<strong>", "<b>").replace("</strong>", "</b>")
            cap_html = "\n<figcaption>%s</figcaption>" % cap
        return '<figure class="fig">\n<div class="plate"><img %s loading="lazy"></div>%s\n</figure>' % (attrs, cap_html)
    return re.sub(r"<figure>\s*<img\s+(.*?)\s*/?>\s*(?:<figcaption[^>]*>(.*?)</figcaption>)?\s*</figure>", fig, h, flags=re.S)


def build_paper(md_path, m):
    frag = pandoc(read(md_path), ["--mathjax"])
    has_math = 'class="math' in frag
    notice = ""
    nm = re.search(r'<div class="paper-notice"[^>]*>(.*?)</div>', frag, re.S)
    if nm:
        notice = '<div class="notice" role="note">%s</div>' % nm.group(1).strip()
        frag = frag.replace(nm.group(0), "", 1)
    # drop the title and the metadata lines at the top (the page header shows them), and the rule that ends them
    first_h2 = frag.find("<h2")
    head_end = frag.find("<hr />")
    cut = head_end if head_end != -1 and (first_h2 == -1 or head_end < first_h2) else (first_h2 if first_h2 != -1 else 0)
    head, rest = frag[:cut], frag[cut:]
    head = re.sub(r"<h1[^>]*>.*?</h1>", "", head, flags=re.S)
    head = re.sub(r"<p><strong>(?:ICMI Working Paper|Author:|Date:|Code &amp; Data:)[^<]*.*?</p>", "", head, flags=re.S)
    rest = re.sub(r"^\s*<hr />\s*", "", rest)
    frag = head + rest
    frag = re.sub(r"<hr />\s*(?=<h2)", "", frag)
    frag = re.sub(r"\s*<hr />\s*$", "", frag)

    toc = []
    pre, *chunks = re.split(r"(?=<h2[ >])", frag)
    abstract_p = re.search(r"<p><strong>Abstract\.</strong>", pre)
    if abstract_p:
        pre = pre.replace(abstract_p.group(0), '<p class="body" id="abstract"><span class="pil">&para;</span><span class="run-in">Abstract.</span>', 1)
        toc.append(("abstract", "", "Abstract"))
    out = [pre.strip()]
    for ch in chunks:
        hm = re.match(r'<h2(?: id="([^"]*)")?[^>]*>(.*?)</h2>', ch, re.S)
        hid, htxt = hm.group(1) or "", hm.group(2)
        nm2 = re.match(r"^(\d+)\.\s+(.*)$", htxt, re.S)
        num, label = (nm2.group(1), nm2.group(2)) if nm2 else ("", htxt)
        h2 = '<h2>%s<span>%s</span></h2>' % ('<span class="n">%s</span>' % num if num else "", label)
        body = ch[hm.end():]
        out.append('<section class="psec"%s>\n%s%s</section>' % (' id="%s"' % hid if hid else "", h2, body))
        if hid:
            toc.append((hid, num, label))
    body = "\n".join(out)
    body = re.sub(r"<h3([^>]*)>(\d+\.\d+)\s+", r'<h3\1><span class="n">\2</span>', body)   # sub-section numbers
    body = re.sub(r"(<h3[^>]*>)(?!<span class=\"n\">)(.*?)(</h3>)", r"\1<span>\2</span>\3", body, flags=re.S)
    body = re.sub(r'(<h3[^>]*><span class="n">[^<]*</span>)([^<].*?)(</h3>)', r"\1<span>\2</span>\3", body, flags=re.S)
    body = convert_figures(body)
    body = re.sub(r"(<table.*?</table>)", r'<div class="tbl">\1</div>', body, flags=re.S)
    body = body.replace("<em>", "<i>").replace("</em>", "</i>")
    body = tie_dashes(body)

    toc_html = ['<div class="k"><i></i><span>Contents</span></div>']
    for hid, num, label in toc:
        toc_html.append('<a class="t" href="#%s"><span class="n">%s</span><span>%s</span></a>' % (hid, num, re.sub(r"<[^>]+>", "", label)))

    links = ['<a class="btn" href="%s">Download the PDF</a>' % m["pdf"]]
    for i, (t, u) in enumerate(m["code_links"]):
        links.append('<a class="more" href="%s">%s &rarr;</a>' % (u, esc(code_label(t, u, i == 0))))

    k = art_fields(m, "band")
    if k:
        art = '<div class="art engrave" data-field="art/field/band-%s.png" data-seed="%d"></div>' % (k, m["seed"])
        band = "art/band/%s.jpg" % k
    else:
        art = '<div class="art fb">%s</div>' % fallback_canvas(m, True)
        band = "art/hero.jpg"
    style, _ = template("paper.css")
    style = fill(style, {"band": band})
    by = m["author"] + (' <span>&middot; %s</span>' % m["date"] if m["date"] else "")
    main = f'''    <section class="phead">
      {art}
      <div class="in">
        <div class="kicker">{m["kicker"]}</div>
        <h1 class="h1">{nbsp_last(m["title"])}</h1>
        <p class="by">{by}</p>
        <div class="links">
          {chr(10).join("          " + l for l in links).strip()}
        </div>
      </div>
    </section>

    <div class="pbody">
      <nav class="toc" aria-label="Contents">
        {chr(10).join("        " + l for l in toc_html).strip()}
      </nav>
      <article class="ptext">
        {notice}
{body}
      </article>
    </div>'''
    desc = plain(inline(m["abstract_md"]))[:300] if m["abstract_md"] else "Working paper %s by %s, %s." % (m["label_plain"], plain(m["author"]), m["date"])
    scripts = ["footer/word.js", "engrave.js"] + ([] if k else ["field.js"])
    write(m["href"], page(
        title=m["title_text"] + " · Proceedings", description=desc, style=style, main=main, current="papers.html",
        scripts=scripts, og_path=m["href"], og_type="article", extra_head="  " + MATHJAX + "\n" if has_math else ""))


# ---------------------------------------------------------------- papers index and homepage
def ordered(papers):
    nums = sorted([p for p in papers if p["is_num"]], key=lambda p: -int(p["n"]))
    lets = sorted([p for p in papers if not p["is_num"]], key=lambda p: p["n"], reverse=True)
    return nums, lets


def build_papers_index(papers):
    nums, lets = ordered(papers)
    tiles = []
    for p in nums + lets:
        k = art_fields(p, "tile")
        if k:
            art = '<div class="art engrave" data-field="art/field/tile-%s.png" data-seed="%d" style="background-image:url(art/tile/%s.jpg)"></div>' % (k, p["seed"], k)
        else:
            art = '<div class="art fb">%s</div>' % fallback_canvas(p)
        tiles.append(f'''      <a class="tile" href="{p["href"]}">
        {art}
        <span class="no">{p["label"]}</span>
        <span class="tt">{nbsp_last(p["title"])}</span>
        <span class="meta">{p["author"]} &middot; {p["date"]}</span>
      </a>''')
    style, main = template("papers.html")
    main = fill(main, {"tiles": "\n".join(tiles)})
    scripts = ["footer/word.js", "engrave.js"] + (["field.js"] if any(not art_fields(p, "tile") for p in papers) else [])
    write("papers.html", page(
        title="Working papers · Institute for a Christian Machine Intelligence",
        description="Working papers of the Institute for a Christian Machine Intelligence.",
        style=style, main=main, current="papers.html", scripts=scripts, og_path="papers.html"))


def build_home(papers):
    nums, lets = ordered(papers)
    latest = nums[0] if nums else (lets[0] if lets else None)
    recent = [p for p in nums if p is not latest][:10]
    k = art_fields(latest, "band")
    if k:
        art = '<div class="art engrave" data-field="art/field/band-%s.png" data-seed="%d"></div>' % (k, latest["seed"])
        band = "art/band/%s.jpg" % k
    else:
        art = '<div class="art fb">%s</div>' % fallback_canvas(latest)
        band = "art/hero.jpg"
    # the title's first letter is the scarlet initial, the rest of its first word in capitals
    t = latest["title"]
    cm = re.match(r"^([A-Za-z])([a-z]*)(?=[ :,]|$)", t)
    title = ('<span class="cap">%s</span><span class="caps">%s</span>%s' % (cm.group(1), cm.group(2), t[cm.end():])) if cm else t
    exc = sentences(tie_dashes(inline(latest["abstract_md"]))) if latest["abstract_md"] else ""
    excerpt = '<p class="excerpt lede">%s</p>' % nbsp_last(exc) if exc else ""
    rows = "\n".join(
        '      <div class="row"><span class="no">no. %s</span><div class="t"><a href="%s">%s</a><span class="meta">%s &middot; %s</span></div><a class="pdf" href="%s" aria-label="PDF of no. %s">pdf</a></div>'
        % (p["n"], p["href"], p["title"], p["author"], p["date"], p["pdf"], p["n"]) for p in recent)
    style, main = template("home.html")
    main = fill(main, {
        "latest_art": art, "latest_label": latest["label_plain"] if latest["is_num"] else latest["n"],
        "latest_href": latest["href"], "latest_pdf": latest["pdf"], "latest_title": title,
        "latest_meta": "%s &middot; %s" % (latest["author"], latest["date"]), "latest_excerpt": excerpt, "recent_rows": rows})
    style = fill(style, {"latest_band": band})
    desc = "How do you reliably orient a capable agent toward the good, even when the incentives favor otherwise?"
    scripts = ["footer/word.js", "field.js", "engrave.js"]
    write("index.html", page(
        title="Proceedings · Institute for a Christian Machine Intelligence", description=desc, style=style, main=main,
        scripts=scripts, og_path="", og_image="index-card.jpg"))


# ---------------------------------------------------------------- About, Fundraising, Primer (from their Markdown)
def fix_links(h):
    h = h.replace('href="review.html"', 'href="primer.html"')
    h = re.sub(r'<a href="([^"]*ICMI-[^"]*)">([^<]*ICMI-[0-9A-Z]+[^<]*)</a>', r'<a class="ref" href="\1">\2</a>', h)
    return h.replace("<em>", "<i>").replace("</em>", "</i>")


def run_in(li):
    """A list item that opens with a bold lead becomes a run-in passage: a red mark, the lead in capitals, the text."""
    li = re.sub(r"^\s*<p>(.*)</p>\s*$", r"\1", li.strip(), flags=re.S)
    m = re.match(r"^<strong>(.*?)</strong>\s*(.*)$", li, re.S)
    return '<span class="pil">&para;</span><span class="run-in">%s</span> %s' % (m.group(1), m.group(2)) if m else None


def list_items(h):
    return [m.group(1) for m in re.finditer(r"<li[^>]*>(.*?)</li>", h, re.S)]


def stack_html(bl, dropcap=False):
    out = []
    for tag, h in bl:
        if tag == "p":
            inner = re.sub(r"^<p>(.*)</p>$", r"\1", h, flags=re.S)
            if dropcap:
                dropcap = False
                out.append(dropcap_para(inner))
            else:
                out.append('<p class="body">%s</p>' % nbsp_last(inner))
        elif tag in ("ul", "ol"):
            runs = [run_in(i) for i in list_items(h)]
            if all(runs):
                out.append('<p class="body">%s</p>' % " ".join(runs))
            else:
                out.append(h.replace("<%s>" % tag, '<%s class="lst body">' % tag, 1))
        elif tag == "hr":
            continue
        else:
            out.append(h)
    return "\n        ".join(out)


def dropcap_para(inner):
    """A drop-initial lede: the first sentence set large with a scarlet initial; the rest of the paragraph follows as body text."""
    first = sentences(inner, limit=0)
    rest = inner[len(first):].strip()
    first = first.strip()
    m = re.match(r"^([A-Za-z])([A-Za-z]*)(.*)$", first, re.S)
    if not m:
        return '<p class="body">%s</p>' % inner
    big = '<div class="dropcap three big"><span class="cap" aria-hidden="true">%s</span><span class="caps">%s</span>%s</div>' % (m.group(1), m.group(2), nbsp_last(m.group(3)))
    return big + ('\n        <p class="body">%s</p>' % nbsp_last(rest) if rest else "")


def sections_of(frag):
    """pandoc's flat top-level blocks -> (h1, intro blocks, [(id, heading html, blocks)])"""
    bl = blocks(frag)
    h1, intro, secs, cur = None, [], [], None
    for tag, h in bl:
        if tag == "h1" and h1 is None:
            h1 = h
        elif tag == "h2":
            hid = re.search(r'id="([^"]*)"', h)
            cur = (hid.group(1) if hid else "", re.sub(r"</?h2[^>]*>", "", h), [])
            secs.append(cur)
        elif cur is None:
            intro.append((tag, h))
        else:
            cur[2].append((tag, h))
    return h1, intro, secs


def is_decor(tag, h):
    """An image-only paragraph or a lone italic epigraph: the design carries neither."""
    return tag == "p" and (re.match(r"^<p>\s*<img[^>]*>\s*</p>$", h) is not None or re.match(r"^<p><(?:em|i)>[^<]*</(?:em|i)></p>$", h) is not None)


def build_longform(name, md_path, og_image, with_dropcap):
    frag = tie_dashes(fix_links(pandoc(read(md_path), ["--from", "markdown-implicit_figures"])))
    h1, intro, secs = sections_of(frag)
    h1_text = plain(h1)
    ps = [(t, h) for t, h in intro if not is_decor(t, h)]
    first = re.sub(r"^<p>(.*)</p>$", r"\1", ps[0][1], flags=re.S) if ps else ""
    if ps and len(plain(first)) <= 240:
        head = ('<div class="kicker">%s</div>\n      <h1 class="h1">%s</h1>'
                % (h1_text, nbsp_last(first.replace("<strong>", "<i>", 1).replace("</strong>", "</i>", 1).replace("<strong>", "").replace("</strong>", ""))))
        ledes = ps[1:]
    else:
        head = '<h1 class="h1">%s</h1>' % h1_text
        ledes = ps
    lede_html = "\n      ".join('<p class="lede">%s</p>' % nbsp_last(re.sub(r"^<p>(.*)</p>$", r"\1", h, flags=re.S)) for t, h in ledes if t == "p")
    parts = ['    <section class="opening">\n      %s\n      %s\n    </section>' % (head, lede_html)]
    n_block = 0
    for hid, htxt, bl in secs:
        title = plain(htxt)
        if hid == "support" and name != "fundraising":
            continue      # the red support band shows this on every page but Fundraising
        if hid == "the-ask":
            paras = [(t, h) for t, h in bl if t == "p"]
            cards = []
            for t, h in bl:
                if t in ("ul", "ol"):
                    for i, li in enumerate(list_items(h)):
                        li = re.sub(r"^\s*<p>(.*)</p>\s*$", r"\1", li.strip(), flags=re.S)
                        m = re.match(r"^<strong>(.*?)</strong>\s*(.*)$", li, re.S)
                        head_t, body_t = (re.sub(r"\.$", "", m.group(1)), m.group(2)) if m else ("", li)
                        cards.append('<div><h3><span>%s</span> %s</h3><p>%s</p></div>' % (ROMAN[i], head_t, nbsp_last(body_t)))
            intro_p = " ".join(re.sub(r"^<p>(.*)</p>$", r"\1", h, flags=re.S) for t, h in paras)
            parts.append('    <section class="ask">\n      <div class="intro">\n        <h2 class="h-side">%s</h2>\n        <p class="body">%s</p>\n      </div>\n      <div class="four">\n        %s\n      </div>\n    </section>'
                         % (title, nbsp_last(intro_p), "\n        ".join(cards)))
            continue
        if hid == "get-in-touch":
            say, mail, tail = [], None, []
            for t, h in bl:
                mm = re.search(r'href="(mailto:[^"]+)"', h)
                if t == "p" and mm and mail is None:
                    mail = mm.group(1)
                elif t == "p":
                    inner = re.sub(r"^<p>(.*)</p>$", r"\1", h, flags=re.S)
                    (tail if mail else say).append(inner)
            links = ""
            if mail:
                addr = mail[len("mailto:"):]
                links = ('<div class="links"><a class="btn" href="%s" style="background:var(--scarlet);border-radius:0">Write to the Institute</a>'
                         '<a class="mail" href="%s">%s</a></div>' % (mail, mail, addr))
            parts.append('    <section class="touch">\n      <h2 class="h-side">%s</h2>\n      <div class="stack">\n        %s\n        %s\n        %s\n      </div>\n    </section>'
                         % (title, "\n        ".join('<p class="say">%s</p>' % nbsp_last(s) for s in say), links,
                            "\n        ".join('<p class="body">%s</p>' % t for t in tail)))
            continue
        parts.append('    <section class="block">\n      <h2 class="h-side">%s</h2>\n      <div class="stack">\n        %s\n      </div>\n    </section>'
                     % (title, stack_html(bl, dropcap=with_dropcap and n_block == 0)))
        n_block += 1
    style, _ = template("page.css")
    desc = plain(first)[:200] if first else h1_text
    write(name + ".html", page(
        title=h1_text + " · Proceedings", description=desc, style=style, main="\n\n".join(parts),
        current=name + ".html", support=(name != "fundraising"), scripts=["footer/word.js"],
        og_path=name + ".html", og_image=og_image))


def build_primer(md_path):
    text = re.sub(r"^<!-- review-(?:meta|body):.*-->\s*$", "", read(md_path), flags=re.M)
    frag = tie_dashes(fix_links(pandoc(text, ["--from", "markdown-implicit_figures"])))
    frag = frag.replace('href="index.html"', 'href="papers.html"')
    h1, intro, secs = sections_of(frag)
    note, body, n = "", [], 0
    for t, h in intro:
        if is_decor(t, h) and "<img" in h:
            continue
        if re.match(r"^<p><i>.*</i></p>$", h, re.S):
            note = re.sub(r"^<p><i>(.*)</i></p>$", r"\1", h, flags=re.S)
            continue
        body.append((t, h))
    text_html = []
    first_p = True
    for t, h in body:
        if t == "p":
            inner = re.sub(r"^<p>(.*)</p>$", r"\1", h, flags=re.S)
            if first_p:
                text_html.append(dropcap_para(inner))
                first_p = False
            else:
                text_html.append('<p class="body">%s</p>' % inner)
        elif t in ("ul", "ol"):
            items = list_items(h)
            text_html.append('<div class="themes body">\n%s\n        </div>' % "\n".join(
                '          <div class="it"><span class="r">%s</span><span>%s</span></div>' % (ROMAN[i], nbsp_last(re.sub(r"^\s*<p>(.*)</p>\s*$", r"\1", li.strip(), flags=re.S)))
                for i, li in enumerate(items)))
    toc = ['<div class="kicker">Three themes</div>']
    for i, (hid, htxt, bl) in enumerate(secs):
        toc.append('<a href="#theme-%d"><span class="n">%s</span> %s</a>' % (i + 1, ROMAN[i], plain(htxt)))
        paras = "\n          ".join('<p class="body">%s</p>' % re.sub(r"^<p>(.*)</p>$", r"\1", h, flags=re.S) for t, h in bl if t == "p")
        text_html.append('<section class="theme" id="theme-%d">\n          <h2><span class="r">%s</span><span>%s</span></h2>\n          %s\n        </section>'
                         % (i + 1, ROMAN[i], nbsp_last(htxt), paras))
    main = f'''    <section class="intro">
      <div class="kicker">Primer</div>
      <h1 class="h1">A Primer on the Proceedings</h1>
      <p class="sub">Where to start, and how the papers fit&nbsp;together.</p>
      <div class="note"><p class="meta">{note}</p></div>
    </section>

    <section class="pbody">
      <nav class="toc" aria-label="Three themes">
        {chr(10).join("        " + l for l in toc).strip()}
      </nav>
      <div class="text">
        {chr(10).join("        " + l for l in text_html).strip()}
      </div>
    </section>'''
    style, _ = template("primer.css")
    og = "primer-card.jpg" if os.path.exists(os.path.join(REPO, "primer-card.jpg")) else "og-image.jpg"
    write("primer.html", page(
        title="A Primer on the Proceedings · Proceedings", description="Where to start, and how the papers fit together.",
        style=style, main=main, current="primer.html", scripts=["footer/word.js"], og_path="primer.html", og_image=og))
    # the old address keeps working: review.html forwards to the Primer
    write("review.html", '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>A Primer on the Proceedings</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex">
  <link rel="canonical" href="%s/primer.html">
  <meta http-equiv="refresh" content="0; url=primer.html">
  <script>location.replace("primer.html" + location.search + location.hash);</script>
</head>
<body><p>The Primer has moved to <a href="primer.html">primer.html</a>.</p></body>
</html>
''' % SITE)


# ---------------------------------------------------------------- main
def main():
    mds = sorted(glob.glob(os.path.join(REPO, "ICMI-*.md")))
    papers = []
    for md in mds:
        m = paper_meta(md)
        papers.append(m)
        print("Building %s ..." % m["href"])
        build_paper(md, m)
    print("Building index.html and papers.html ...")
    build_home(papers)
    build_papers_index(papers)
    review = os.path.join(REPO, "literature-review.md")
    if os.path.exists(review):
        print("Rendering primer.html (and the review.html redirect) from literature-review.md ...")
        build_primer(review)
    for name, card, dc in (("about", "about-card.jpg", True), ("fundraising", "fundraising-card.jpg", False)):
        src = os.path.join(REPO, name + ".md")
        if os.path.exists(src):
            print("Building %s.html ..." % name)
            build_longform(name, src, card if os.path.exists(os.path.join(REPO, card)) else "og-image.jpg", dc)


if __name__ == "__main__":
    main()
