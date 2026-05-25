#!/usr/bin/env python3
"""Move entries whose lemma starts with '-' from the main root lexicon
into a dedicated *_lastpart lexicon.

These entries are not full lemmas but bound combining forms that require
a preceding element (last parts of compounds).

Usage:
    extract_lastpart.py verbs
    extract_lastpart.py adjectives
    extract_lastpart.py nouns

No action is taken for propernouns (no '-' entries).
"""

import sys
from pathlib import Path

POS_CONFIG = {
    "verbs": {
        "file":         "stems/verbs.lexc",
        "main_lexicon": "VerbRoot",
        "lastpart_lex": "verbs_lastpart",
        "tail_lex":     "irregular-verb",   # first LEXICON of keep-tail
    },
    "adjectives": {
        "file":         "stems/adjectives.lexc",
        "main_lexicon": "AdjectiveRoot",
        "lastpart_lex": "adjectives_lastpart",
        "tail_lex":     "irregadj",
    },
    "nouns": {
        "file":         "stems/nouns.lexc",
        "main_lexicon": "NounRoot",
        "lastpart_lex": "nouns_lastpart",
        "tail_lex":     None,               # no tail lexicon
    },
}


def is_lastpart_entry(line: str) -> bool:
    """True if the first token (lemma) starts with '-'."""
    s = line.strip()
    if not s or s.startswith("!") or s.startswith("LEXICON"):
        return False
    first = s.split()[0]
    return first.startswith("-")


def extract(path: Path, main_lexicon: str, lastpart_lex: str, tail_lex: str | None):
    lines = path.read_text(encoding="utf-8").splitlines()

    # Locate main lexicon header
    main_idx = next(
        i for i, l in enumerate(lines)
        if l.strip() == f"LEXICON {main_lexicon}"
    )

    # Locate start of tail section (lexicons to keep untouched)
    tail_start = len(lines)
    if tail_lex:
        for i, l in enumerate(lines):
            if l.strip() == f"LEXICON {tail_lex}":
                tail_start = i - 1 if i > 0 and not lines[i - 1].strip() else i
                break

    # Split lines into: header (before main_idx+1), body, tail
    header = lines[: main_idx + 1]
    body   = lines[main_idx + 1 : tail_start]
    tail   = lines[tail_start :]

    # Partition body into normal entries, lastpart entries, and other lines
    normal   = []
    lastpart = []
    for l in body:
        if is_lastpart_entry(l):
            lastpart.append(l.strip())
        else:
            normal.append(l)

    print(f"  Main entries kept : {sum(1 for l in normal if l.strip() and not l.strip().startswith('!') and l.strip().endswith(';'))}")
    print(f"  Moved to lastpart : {len(lastpart)}")

    if not lastpart:
        print("  Nothing to move.")
        return

    # Remove trailing blanks from normal
    while normal and not normal[-1].strip():
        normal.pop()

    # Find the existing keep_calls in normal (e.g. "irregular-verb ;")
    # They are single-token continuation calls at the end of body.
    # We want to insert "lastpart_lex ;" before them.
    # Find the first continuation-call-only line at the end
    split_pos = len(normal)
    for i in range(len(normal) - 1, -1, -1):
        s = normal[i].strip()
        if not s or s.startswith("!"):
            continue
        toks = s.rstrip(";").split()
        if len(toks) == 1:  # single-token call
            split_pos = i
        else:
            break

    body_entries   = normal[:split_pos]
    keep_calls_raw = normal[split_pos:]

    # Remove trailing blanks from body_entries
    while body_entries and not body_entries[-1].strip():
        body_entries.pop()

    # Build output
    out = list(header)
    out.extend(body_entries)
    out.append("")
    out.append(f"{lastpart_lex} ;")
    if keep_calls_raw:
        stripped_calls = [l for l in keep_calls_raw if l.strip()]
        if stripped_calls:
            for c in stripped_calls:
                out.append(c)
    if tail:
        out.append("")
        out.extend(tail)

    # Append new lastpart lexicon at the very end
    while out and not out[-1].strip():
        out.pop()
    out.append("")
    out.append(f"LEXICON {lastpart_lex}")
    for e in lastpart:
        out.append(e)

    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in POS_CONFIG:
        sys.exit(__doc__)

    pos  = sys.argv[1]
    cfg  = POS_CONFIG[pos]
    base = Path(__file__).parent.parent
    path = Path(sys.argv[2]) if len(sys.argv) > 2 else base / cfg["file"]

    print(f"\n=== Extracting lastpart entries from {pos} ({path.name}) ===")
    extract(path, cfg["main_lexicon"], cfg["lastpart_lex"], cfg["tail_lex"])
    print(f"  Wrote {path}")


if __name__ == "__main__":
    main()
