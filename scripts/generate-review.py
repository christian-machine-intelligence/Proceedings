#!/usr/bin/env python3
"""Author/refresh the pinned ICMI literature review via the Claude API.

The review is a *committed, hand-editable* file (``literature-review.md``) that is the
single source of truth for what publishes: build-site.sh renders it to review.html and
links to it from the Proceedings index. The Claude API is NOT called at build/deploy
time — only when you run this script to refresh the review (e.g. after adding a paper).

This script scans every ICMI-*.md working paper, extracts its metadata + abstract, asks
Claude to synthesize a ~500-1000 word plain-language "trailhead" review that links to
the individual papers, and writes it to literature-review.md with a small ``review-meta``
header recording the corpus hash it was generated from. Re-running is a no-op while the
corpus is unchanged (it won't clobber your edits); pass --force to regenerate anyway.

Workflow:
    # after adding/editing a paper, refresh the review, then review the diff & commit
    python3 scripts/generate-review.py            # regenerate if the corpus changed
    python3 scripts/generate-review.py --check     # warn (exit 0) if it's stale; no API
    python3 scripts/generate-review.py --force     # regenerate even if unchanged
    python3 scripts/generate-review.py --dry-run   # print the prompt only; no API call

Credentials: reads ANTHROPIC_API_KEY from the environment, or from a gitignored
``.env`` in the repo root. Generation never destroys the existing review: with no
credential (or on an API error) it logs a warning and leaves literature-review.md as-is.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Bump PROMPT_VERSION whenever the prompt below changes, so the cache invalidates.
PROMPT_VERSION = "2"
DEFAULT_MODEL = "claude-fable-5"
SITE_BASE = "https://icmi-proceedings.com"
WORD_TARGET = "500 to 1000 words"
MAX_OUTPUT_TOKENS = 8000
# How many follow-up passes to spend weaving in any papers the draft missed.
MAX_COVERAGE_REPAIRS = 2
# Committed source of truth for the published review (relative to the repo root).
SOURCE_FILENAME = "literature-review.md"
# Marker line carrying the corpus hash the review was generated from.
META_PREFIX = "<!-- review-meta: "
META_SUFFIX = " -->"
# Everything before this marker (the masthead, intro, mission) is a hand-written
# preamble that regeneration PRESERVES; only the categorized body after it is rewritten.
BODY_START_MARKER = "<!-- review-body:start -->"

# Fixed section structure: the body is organized under exactly these three headings.
CATEGORIES = [
    "How might Christian representations be activated within a model, and what are the effects?",
    "How is one to measure and evaluate Christian virtue, and what does it reveal?",
    "How might Christian theology and doctrine inform thinking about AI governance, risk, and safety?",
]

# Used only when generating into a file that has no preamble yet (fresh setup / --force).
DEFAULT_PREAMBLE = (
    "*This is a programmatically generated overview of all research published by the "
    "Institute for a Christian Machine Intelligence (ICMI) to date. It is meant as a "
    "plain-language trailhead for the curious reader; for the papers themselves, see "
    "the [full list of Proceedings](index.html).*\n\n"
    "To date, the Institute's research has followed three themes:\n\n"
    + "\n".join(f"- {c}" for c in CATEGORIES)
)

SYSTEM_PROMPT = """\
You are a science writer for the Institute for a Christian Machine Intelligence \
(ICMI), a research group publishing working papers at the intersection of Christian \
theology and AI alignment, interpretability, and evaluation.

You are writing the BODY of a plain-language "Primer" that surveys the institute's \
{n} working papers for a curious non-specialist. The page title, introduction, and \
masthead are supplied separately — you write ONLY the categorized body, about {words}.

Organize the papers under EXACTLY these three section headings, in this order, each \
used verbatim as a Markdown `##` heading:

{headings}

Where each paper goes:
- The FIRST category covers empirical interventions that change a model's behavior and \
their measured effects — scripture injection, activation steering and interpretability, \
training, and the safety-relevant behaviors these methods produce (e.g. reduced \
scheming or shutdown resistance).
- The SECOND covers benchmarks and the evaluation of virtue and character.
- The THIRD covers conceptual and doctrinal contributions — theology as a lens on what \
a model is, and on how to think about governance, risk, and safety — as opposed to \
empirical interventions, which belong in the first category.

