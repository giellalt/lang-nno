#!/usr/bin/env python3

"""Convert Ordbank Nynorsk fullforms and paradigms to lexc files.

This script is intentionally conservative and metadata-heavy to support
re-imports without clobbering manual edits in lexc files.
"""

from __future__ import annotations

import argparse
import io
import os
import re
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class FullformRow:
    source_row: int
    lemma_id: str
    wordform: str
    tags: str
    paradigm_id: str
    paradigm_line: str


@dataclass(frozen=True)
class ParadigmRow:
    paradigm_id: str
    pos: str
    description: str
    completeness: str
    example: str
    line_no: str
    morph_desc: str
    ending: str


ROW_RE = re.compile(r"^\d+\t\d+\t")

POS_TO_STEM_FILE = {
    "subst": ("nouns.lexc", "Noun"),
    "verb": ("verbs.lexc", "Verb"),
    "adj": ("adjectives.lexc", "Adjective"),
    "adv": ("adverbs.lexc", "Adverb"),
    "pron": ("pronouns.lexc", "Pronoun"),
    "det": ("determiners.lexc", "Determiner"),
    "prep": ("prepositions.lexc", "Preposition"),
    "pref": ("prefixes.lexc", "Prefix"),
    "fork": ("abbreviations.lexc", "Abbreviation"),
    "interj": ("interjections.lexc", "Interjection"),
    "konj": ("conjunctions.lexc", "Conjunction"),
    "sbu": ("subjunctions.lexc", "Subjunction"),
    "symb": ("symbols.lexc", "Symbol"),
    "i": ("multiword.lexc", "Multiword"),
    "egennamn": ("propernouns.lexc", "ProperNoun"),
    "prop": ("propernouns.lexc", "ProperNoun"),
}


def read_zip_text(path: str, encoding: str = "iso-8859-1") -> Iterable[str]:
    with zipfile.ZipFile(path) as zf:
        members = [name for name in zf.namelist() if not name.endswith("/")]
        if not members:
            raise RuntimeError(f"No files in zip archive: {path}")
        # Use the first regular file in archive.
        with zf.open(members[0]) as fh:
            text = io.TextIOWrapper(fh, encoding=encoding, newline="")
            for line in text:
                yield line


def normalize_input_lines(lines: Iterable[str]) -> Iterable[str]:
    """Yield only data lines, handling preamble and trailer blocks."""
    started = False
    for raw_line in lines:
        line = raw_line.rstrip("\r\n")
        if "Mac OS X" in line:
            break
        if not started:
            if ROW_RE.match(line):
                started = True
            else:
                continue
        if line:
            yield line


def parse_fullforms(path: str) -> Dict[str, List[FullformRow]]:
    grouped: Dict[str, List[FullformRow]] = defaultdict(list)
    for line in normalize_input_lines(read_zip_text(path)):
        cols = line.split("\t")
        if len(cols) < 6:
            continue
        source_row = to_int(cols[0])
        lemma_id = cols[1].strip()
        wordform = cols[2].strip()
        tags = cols[3].strip()
        paradigm_id = cols[4].strip()
        paradigm_line = cols[5].strip()
        if not lemma_id or not wordform or not paradigm_id:
            continue
        grouped[lemma_id].append(
            FullformRow(
                source_row=source_row,
                lemma_id=lemma_id,
                wordform=wordform,
                tags=tags,
                paradigm_id=paradigm_id,
                paradigm_line=paradigm_line,
            )
        )
    for lemma_id in grouped:
        grouped[lemma_id].sort(key=lambda row: row.source_row)
    return grouped


def parse_paradigms(path: str) -> Dict[str, List[ParadigmRow]]:
    grouped: Dict[str, List[ParadigmRow]] = defaultdict(list)
    with open(path, "r", encoding="iso-8859-1", newline="") as fh:
        for raw_line in fh:
            line = raw_line.rstrip("\r\n")
            if not line:
                continue
            if line.startswith("*"):
                continue
            cols = line.split("\t")
            if len(cols) < 8:
                continue
            row = ParadigmRow(
                paradigm_id=cols[0].strip(),
                pos=cols[1].strip(),
                description=cols[2].strip(),
                completeness=cols[3].strip(),
                example=cols[4].strip(),
                line_no=cols[5].strip(),
                morph_desc=cols[6].strip(),
                ending=cols[7].strip(),
            )
            if row.paradigm_id:
                grouped[row.paradigm_id].append(row)
    for paradigm_id in grouped:
        grouped[paradigm_id].sort(key=lambda row: to_int(row.line_no))
    return grouped


