#!/usr/bin/env python3
"""Post-process generated HTML to hyperlink bibliography cross-references.

Scans _site/ICMI-*.html files for "ICMI Working Paper No. N" in bibliography
entries and replaces them with links to the corresponding paper's HTML page.
Source .md files are never touched.
"""

import glob
import os
import re
import sys

def main():
    site_dir = sys.argv[1] if len(sys.argv) > 1 else "_site"
    html_files = sorted(glob.glob(os.path.join(site_dir, "ICMI-*.html")))

    if not html_files:
        print("No ICMI HTML files found in", site_dir)
        return

    # Build map: paper number (int) -> HTML filename
    paper_map = {}
    for path in html_files:
        basename = os.path.basename(path)
        m = re.match(r"ICMI-(\d+)-", basename)
        if m:
            paper_map[int(m.group(1))] = basename

    # Process each file
    for path in html_files:
        basename = os.path.basename(path)
        # Determine this file's own paper number so we skip self-links
        self_match = re.match(r"ICMI-(\d+)-", basename)
        self_num = int(self_match.group(1)) if self_match else None

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        original = content
        for num, target_file in paper_map.items():
            if num == self_num:
                continue
            # Replace plain text "ICMI Working Paper No. N" with a hyperlink
            pattern = r'ICMI Working Paper No\.\s*' + str(num) + r'(?![0-9])'
            replacement = f'<a href="{target_file}">ICMI Working Paper No. {num}</a>'
            content = re.sub(pattern, replacement, content)

        if content != original:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  Cross-linked: {basename}")
        else:
            print(f"  No cross-links: {basename}")


if __name__ == "__main__":
    main()