Style and substance:
- Assign each paper to the SINGLE category where it best fits.
- Cite MOST papers, but prioritize a clear narrative over exhaustive coverage: you may \
omit a paper that is a minor control, tangential, or fully superseded if it does not \
fit the story. Never force a paper in just to mention it.
- Use SHORT paragraphs — usually one idea each (one to three sentences). Break a \
section into several short paragraphs rather than one dense block, and never write a \
paper-by-paper list.
- Lead with the substantive finding, stated plainly and with confidence. Do not dwell \
on negative controls, statistical caveats, or self-corrections — note a limitation only \
when it is central. Stay accurate and never overstate a finding, but keep the register \
constructive rather than self-critical.
- The first time a technical or in-house term appears (e.g. "scripture injection", \
"VirtueBench", "corrigibility"), define it in a few words. Avoid unexplained jargon.
- Cite papers inline with the [[n]] markers described below.

Output ONLY the three `##` sections, in Markdown — no title, introduction, masthead, \
footer, closing sentence, or notes about your process.\
"""

CITATION_INSTRUCTIONS = """\
CITATION MARKERS: Each paper above is tagged with a bracketed number, e.g. [3]. To \
cite a paper, put that number in DOUBLE square brackets in your prose, like [[3]]. \
These markers are automatically converted into hyperlinks to the paper, so do not \
write out any URLs yourself. Rules:
- Only use numbers from 1 to {maxtag}.
- Aim for broad coverage — cite most papers — but a few deliberate omissions (minor \
controls, superseded results) are acceptable; do not force a paper in just to cover it.
- To cite several papers together, separate the markers: [[2]], [[5]], [[9]].
- Put each marker right after the claim or paper it supports.\
"""


def log(msg: str) -> None:
    print(f"[generate-review] {msg}", file=sys.stderr)


def strip_md(s: str) -> str:
    """Remove bold/italic markers from a short inline string."""
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = re.sub(r"\*([^*]+)\*", r"\1", s)
    return s.strip()


def parse_date(s: str) -> datetime | None:
    """Parse a paper's '**Date:**' value, e.g. 'April 1, 2026'. Returns None on failure."""
    s = (s or "").strip()
    for fmt in ("%B %d, %Y", "%B %d %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def extract_abstract(text: str) -> str:
    """Pull the abstract out of a paper. Handles the inline ``**Abstract.**`` form
    used across the corpus, with a first-paragraph fallback."""
    # Inline "**Abstract.** ..." running up to the next horizontal rule or H2.
    m = re.search(
        r"\*\*Abstract\.?\*\*\s*(.+?)(?:\n\s*\n\s*---|\n\s*\n##\s|\n\s*---)",
        text,
        re.S,
    )
    if not m:
        m = re.search(r"\*\*Abstract\.?\*\*\s*(.+?)\n\s*\n", text, re.S)
    if m:
        ab = m.group(1)
    else:
        # Fallback: first real paragraph after the metadata block (the first ---).
        parts = text.split("\n---\n", 1)
        body = parts[1] if len(parts) > 1 else text
        ab = ""
        for para in re.split(r"\n\s*\n", body):
            p = para.strip()
            if p and not p.startswith("#") and not p.startswith("**"):
                ab = p
                break
    ab = strip_md(ab)
    ab = re.sub(r"\s+", " ", ab).strip()
    return ab[:1600]


def extract_paper(md_path: Path) -> dict:
    text = md_path.read_text(encoding="utf-8")
    basename = md_path.stem

    m = re.search(r"^#\s+(.+)$", text, re.M)
    title = strip_md(m.group(1)) if m else basename

    num = letter = None
    m = re.search(r"Working Paper No\.?\s*(\d+)", text)
    if m:
        num = int(m.group(1))
    else:
        m = re.search(r"Working Paper\s+([A-Z])\b", text)
        if m:
            letter = m.group(1)

    author = ""
    m = re.search(r"^\*\*Author:\*\*\s*(.+)$", text, re.M)
    if m:
        author = m.group(1).strip()
    author = re.sub(r",?\s*with research assistance from Claude \(Anthropic\)", "", author)
    author = re.sub(r",?\s*Institute for a Christian Machine Intelligence", "", author)
    author = author.strip().rstrip(",").strip()

    date = ""
    m = re.search(r"^\*\*Date:\*\*\s*(.+)$", text, re.M)
    if m:
        date = m.group(1).strip()

    if num is not None:
        cite_label = f"ICMI-{num:03d}"
        label = f"ICMI Working Paper No. {num}"
        tiebreak = (1, num)  # letters (group 0) precede numbers (group 1) on a date tie
    elif letter is not None:
        cite_label = f"ICMI-{letter}"
        label = f"ICMI Working Paper {letter}"
        tiebreak = (0, ord(letter))
    else:
        cite_label = basename
        label = basename
        tiebreak = (2, 0)

    return {
        "basename": basename,
        "title": title,
        "author": author,
        "date": date,
        "parsed_date": parse_date(date),
        "abstract": extract_abstract(text),
        "cite_label": cite_label,
        "label": label,
        "tiebreak": tiebreak,
        "url": f"{SITE_BASE}/{basename}.html",
    }


def build_corpus(repo_dir: Path) -> list[dict]:
    papers = []
    for p in sorted(repo_dir.glob("ICMI-*.md")):
        try:
            papers.append(extract_paper(p))
        except Exception as e:  # noqa: BLE001 - one bad file shouldn't sink the build
            log(f"WARN failed to parse {p.name}: {e}")
    # Chronological order (oldest first): by date, then letters-before-numbers, then number.
    papers.sort(key=lambda d: (d["parsed_date"] or datetime.max, d["tiebreak"], d["basename"]))
    for i, d in enumerate(papers, 1):
        d["tag"] = i
    return papers


def corpus_hash(papers: list[dict], model: str) -> str:
    h = hashlib.sha256()
    h.update(f"v{PROMPT_VERSION}|{model}\n".encode())
    for d in papers:
        h.update(
            "|".join([d["basename"], d["title"], d["date"], d["abstract"]]).encode("utf-8")
        )
        h.update(b"\n")
    return h.hexdigest()


def build_user_prompt(papers: list[dict]) -> str:
    lines = [
        f"Here are all {len(papers)} ICMI working papers, ordered oldest to newest:",
        "",
    ]
    for d in papers:
        lines.append(f'[{d["tag"]}] {d["label"]} — "{d["title"]}"')
        meta = " · ".join(x for x in (d["author"], d["date"]) if x)
        if meta:
            lines.append(f"    {meta}")
        lines.append(f'    Abstract: {d["abstract"] or "(no abstract found)"}')
        lines.append("")
    lines.append(CITATION_INSTRUCTIONS.format(maxtag=len(papers)))
    return "\n".join(lines)


def substitute_citations(md: str, papers: list[dict]) -> tuple[str, set[int]]:
    by_tag = {d["tag"]: d for d in papers}
    cited: set[int] = set()

    def repl(m: re.Match) -> str:
        tag = int(m.group(1))
        d = by_tag.get(tag)
        if not d:
            log(f"WARN dropping unknown citation [[{tag}]]")
            return ""
        cited.add(tag)
        return f'[{d["cite_label"]}]({d["url"]})'

    md = re.sub(r"\[\[\s*(\d+)\s*\]\]", repl, md)
    return md, cited


def footer_md(papers: list[dict], model: str) -> str:
    latest = papers[-1]
    today = datetime.now(timezone.utc).strftime("%B %-d, %Y")
    return (
        "\n\n---\n\n"
        f"*Auto-generated on {today}, synthesizing the abstracts of all ICMI working "
        f'papers (most recent: [{latest["cite_label"]}]({latest["url"]}), '
        f'“{latest["title"]}”). Browse the [full Proceedings](index.html).*\n'
    )


def read_preamble(source_file: Path) -> str | None:
    """Return the frozen preamble — everything after the review-meta line up to (and not
    including) BODY_START_MARKER. None if the file is missing or has no marker."""
    try:
        text = source_file.read_text(encoding="utf-8")
    except OSError:
        return None
    if BODY_START_MARKER not in text:
        return None
    before = text.split(BODY_START_MARKER, 1)[0]
    lines = before.splitlines()
    if lines and lines[0].startswith(META_PREFIX):
        lines = lines[1:]
    return "\n".join(lines).strip()


def assemble_with_preamble(preamble: str, body: str, papers: list[dict], model: str) -> str:
    """Splice the (preserved) preamble, the body marker, the freshly generated body,
    and the footer into the full review markdown."""
    return (
        preamble.strip()
        + "\n\n"
        + BODY_START_MARKER
        + "\n\n"
        + body.strip()
        + footer_md(papers, model)
    )


def cited_tags(md: str, papers: list[dict]) -> set[int]:
    """The set of valid paper tags referenced by [[n]] markers in raw model output."""
    valid = {d["tag"] for d in papers}
    return {int(m) for m in re.findall(r"\[\[\s*(\d+)\s*\]\]", md) if int(m) in valid}


def generate_markdown(papers: list[dict], model: str) -> str:
    """Generate the review body. If the draft drops MORE than a tolerated number of
    papers (a few deliberate omissions are fine), make up to MAX_COVERAGE_REPAIRS
    follow-up passes nudging the model to weave the missing ones back in. Returns raw
    Markdown with [[n]] markers still in place (substitution happens afterwards)."""
    import anthropic  # imported lazily so --dry-run works without the package

    client = anthropic.Anthropic()
    headings = "\n".join(f"## {c}" for c in CATEGORIES)
    system = SYSTEM_PROMPT.format(n=len(papers), words=WORD_TARGET, headings=headings)

    def call(messages: list[dict]) -> str:
        resp = client.messages.create(
            model=model,
            max_tokens=MAX_OUTPUT_TOKENS,
            thinking={"type": "adaptive"},
            output_config={"effort": "high"},
            system=system,
            messages=messages,
        )
        if resp.stop_reason == "refusal":
            raise RuntimeError(
                "model declined the request (stop_reason=refusal"
                f", category={getattr(resp.stop_details, 'category', None)})"
            )
        text = "".join(b.text for b in resp.content if b.type == "text").strip()
        if not text:
            raise RuntimeError(f"model returned no text (stop_reason={resp.stop_reason})")
        return text

    messages = [{"role": "user", "content": build_user_prompt(papers)}]
    body = call(messages)

    # Tolerate a handful of deliberate omissions; only repair a wholesale drop.
    allowed = max(3, len(papers) // 5)
    for _ in range(MAX_COVERAGE_REPAIRS):
        missing = [d for d in papers if d["tag"] not in cited_tags(body, papers)]
        if len(missing) <= allowed:
            break
        log(f"coverage repair: {len(missing)} papers uncited (> {allowed} tolerated); revising")
        missing_list = "\n".join(
            f'[{d["tag"]}] {d["cite_label"]} — "{d["title"]}"' for d in missing
        )
        messages.append({"role": "assistant", "content": body})
        messages.append(
            {
                "role": "user",
                "content": (
                    "Quite a few papers aren't cited yet. Weave in the ones that "
                    "genuinely fit the narrative, each with its [[n]] marker; you may "
                    "leave out only papers that are minor controls or fully superseded. "
                    "Keep paragraphs short, the three categories intact, and the existing "
                    "citations. Return the full revised body in Markdown:\n\n" + missing_list
                ),
            }
        )
        body = call(messages)

    return body


def load_dotenv(repo_dir: Path) -> None:
    """If ANTHROPIC_API_KEY isn't already set, load it from a gitignored repo .env.
    Minimal parser (KEY=value, optional 'export' and quotes); no dependency."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return
    env_path = repo_dir / ".env"
    if not env_path.is_file():
        return
    try:
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            line = line[len("export "):].strip() if line.startswith("export ") else line
            if "=" not in line:
                continue
            key, val = line.split("=", 1)
            key, val = key.strip(), val.strip().strip("'\"")
            if key and key not in os.environ:
                os.environ[key] = val
    except Exception as e:  # noqa: BLE001
        log(f"WARN could not read {env_path}: {e}")


def have_api_credential() -> bool:
    return bool(
        os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    )


def read_source_meta(source_file: Path) -> dict | None:
    """Parse the review-meta header from a committed literature-review.md, or None."""
    try:
        first = source_file.read_text(encoding="utf-8").splitlines()[0]
    except (OSError, IndexError):
        return None
    if first.startswith(META_PREFIX) and first.rstrip().endswith(META_SUFFIX.strip()):
        try:
            return json.loads(first[len(META_PREFIX):].rstrip()[: -len(META_SUFFIX.strip())])
        except json.JSONDecodeError:
            return None
    return None


def write_source(source_file: Path, review_md: str, meta: dict) -> None:
    header = META_PREFIX + json.dumps(meta, separators=(",", ":")) + META_SUFFIX
    source_file.write_text(header + "\n" + review_md.strip() + "\n", encoding="utf-8")


def load_cache(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def save_cache(path: Path, data: dict) -> None:
    try:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        log(f"WARN could not write cache {path}: {e}")


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    repo_dir = script_dir.parent

    ap = argparse.ArgumentParser(description="Author/refresh the pinned ICMI review.")
    ap.add_argument("--repo-dir", type=Path, default=repo_dir)
    ap.add_argument("--source-file", type=Path, default=None,
                    help=f"committed review markdown (default <repo>/{SOURCE_FILENAME})")
    ap.add_argument("--cache", type=Path, default=script_dir / ".review-cache.json")
    ap.add_argument("--model", default=os.environ.get("ICMI_REVIEW_MODEL", DEFAULT_MODEL))
    ap.add_argument("--force", action="store_true",
                    help="regenerate even if the corpus is unchanged")
    ap.add_argument("--check", action="store_true",
                    help="report whether the review is stale; no API call, no writes")
    ap.add_argument("--strict", action="store_true",
                    help="with --check, exit 1 (instead of 0) when stale or missing")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the assembled prompt and exit (no API call, no writes)")
    args = ap.parse_args()

    load_dotenv(args.repo_dir)
    source_file: Path = args.source_file or (args.repo_dir / SOURCE_FILENAME)

    papers = build_corpus(args.repo_dir)
    if not papers:
        log("no ICMI-*.md papers found; nothing to do")
        return 0

    if args.dry_run:
        print(build_user_prompt(papers))
        log(f"parsed {len(papers)} papers (dry run; no API call)")
        return 0

    chash = corpus_hash(papers, args.model)
    meta = read_source_meta(source_file)
    up_to_date = bool(meta) and meta.get("corpus_hash") == chash

    # ---- --check: report staleness only (no API, no writes) ----
    if args.check:
        if not source_file.exists():
            log(f"{source_file.name} does not exist yet — run generate-review.py to create it")
            return 1 if args.strict else 0
        if up_to_date:
            log(f"{source_file.name} is up to date ({len(papers)} papers)")
            return 0
        log(f"WARN {source_file.name} is STALE — the corpus changed since it was "
            "generated. Refresh it with: python3 scripts/generate-review.py")
        return 1 if args.strict else 0

    # ---- regenerate the committed review ----
    if up_to_date and not args.force:
        log(f"{source_file.name} already up to date (hash {chash[:12]}); nothing to do "
            "(use --force to regenerate anyway)")
        return 0

    # Preserve the hand-written preamble (masthead, intro, mission) — only the
    # categorized body after BODY_START_MARKER is regenerated.
    preamble = read_preamble(source_file)
    if preamble is None:
        if source_file.exists() and not args.force:
            log(f"WARN {source_file.name} has no '{BODY_START_MARKER}' marker; refusing "
                "to regenerate so hand-edited content isn't overwritten. Add the marker "
                "above the first '## ' section, or pass --force to rebuild from a default "
                "preamble.")
            return 0
        preamble = DEFAULT_PREAMBLE  # fresh setup, or --force over a marker-less file

    cache = load_cache(args.cache)
    body = cited = None
    if cache and cache.get("corpus_hash") == chash and not args.force:
        log("reusing cached body (corpus unchanged since the last API call)")
        body = cache.get("body")
        cited = set(cache.get("cited_tags", []))

    if body is None:
        if not have_api_credential():
            log("WARN no ANTHROPIC_API_KEY (env or repo .env); leaving "
                f"{source_file.name} unchanged. Set the key and re-run to refresh it.")
            return 0
        try:
            raw = generate_markdown(papers, args.model)
            body, cited = substitute_citations(raw, papers)
            save_cache(args.cache, {
                "corpus_hash": chash,
                "model": args.model,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "cited_tags": sorted(cited),
                "paper_count": len(papers),
                "body": body,
            })
        except Exception as e:  # noqa: BLE001 - don't destroy the approved review
            log(f"ERROR generation failed ({e}); leaving {source_file.name} unchanged")
            return 0

    review_md = assemble_with_preamble(preamble, body, papers, args.model)
    coverage = f"cited {len(cited)}/{len(papers)} papers"
    omitted = [d["cite_label"] for d in papers if d["tag"] not in cited]
    if omitted:
        coverage += " (omitted: " + ", ".join(omitted) + " — add by hand if wanted)"
    log(f"assembled review (~{len(review_md.split())} words; {coverage})")

    write_source(source_file, review_md, {
        "corpus_hash": chash,
        "model": args.model,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "prompt_version": PROMPT_VERSION,
        "paper_count": len(papers),
    })
    log(f"wrote {source_file} — review the diff, then commit it")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
