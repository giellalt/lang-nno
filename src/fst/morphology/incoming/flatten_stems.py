#!/usr/bin/env python3
"""Flatten stem lexicons: remove BEGIN/END markers, merge leftover manual
entries into the main sorted list.

Usage:
    flatten_stems.py verbs        [stems/verbs.lexc]
    flatten_stems.py adjectives   [stems/adjectives.lexc]
    flatten_stems.py nouns        [stems/nouns.lexc]
    flatten_stems.py propernouns  [stems/propernouns.lexc]

After flattening each file contains a single alphabetically sorted entry list.
The only distinction between Ordbank entries and others is the presence of a
"! LEMMA_ID=..." comment.

Irregular/special lexicons (irregular-verb, irregadj, GOD, STOR, PROP) are
kept completely unchanged.
"""

import re
import sys
from pathlib import Path

BEGIN = "! BEGIN ORDBANK_NN AUTO"
END   = "! END ORDBANK_NN AUTO"

# Matches entries already in new format: lemma+POS:stem ...
NEW_FORMAT_RE = re.compile(r"^\S+\+\w+:")

# Config per POS
# keep_calls:   continuation calls to keep in the main lexicon (e.g. irregular-verb ;)
# flatten_lex:  named lexicons whose entries get merged into main and then removed
# keep_from:    first LEXICON name that begins the "keep untouched" tail section
# pos_tag:      tag to insert when converting old-format entries
POS_CONFIG = {
    "verbs": {
        "file":         "stems/verbs.lexc",
        "main_lexicon": "VerbRoot",
        "keep_calls":   ["irregular-verb"],
        "flatten_lex":  ["regular-verb"],
        "keep_from":    "irregular-verb",
        "pos_tag":      "V",
    },
    "adjectives": {
        "file":         "stems/adjectives.lexc",
        "main_lexicon": "AdjectiveRoot",
        "keep_calls":   ["irregadj"],
        "flatten_lex":  ["regadj"],
        "keep_from":    "irregadj",
        "pos_tag":      "A",
    },
    "nouns": {
        "file":         "stems/nouns.lexc",
        "main_lexicon": "NounRoot",
        "keep_calls":   [],
        "flatten_lex":  [],
        "keep_from":    None,
        "pos_tag":      "N",
    },
    "propernouns": {
        "file":         "stems/propernouns.lexc",
        "main_lexicon": "ProperNoun",
        "keep_calls":   [],
        "flatten_lex":  [],
        "keep_from":    None,
        "pos_tag":      "N",
    },
}


def is_entry(line: str) -> bool:
    """True for data lines (stem entries), False for LEXICON headers,
    comment lines, blank lines, and single-token continuation calls."""
    s = line.strip()
    if not s or s.startswith("!") or s.startswith("LEXICON "):
        return False
    # Single-token call like "irregular-verb ;" has exactly one non-ws token before ;
    # Data entries have at least two: the stem/lemma and the continuation class.
    tokens = s.rstrip(";").split()
    return len(tokens) >= 2


def convert_entry(line: str, pos_tag: str) -> str:
    """Convert old-format 'stem ContLex ;' to new 'stem+POS:stem ContLex ;'.
    Lines already in new format are returned unchanged."""
    s = line.strip()
    tokens = s.split()
    first = tokens[0]
    if NEW_FORMAT_RE.match(first):
        return s  # already lemma+POS:stem
    # old format: first token is both lemma and stem
    rest = " ".join(tokens[1:])
    return f"{first}+{pos_tag}:{first} {rest}"


def sort_key(line: str) -> str:
    first = line.strip().split()[0]
    # new format: lemma+POS:stem  → sort by lemma (before first +)
    base = first.split("+")[0]
    return base.casefold()


def find_lex_bounds(lines, lex_name):
    """Return (start, end) where start is index of 'LEXICON lex_name' line,
    end is the index of the next 'LEXICON ' line (or len(lines))."""
    start = None
    for i, l in enumerate(lines):
        if l.strip() == f"LEXICON {lex_name}":
            start = i
            break
    if start is None:
        return None, None
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("LEXICON "):
            end = i
            break
    return start, end


def flatten(path: Path, main_lexicon: str, keep_calls: list,
            flatten_lex: list, keep_from: str | None, pos_tag: str):
    text  = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # ------------------------------------------------------------------
    # 1. Find the "keep untouched tail" – everything from keep_from onward
    # ------------------------------------------------------------------
    tail_start = len(lines)
    if keep_from:
        for i, l in enumerate(lines):
            if l.strip() == f"LEXICON {keep_from}":
                # include a preceding blank line if present
                tail_start = i - 1 if i > 0 and not lines[i - 1].strip() else i
                break

    working = lines[:tail_start]
    tail    = lines[tail_start:]

    # ------------------------------------------------------------------
    # 2. Locate BEGIN / END markers within working section
    # ------------------------------------------------------------------
    begin_idx = next((i for i, l in enumerate(working) if l.strip() == BEGIN), None)
    end_idx   = next((i for i, l in enumerate(working) if l.strip() == END),   None)

    # ------------------------------------------------------------------
    # 3. Collect all entries
    # ------------------------------------------------------------------
    entries = []

    # a) entries inside the AUTO block
    if begin_idx is not None and end_idx is not None:
        for l in working[begin_idx + 1 : end_idx]:
            if is_entry(l):
                entries.append(convert_entry(l.strip(), pos_tag))

    # b) entries after END (inline in main lexicon – nouns / propernouns)
    if end_idx is not None:
        for l in working[end_idx + 1 :]:
            if is_entry(l):
                entries.append(convert_entry(l.strip(), pos_tag))

    # c) entries from named lexicons to flatten
    for lex_name in flatten_lex:
        start, end = find_lex_bounds(working, lex_name)
        if start is None:
            continue
        for l in working[start + 1 : end]:
            if is_entry(l):
                entries.append(convert_entry(l.strip(), pos_tag))

    # ------------------------------------------------------------------
    # 4. Sort
    # ------------------------------------------------------------------
    entries.sort(key=sort_key)

    print(f"  Entries collected: {len(entries)}")

    # ------------------------------------------------------------------
    # 5. Rebuild: main lexicon header + sorted entries + keep_calls + tail
    # ------------------------------------------------------------------
    # Find the main lexicon header line
    main_header_idx = next(
        i for i, l in enumerate(lines)
        if l.strip() == f"LEXICON {main_lexicon}"
    )

    out = []
    # Everything before (and including) the main lexicon header
    out.extend(lines[: main_header_idx + 1])
    # Sorted entries
    for e in entries:
        out.append(e)
    # Blank line + keep_calls (e.g. "irregular-verb ;")
    if keep_calls:
        out.append("")
        for call in keep_calls:
            out.append(f"{call} ;")
    # Tail (special lexicons)
    if tail:
        out.append("")
        out.extend(tail)

    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in POS_CONFIG:
        sys.exit(__doc__)

    pos  = sys.argv[1]
    cfg  = POS_CONFIG[pos]
    base = Path(__file__).parent.parent
    path = Path(sys.argv[2]) if len(sys.argv) > 2 else base / cfg["file"]

    print(f"\n=== Flattening {pos} ({path.name}) ===")
    flatten(
        path,
        cfg["main_lexicon"],
        cfg["keep_calls"],
        cfg["flatten_lex"],
        cfg["keep_from"],
        cfg["pos_tag"],
    )
    print(f"  Wrote {path}")


if __name__ == "__main__":
    main()