def to_int(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        return 0


def longest_common_prefix(values: List[str]) -> str:
    if not values:
        return ""
    prefix = values[0]
    for value in values[1:]:
        max_len = min(len(prefix), len(value))
        i = 0
        while i < max_len and prefix[i] == value[i]:
            i += 1
        prefix = prefix[:i]
        if not prefix:
            break
    return prefix


def normalize_pos_label(raw_label: str) -> str:
    label = raw_label.strip().lower()
    if not label:
        return ""
    first = label.split()[0]
    if "+" in first:
        first = first.split("+", 1)[0]
    return first


def pos_bucket(raw_tags: str) -> Tuple[str, str]:
    normalized = normalize_pos_label(raw_tags)
    stem_file, root_lexicon = POS_TO_STEM_FILE.get(normalized, ("other.lexc", "Entries"))
    return stem_file, root_lexicon


def choose_base_row(rows: List[FullformRow]) -> FullformRow:
    line_one = [row for row in rows if row.paradigm_line == "1"]
    if line_one:
        return sorted(line_one, key=lambda row: row.source_row)[0]

    numeric = [row for row in rows if row.paradigm_line.isdigit()]
    if numeric:
        return sorted(numeric, key=lambda row: (to_int(row.paradigm_line), row.source_row))[0]

    return rows[0]


def escape_lexc(text: str) -> str:
    return text.replace("%", "%%").replace(" ", "% ")


def normalize_tag_string(tag_string: str) -> str:
    out = tag_string
    out = out.replace("+", "_")
    out = out.replace("< ", "<").replace(" >", ">")
    out = out.replace("<.", "<").replace(".>", ">")
    out = out.replace("(", "/")
    out = out.replace("<>", "")
    out = re.sub(r"\s+", " ", out).strip()
    out = out.replace("<", "%<").replace(">", "%>")
    if not out:
        return ""
    return "".join("+" + token for token in out.split(" "))


def strip_plus_markers(ending: str) -> str:
    # The plus markers in Ordbank endings encode stem interaction. For a first
    # pass we remove them and keep original value in comments for traceability.
    return ending.replace("+", "")


def write_stems(
    grouped_fullforms: Dict[str, List[FullformRow]], out_dir: str
) -> Dict[str, int]:
    stem_dir = os.path.join(out_dir, "stems")
    os.makedirs(stem_dir, exist_ok=True)

    by_file: Dict[str, List[str]] = defaultdict(list)
    counters: Dict[str, int] = defaultdict(int)

    for lemma_id, rows in grouped_fullforms.items():
        base = choose_base_row(rows)
        forms = sorted({row.wordform for row in rows})
        stem = longest_common_prefix(forms)
        if not stem:
            stem = base.wordform

        stem_file, root_lexicon = pos_bucket(base.tags)
        line = (
            f"{escape_lexc(base.wordform)}:{escape_lexc(stem)} {base.paradigm_id} ; "
            f"! LEMMA_ID={lemma_id} PARADIGME_ID={base.paradigm_id} "
            f"SOURCE_ROW={base.source_row} ROOT={root_lexicon}"
        )
        by_file[stem_file].append(line)
        counters[stem_file] += 1

    for stem_file, lines in by_file.items():
        lines.sort()
        root_lexicon = "Entries"
        for pos, mapping in POS_TO_STEM_FILE.items():
            if mapping[0] == stem_file:
                root_lexicon = mapping[1]
                break
        path = os.path.join(stem_dir, stem_file)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("! Generated from ordbank_nn/fullformer_2012.txt.zip\n")
            fh.write("! One lemma per LEMMA_ID, with stem = longest common prefix of forms.\n")
            fh.write(f"LEXICON {root_lexicon}\n")
            for line in lines:
                fh.write(line + "\n")

    return counters


def write_affixes(
    grouped_paradigms: Dict[str, List[ParadigmRow]], out_dir: str
) -> Dict[str, int]:
    affix_dir = os.path.join(out_dir, "affixes")
    os.makedirs(affix_dir, exist_ok=True)

    by_file: Dict[str, List[str]] = defaultdict(list)
    counters: Dict[str, int] = defaultdict(int)

    for paradigm_id, rows in grouped_paradigms.items():
        pos = normalize_pos_label(rows[0].pos) if rows else ""
        affix_file = POS_TO_STEM_FILE.get(pos, ("other.lexc", "Entries"))[0]
        lexicon_header = f"LEXICON {paradigm_id}"
        lex_lines = [lexicon_header]
        for row in rows:
            tag = normalize_tag_string(row.morph_desc)
            if row.ending == "-":
                continue
            ending = strip_plus_markers(row.ending)
            surf = escape_lexc(ending)
            lex_lines.append(
                f" {tag}:{surf} # ; ! POS={row.pos} LINE={row.line_no} ENDING_RAW={row.ending}"
            )
            counters[affix_file] += 1
        by_file[affix_file].append("\n".join(lex_lines))

    for affix_file, blocks in by_file.items():
        path = os.path.join(affix_dir, affix_file)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("! Generated from ordbank_nn/paradigme_nn.txt\n")
            fh.write("! Continuation lexicon names are raw PARADIGME_ID values.\n\n")
            fh.write("\n\n".join(sorted(blocks)) + "\n")

    return counters


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fullforms-zip",
        default="ordbank_nn/fullformer_2012.txt.zip",
        help="Path to fullform zip export",
    )
    parser.add_argument(
        "--paradigms",
        default="ordbank_nn/paradigme_nn.txt",
        help="Path to paradigm export",
    )
    parser.add_argument(
        "--out-dir",
        default="generated_nn_lexc",
        help="Output directory for generated lexc files",
    )
    args = parser.parse_args()

    grouped_fullforms = parse_fullforms(args.fullforms_zip)
    grouped_paradigms = parse_paradigms(args.paradigms)

    os.makedirs(args.out_dir, exist_ok=True)
    stem_counts = write_stems(grouped_fullforms, args.out_dir)
    affix_counts = write_affixes(grouped_paradigms, args.out_dir)

    print(f"Generated stems for {len(grouped_fullforms)} lemma IDs")
    for name in sorted(stem_counts):
        print(f"  stems/{name}: {stem_counts[name]} entries")

    print(f"Generated affix lexicons for {len(grouped_paradigms)} paradigm IDs")
    for name in sorted(affix_counts):
        print(f"  affixes/{name}: {affix_counts[name]} entries")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())