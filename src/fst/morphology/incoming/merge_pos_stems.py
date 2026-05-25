#!/usr/bin/env python3
"""Generalised merge of hand-written stem entries into the ORDBANK_NN AUTO block.

Usage:
    merge_pos_stems.py adjectives   [stems/adjectives.lexc]
    merge_pos_stems.py nouns        [stems/nouns.lexc]
    merge_pos_stems.py propernouns  [stems/propernouns.lexc]

For each POS, entries common to both the AUTO block and the manual section
are merged:
  - continuation lexicon  ← old (manual) entry
  - lemma+POS:stem format and LEMMA_ID comment ← new (AUTO) entry

The merged AUTO block is sorted alphabetically.
Manual entries with no AUTO counterpart are kept in place.
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

BEGIN = "! BEGIN ORDBANK_NN AUTO"
END   = "! END ORDBANK_NN AUTO"

# AUTO entry: e.g.  lemma+A:stem  ContLex ; ! LEMMA_ID=xxx
AUTO_RE = re.compile(r"^(\S+)\+([A-Z]):(\S+)\s+(\S+)\s+;(.*)$")
# manual entry: e.g.  stem  ContLex ;
MAN_RE  = re.compile(r"^(\S+)\s+(\S+)\s*;(.*)$")

# ------------------------------------------------------------------
# Config per POS
# ------------------------------------------------------------------
POS_CONFIG = {
    "adjectives": {
        "file":        "stems/adjectives.lexc",
        "pos_tag":     "A",
        "manual_lexicon": "regadj",   # named LEXICON to scan
    },
    "nouns": {
        "file":        "stems/nouns.lexc",
        "pos_tag":     "N",
        "manual_lexicon": None,        # entries directly after END marker
    },
    "propernouns": {
        "file":        "stems/propernouns.lexc",
        "pos_tag":     "N",
        "manual_lexicon": None,
    },
}


def parse_auto_entries(lines):
    """Return list of (lemma, pos, stem, cont_lex, comment_tail)."""
    entries = []
    for line in lines:
        m = AUTO_RE.match(line.strip())
        if m:
            lemma, pos, stem, cont, tail = m.groups()
            entries.append((lemma, pos, stem, cont, tail.strip()))
    return entries


def parse_manual_entries(lines):
    """Return list of (lemma, cont_lex) parsed from bare 'stem ContLex ;' lines."""
    entries = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("!") or stripped.startswith("LEXICON"):
            continue
        m = MAN_RE.match(stripped)
        if m:
            lemma, cont, _tail = m.groups()
            entries.append((lemma, cont))
    return entries


def find_section_bounds(lines, section_name):
    """Return (start_idx_exclusive, end_idx_exclusive) of body lines
    for a LEXICON named *section_name*.
    start is the line AFTER 'LEXICON section_name'.
    end is the first following 'LEXICON ' line, or EOF."""
    start = None
    for i, line in enumerate(lines):
        if line.strip() == f"LEXICON {section_name}":
            start = i + 1
            break
    if start is None:
        return None, None
    end = len(lines)
    for i in range(start, len(lines)):
        if lines[i].startswith("LEXICON "):
            end = i
            break
    return start, end


def merge(auto_entries, man_entries):
    """
    Returns (merged_lines, leftover_lemmas).

    For each lemma present in manual:
      - for each unique old cont_lex: emit lemma+POS:first_auto_stem old_cont ; ! first_auto_LEMMA_ID
    For lemmas only in AUTO: keep as-is.
    Deduplicated by (lemma, stem, cont), sorted alphabetically.
    """
    auto_by_lemma = defaultdict(list)
    for lemma, pos, stem, cont, tail in auto_entries:
        auto_by_lemma[lemma].append((pos, stem, cont, tail))

    man_by_lemma = defaultdict(list)
    for lemma, cont in man_entries:
        if cont not in man_by_lemma[lemma]:
            man_by_lemma[lemma].append(cont)

    merged = []
    leftover_lemmas = set()

    for lemma in sorted(man_by_lemma):
        if lemma not in auto_by_lemma:
            leftover_lemmas.add(lemma)
            continue
        first_pos, first_stem, _first_cont, first_tail = auto_by_lemma[lemma][0]
        for old_cont in man_by_lemma[lemma]:
            merged.append((lemma, first_pos, first_stem, old_cont, first_tail))

    for lemma in sorted(auto_by_lemma):
        if lemma in man_by_lemma:
            continue
        for pos, stem, cont, tail in auto_by_lemma[lemma]:
            merged.append((lemma, pos, stem, cont, tail))

    # Deduplicate by (lemma, stem, cont)
    seen = set()
    deduped = []
    for lemma, pos, stem, cont, tail in merged:
        key = (lemma, stem, cont)
        if key not in seen:
            seen.add(key)
            deduped.append((lemma, pos, stem, cont, tail))

    deduped.sort(key=lambda x: (x[0].casefold(), x[3]))

    entry_lines = []
    for lemma, pos, stem, cont, tail in deduped:
        comment = f" {tail}" if tail else ""
        entry_lines.append(f"{lemma}+{pos}:{stem} {cont} ;{comment}")

    return entry_lines, leftover_lemmas


def rebuild_file(path: Path, pos_tag: str, manual_lexicon: str | None):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    begin_idx = next(i for i, l in enumerate(lines) if l.strip() == BEGIN)
    end_idx   = next(i for i, l in enumerate(lines) if l.strip() == END)

    auto_lines = lines[begin_idx + 1 : end_idx]

    if manual_lexicon:
        man_start, man_end = find_section_bounds(lines, manual_lexicon)
        if man_start is None:
            sys.exit(f"ERROR: LEXICON {manual_lexicon} not found in {path}")
        man_body_lines = lines[man_start:man_end]
    else:
        # Manual entries are everything after END
        man_start = end_idx + 1
        man_end   = len(lines)
        man_body_lines = lines[man_start:man_end]

    auto_entries = parse_auto_entries(auto_lines)
    man_entries  = parse_manual_entries(man_body_lines)

    print(f"AUTO entries:    {len(auto_entries)}")
    print(f"Manual entries:  {len(man_entries)}")

    merged_lines, leftover_lemmas = merge(auto_entries, man_entries)

    common = len(set(l for l, *_ in auto_entries) & set(l for l, _ in man_entries))
    print(f"Felles lemma:    {common}")
    print(f"Berre AUTO:      {len(set(l for l,*_ in auto_entries)) - common}")
    print(f"Leftover manual: {len(leftover_lemmas)}")
    print(f"Merged entries:  {len(merged_lines)}")

    # Rebuild manual section keeping only leftover entries
    new_man_body = []
    for line in man_body_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("!"):
            new_man_body.append(line)
            continue
        if stripped.startswith("LEXICON "):
            new_man_body.append(line)
            continue
        m = MAN_RE.match(stripped)
        if m and m.group(1) not in leftover_lemmas:
            continue   # merged → drop
        new_man_body.append(line)

    # Strip trailing blank lines from new_man_body
    while new_man_body and not new_man_body[-1].strip():
        new_man_body.pop()

    # Assemble
    out = []
    out.extend(lines[: begin_idx + 1])   # up to and including BEGIN
    out.extend(merged_lines)
    out.extend(lines[end_idx : man_start])  # END marker + lines between END and manual body
    out.extend(new_man_body)
    if manual_lexicon:
        out.extend(lines[man_end:])       # rest of file after named lexicon

    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Wrote {path}")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)

    pos_name = sys.argv[1]
    if pos_name not in POS_CONFIG:
        sys.exit(f"Unknown POS '{pos_name}'. Choose from: {', '.join(POS_CONFIG)}")

    cfg  = POS_CONFIG[pos_name]
    base = Path(__file__).parent.parent
    path = Path(sys.argv[2]) if len(sys.argv) > 2 else base / cfg["file"]

    print(f"\n=== {pos_name} ({path}) ===")
    rebuild_file(path, cfg["pos_tag"], cfg["manual_lexicon"])


if __name__ == "__main__":
    main()
