# Proceedings

Proceedings of the Institute for a Christian Machine Intelligence

## About

This repository contains the working paper series of the Institute for a Christian Machine Intelligence (ICMI). Working papers are pre-publication research documents exploring the intersection of Christian theology and machine intelligence.

## File Naming Convention

All working papers follow the format:

```
ICMI-[NUMBER]-[short-title].[ext]
```

- **NUMBER**: Zero-padded three-digit sequence number (e.g., `001`, `002`)
- **short-title**: Lowercase, hyphen-separated summary of the paper's subject
- **ext**: `.md` for Markdown, `.tex` for LaTeX

Each paper should be published in both Markdown and LaTeX formats. The Markdown version serves as the GitHub-readable version; the LaTeX version is the typeset-ready source.

Examples:
- `ICMI-001-attention-prayer-paradigm.md`
- `ICMI-001-attention-prayer-paradigm.tex`

## Working Paper Format

Every working paper should include:

1. **Title and designation**: The paper title followed by its ICMI Working Paper number (e.g., "ICMI Working Paper No. 1")
2. **Abstract**: A concise summary of the paper's argument and contributions
3. **Numbered sections**: Introduction, body sections, proposed experiments (where applicable), and conclusion
4. **Biblical citations**: References to scripture should use the English Standard Version (ESV) unless otherwise noted, with book, chapter, and verse specified inline (e.g., Psalm 46:10, ESV)
5. **Technical citations**: All technical claims must be supported by inline citations in author-date format (e.g., Vaswani et al., 2017). Every entry in the bibliography must appear at least once in the body text.
6. **Bibliography**: A complete list of references at the end of the paper, alphabetized by first author's surname

## Contributing

To propose a new working paper:

1. Claim the next available number in the sequence
2. Create both `.md` and `.tex` files following the naming convention above
3. Ensure all citations (biblical and technical) are verified for accuracy
4. Submit a pull request for review

## Current Papers

| No. | Title | Authors |
|-----|-------|---------|
| 001 | [Attention Is All You Need: The Prayer Paradigm of the Transformer](ICMI-001-attention-prayer-paradigm.md) | Tim Hwang |
| 002 | ["The Lord Is My Strength and My Shield": Imprecatory Psalm Injection and Cardinal Virtue Simulation in Large Language Models](ICMI-002-imprecatory-psalms-virtue-bench.md) | Christopher McCaffery |
| 003 | [Toward a Theology of Machine Temptation: Four Models for VirtueBench V2](ICMI-003-temptation-taxonomy-virtuebench.md) | Tim Hwang |
