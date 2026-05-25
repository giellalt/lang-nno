#!/usr/bin/env python3
"""Merge regular-verb entries into the ORDBANK_NN AUTO block of stems/verbs.lexc.

For verbs common to both sections:
- continuation lexicon  ← old (regular-verb) entry
- lemma, stem (+V:stem), codes after lemma ← new (AUTO) entry
- LEMMA_ID comment ← new (AUTO) entry

Result: a single sorted AUTO block; regular-verb retains only entries with
no AUTO counterpart.
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

BEGIN = "! BEGIN ORDBANK_NN AUTO"
END = "! END ORDBANK_NN AUTO"

# AUTO line: lemma+V:stem ContLex ; ! comment
AUTO_RE = re.compile(r"^(\S+)\+V:(\S+)\s+(\S+)\s+;(.*)$")
# regular-verb line: stem  ContLex ;   (with optional trailing spaces/comment)
REG_RE = re.compile(r"^(\S+)\s+(\S+)\s*;(.*)$")


def parse_auto_entries(lines):
    """Return list of (lemma, stem, cont_lex, comment_tail) for AUTO section lines."""
    entries = []
    for line in lines:
        m = AUTO_RE.match(line.strip())
        if m:
            lemma, stem, cont, tail = m.groups()
            entries.append((lemma, stem, cont, tail.strip()))
    return entries


def parse_reg_entries(lines):
    """Return list of (lemma, cont_lex) for regular-verb section lines."""
    entries = []
    for line in lines:
        m = REG_RE.match(line.strip())
        if m:
            lemma, cont, _tail = m.groups()
            entries.append((lemma, cont))
    return entries


def merge(auto_entries, reg_entries):
    """
    Produce merged entry list and leftover reg entries.

    For each lemma present in OLD (regular-verb):
      - For each unique OLD cont_lex for that lemma:
          emit lemma+V:first_auto_stem  old_cont ; ! first_auto_LEMMA_ID
      - Any AUTO entries for that lemma with a cont_lex NOT covered by old
        are dropped (the old entries are authoritative).
    For lemmas only in AUTO: keep as-is.

    Returns:
      merged   – list of formatted entry strings (sorted by lemma, then cont)
      leftover – list of raw old lines for lemmas with NO AUTO counterpart
    """
    # Index AUTO by lemma → list of (stem, cont, comment_tail)
    auto_by_lemma = defaultdict(list)
    for lemma, stem, cont, tail in auto_entries:
        auto_by_lemma[lemma].append((stem, cont, tail))

    # Index OLD by lemma → ordered-unique list of cont_lex values
    reg_by_lemma = defaultdict(list)
    for lemma, cont in reg_entries:
        if cont not in reg_by_lemma[lemma]:
            reg_by_lemma[lemma].append(cont)

    merged = []
    leftover_lemmas = set()

    # Handle common lemmas
    for lemma in sorted(reg_by_lemma):
        if lemma not in auto_by_lemma:
            leftover_lemmas.add(lemma)
            continue
        # Take the first AUTO entry for this lemma to get stem + LEMMA_ID
        first_stem, _first_cont, first_tail = auto_by_lemma[lemma][0]
        for old_cont in reg_by_lemma[lemma]:
            merged.append((lemma, first_stem, old_cont, first_tail))

    # Handle AUTO-only lemmas
    for lemma in sorted(auto_by_lemma):
        if lemma in reg_by_lemma:
            continue
        for stem, cont, tail in auto_by_lemma[lemma]:
            merged.append((lemma, stem, cont, tail))

    # Deduplicate by (lemma, stem, cont) keeping first occurrence
    seen = set()
    deduped = []
    for lemma, stem, cont, tail in merged:
        key = (lemma, stem, cont)
        if key not in seen:
            seen.add(key)
            deduped.append((lemma, stem, cont, tail))

    # Sort alphabetically by lemma, then cont
    deduped.sort(key=lambda x: (x[0].casefold(), x[2]))

    # Format
    entry_lines = []
    for lemma, stem, cont, tail in deduped:
        comment = f" {tail}" if tail else ""
        entry_lines.append(f"{lemma}+V:{stem} {cont} ;{comment}")

    return entry_lines, leftover_lemmas


def rebuild_file(path: Path):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Locate section boundaries
    begin_idx = next(i for i, l in enumerate(lines) if l.strip() == BEGIN)
    end_idx = next(i for i, l in enumerate(lines) if l.strip() == END)
    reg_lex_idx = next(
        (i for i, l in enumerate(lines) if l.strip() == "LEXICON regular-verb"), None
    )
    if reg_lex_idx is None:
        sys.exit("ERROR: 'LEXICON regular-verb' not found")

    # Everything after 'LEXICON regular-verb' until the next LEXICON or EOF
    # is the regular-verb body
    reg_body_start = reg_lex_idx + 1
    reg_body_end = len(lines)
    for i in range(reg_body_start, len(lines)):
        if lines[i].startswith("LEXICON ") and i != reg_body_start:
            reg_body_end = i
            break

    auto_lines = lines[begin_idx + 1 : end_idx]
    reg_lines = lines[reg_body_start:reg_body_end]

    auto_entries = parse_auto_entries(auto_lines)
    reg_entries = parse_reg_entries(reg_lines)

    print(f"AUTO entries:         {len(auto_entries)}")
    print(f"regular-verb entries: {len(reg_entries)}")

    merged_lines, leftover_lemmas = merge(auto_entries, reg_entries)

    print(f"Merged AUTO entries:  {len(merged_lines)}")
    print(f"Leftover (reg-only):  {len(leftover_lemmas)}")

    # Rebuild leftover regular-verb body (preserving blank lines and comments)
    new_reg_body = []
    for line in reg_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("!"):
            new_reg_body.append(line)
            continue
        m = REG_RE.match(stripped)
        if m:
            lemma = m.group(1)
            if lemma in leftover_lemmas:
                new_reg_body.append(line)
        # else: merged → drop from regular-verb

    # Assemble the new file
    out = []
    # Lines before and including BEGIN
    out.extend(lines[: begin_idx + 1])
    # New merged AUTO body
    out.extend(merged_lines)
    # END marker through end of file, with updated regular-verb body
    out.extend(lines[end_idx : reg_body_start])
    out.extend(new_reg_body)
    out.extend(lines[reg_body_end:])

    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Wrote {path}")


if __name__ == "__main__":
    target = Path(__file__).parent.parent / "stems" / "verbs.lexc"
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
    rebuild_file(target)
