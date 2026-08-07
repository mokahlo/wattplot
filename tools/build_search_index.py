"""Build a static search index for the Wattplot docs site.

The Jekyll site is plain HTML -- no plugins -- so we don't get a
build-time search index for free. This script walks every .md
file under docs/ (excluding _internal/) and emits a JSON file
that the search.html page loads and queries with Fuse.js
(client-side fuzzy search).

Run:  python tools/build_search_index.py
Writes:  docs/search-index.json

Schema:
[
  {
    "title": "Pin map",
    "url":   "pinmap.html",
    "excerpt": "...150 chars of body around the first heading...",
    "section": "Hardware",
    "body":   "...up to 1500 chars of body text..."
  },
  ...
]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
OUT_PATH = DOCS_DIR / "search-index.json"
EXCLUDE_DIRS = {"_internal", "adr", "node_modules", "_site", ".jekyll-cache"}

# The Jekyll permalink scheme is /:basename.html -- so docs/control_law.md
# becomes /control_law.html. The nav links in the HTML pages all use
# that scheme.
URL_FOR_MD = lambda p: f"/{p.stem}.html"

# Match Markdown headers; we'll emit one entry per header, with the
# body text under it as the searchable content.
_HEADER_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


def _strip_markdown(text: str) -> str:
    """Crude Markdown -> plain text for the index.

    We don't need a real parser; we just want the searchable text
    to be roughly what a human would read. The client-side search
    ranks by fuzzy match on the body string, so a few stray
    backticks or asterisks are fine.
    """
    # Drop fenced code blocks (they're not useful for search)
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    # Drop inline code
    text = re.sub(r"`[^`]+`", " ", text)
    # Drop link syntax, keep the link text: [text](url) -> text
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # Drop image syntax
    text = re.sub(r"!\[[^\]]*\]\([^\)]+\)", " ", text)
    # Drop HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Drop emphasis
    text = re.sub(r"[*_]{1,3}([^*_]+)[*_]{1,3}", r"\1", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _make_excerpt(body: str, max_chars: int = 200) -> str:
    if len(body) <= max_chars:
        return body
    # Truncate at the nearest word boundary.
    truncated = body[:max_chars].rsplit(" ", 1)[0]
    return truncated + "..."


def _entries_for_file(md_path: Path) -> list[dict]:
    """Split a Markdown file into per-header entries.

    The first H1 is the page title; the body under it (plus
    everything up to the next H2) is the lead entry. Each H2+
    becomes its own entry; if there's no H2, the file is one
    entry.
    """
    text = md_path.read_text(encoding="utf-8")
    # Strip the front matter
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end > 0:
            text = text[end + 4 :]

    # Find all header positions
    headers = [(m.start(), len(m.group(1)), m.group(2))
               for m in _HEADER_RE.finditer(text)]

    if not headers:
        # No headers -- treat the whole file as one entry
        body = _strip_markdown(text)
        return [{
            "title":   md_path.stem.replace("-", " ").replace("_", " "),
            "url":     URL_FOR_MD(md_path),
            "excerpt": _make_excerpt(body, 200),
            "section": "(no headers)",
            "body":    body[:1500],
        }]

    entries = []
    for i, (pos, level, title) in enumerate(headers):
        end = headers[i + 1][0] if i + 1 < len(headers) else len(text)
        body = _strip_markdown(text[pos:end])
        if not body.strip():
            continue
        # The "section" is the topmost header under which this
        # header lives (level 1 if any, else level 2).
        section = "(top)"
        for prev_pos, prev_level, prev_title in headers[:i][::-1]:
            if prev_level < level:
                section = prev_title
                break
        entries.append({
            "title":   title,
            "url":     URL_FOR_MD(md_path),
            "excerpt": _make_excerpt(body, 200),
            "section": section,
            "body":    body[:1500],
        })
    return entries


def main():
    if not DOCS_DIR.is_dir():
        print(f"docs/ not found at {DOCS_DIR}; run from the repo root",
              file=sys.stderr)
        sys.exit(1)

    all_entries = []
    for md_path in sorted(DOCS_DIR.rglob("*.md")):
        if any(part in EXCLUDE_DIRS for part in md_path.parts):
            continue
        try:
            entries = _entries_for_file(md_path)
        except Exception as exc:
            print(f"  skip {md_path}: {exc}")
            continue
        all_entries.extend(entries)
        print(f"  +{len(entries):3d}  {md_path.relative_to(REPO_ROOT)}")

    OUT_PATH.write_text(json.dumps(all_entries, indent=2), encoding="utf-8")
    print(f"\nWrote {len(all_entries)} entries to {OUT_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()