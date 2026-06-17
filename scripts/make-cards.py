#!/usr/bin/env python3
"""Generate clean 1200x630 social share (Open Graph) cards for the top-nav pages.

Typographic cards matching the site's masthead: a consistent brand eyebrow, a
page headline, and a subhead, framed in black on white. Run locally (needs the
Georgia system font); the resulting *-card.jpg files are committed and copied to
_site by build-site.sh. Individual paper pages keep og-image.jpg (the Aquinas
engraving); see the og:image meta wiring in the templates.

    python3 scripts/make-cards.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
MARGIN = 96
INK = (20, 20, 20)
GREY = (96, 96, 96)
SUB = (78, 78, 78)
BG = (255, 255, 255)

GEORGIA = "/System/Library/Fonts/Supplemental/Georgia.ttf"
GEORGIA_BOLD = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"

EYEBROW = "Institute for a Christian Machine Intelligence"
URL = "icmi-proceedings.com"

# (outfile, headline, subhead)
CARDS = [
    ("index-card.jpg", "ICMI Proceedings",
     "An ongoing working paper series at the intersection of Christian theology and artificial intelligence."),
    ("about-card.jpg", "A Christian Approach to AI Alignment",
     "Towards an alternative toolkit, built from Christian first principles."),
    ("primer-card.jpg", "A Primer on Christian Machine Intelligence",
     "A plain-language tour of ICMI research to date."),
    ("fundraising-card.jpg", "Support the Institute",
     "Help fund an independent, Christian alignment lab."),
]


def font(path, size):
    return ImageFont.truetype(path, size)


def tlen(d, s, f):
    return d.textlength(s, font=f)


def wrap(d, text, f, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if tlen(d, t, f) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_tracked(d, cx, cy, text, f, fill, tracking):
    widths = [tlen(d, ch, f) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = cx - total / 2
    for ch, wch in zip(text, widths):
        d.text((x, cy), ch, font=f, fill=fill, anchor="lm")
        x += wch + tracking


def fit_tracked(d, text, max_w, start, tracking):
    size = start
    while size >= 14:
        f = font(GEORGIA_BOLD, size)
        widths = [tlen(d, ch, f) for ch in text]
        if sum(widths) + tracking * (len(text) - 1) <= max_w:
            return f
        size -= 1
    return font(GEORGIA_BOLD, 14)


def fit_headline(d, text, max_w, start=76, mins=50):
    size = start
    while size >= mins:
        f = font(GEORGIA_BOLD, size)
        lines = wrap(d, text, f, max_w)
        if len(lines) <= 2 and all(tlen(d, l, f) <= max_w for l in lines):
            return f, lines
        size -= 3
    f = font(GEORGIA_BOLD, mins)
    return f, wrap(d, text, f, max_w)


def make_card(outfile, headline, subhead):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([34, 34, W - 34, H - 34], outline=INK, width=2)
    max_w = W - 2 * MARGIN

    # eyebrow + rule
    ebf = fit_tracked(d, EYEBROW.upper(), max_w - 40, start=25, tracking=5)
    draw_tracked(d, W / 2, 116, EYEBROW.upper(), ebf, GREY, tracking=5)
    d.line([(W / 2 - 58, 178), (W / 2 + 58, 178)], fill=INK, width=2)

    # headline + subhead block, vertically centered in the open band
    hf, hlines = fit_headline(d, headline, max_w)
    lh_h = hf.size * 1.14
    sf = font(GEORGIA, 33)
    slines = wrap(d, subhead, sf, max_w - 30)
    lh_s = 33 * 1.34
    gap = 36
    total = len(hlines) * lh_h + (gap + len(slines) * lh_s if subhead else 0)
    y = (196 + 520) / 2 - total / 2
    for l in hlines:
        d.text((W / 2, y + lh_h / 2), l, font=hf, fill=INK, anchor="mm")
        y += lh_h
    if subhead:
        y += gap
        for l in slines:
            d.text((W / 2, y + lh_s / 2), l, font=sf, fill=SUB, anchor="mm")
            y += lh_s

    # url
    draw_tracked(d, W / 2, H - 80, URL.upper(), font(GEORGIA_BOLD, 22), GREY, tracking=4)

    img.save(outfile, quality=92, optimize=True)
    print("wrote", outfile)


def main():
    repo = Path(__file__).resolve().parent.parent
    for outfile, headline, subhead in CARDS:
        make_card(str(repo / outfile), headline, subhead)


if __name__ == "__main__":
    main()
