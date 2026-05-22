#!/usr/bin/env python3

"""Convert Ordbank Nynorsk exports to POS-split UTF-8 lexc files.

Design goals:
- one lemma per LEMMA_ID in stem files
- continuation lexicon name equals PARADIGME_ID
- POS tag is in stems right after lemma
- all non-POS tags are in affix files
- output is UTF-8 and suitable for further manual editing/check-in
"""

from __future__ import annotations

import argparse
import io
import os
import re
import unicodedata
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple


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
    "subst": ("nouns.lexc", "NounOrdbankNN"),
    "subst_prop": ("propernouns.lexc", "ProperNounOrdbankNN"),
    "verb": ("verbs.lexc", "VerbOrdbankNN"),
    "adj": ("adjectives.lexc", "AdjectiveOrdbankNN"),
    "adv": ("adverbs.lexc", "AdverbOrdbankNN"),
    "pron": ("pronouns.lexc", "PronounOrdbankNN"),
    "det": ("determiners.lexc", "DeterminerOrdbankNN"),
    "prep": ("prepositions.lexc", "PrepositionOrdbankNN"),
    "pref": ("prefixes.lexc", "PrefixOrdbankNN"),
    "fork": ("abbreviations.lexc", "AbbreviationOrdbankNN"),
    "interj": ("interjections.lexc", "InterjectionOrdbankNN"),
    "konj": ("conjunctions.lexc", "ConjunctionOrdbankNN"),
    "sbu": ("subjunctions.lexc", "SubjunctionOrdbankNN"),
    "symb": ("symbols.lexc", "SymbolOrdbankNN"),
    "i": ("multiword.lexc", "MultiwordOrdbankNN"),
    "other": ("other.lexc", "OtherOrdbankNN"),
}

POS_TO_TAG = {
    "subst": "+N",
    "verb": "+V",
    "adj": "+A",
    "adv": "+Adv",
    "pron": "+Pron",
    "det": "+Det",
    "prep": "+Pr",
    "pref": "+Pref",
    "fork": "+ABBR",
    "interj": "+Interj",
    "konj": "+CC",
    "sbu": "+CS",
    "symb": "+Symbol",
    "i": "+Multiword",
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
                yield unicodedata.normalize("NFC", line)


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
            line = unicodedata.normalize("NFC", raw_line.rstrip("\r\n"))
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


def is_proper_label(label: str) -> bool:
    low = label.lower()
    return " prop" in f" {low} " or low.endswith(" prop") or "egennamn" in low


def classify_pos(raw_label: str) -> str:
    base = normalize_pos_label(raw_label)
    if base == "subst" and is_proper_label(raw_label):
        return "subst_prop"
    return base if base in POS_TO_STEM_FILE else "other"


def pos_bucket(raw_label: str) -> Tuple[str, str]:
    key = classify_pos(raw_label)
    return POS_TO_STEM_FILE[key]


def choose_base_row(rows: List[FullformRow]) -> FullformRow:
    line_one = [row for row in rows if row.paradigm_line == "1"]
    if line_one:
        return sorted(line_one, key=lambda row: row.source_row)[0]

    numeric = [row for row in rows if row.paradigm_line.isdigit()]
    if numeric:
        return sorted(numeric, key=lambda row: (to_int(row.paradigm_line), row.source_row))[0]

    return rows[0]


def escape_lexc_lexeme(text: str) -> str:
    # Keep escaping minimal: only characters that conflict with lexc syntax.
    escaped = []
    for ch in text:
        if ch == "%":
            escaped.append("%%")
        elif ch == " ":
            escaped.append("% ")
        elif ch == ":":
            escaped.append("%:")
        elif ch == ";":
            escaped.append("%;")
        elif ch == "+":
            escaped.append("%+")
        elif ch == "#":
            escaped.append("%#")
        else:
            escaped.append(ch)
    return "".join(escaped)


def escape_affix_literal(text: str) -> str:
    escaped = []
    for ch in text:
        if ch == "%":
            escaped.append("%%")
        elif ch == " ":
            escaped.append("% ")
        elif ch == ":":
            escaped.append("%:")
        elif ch == ";":
            escaped.append("%;")
        elif ch == "#":
            escaped.append("%#")
        else:
            escaped.append(ch)
    return "".join(escaped)


def normalize_free_token(token: str) -> str:
    token = token.strip().lower().replace("/", "_")
    token = re.sub(r"[^0-9a-zA-ZæøåÆØÅ_-]", "", token)
    if not token:
        return ""
    parts = [p for p in re.split(r"[_-]+", token) if p]
    return "".join(p[:1].upper() + p[1:] for p in parts)


def parse_ending_code(raw_ending: str) -> str:
    # Ordbank uses '+' and '%' as code markers. We interpret them as
    # non-literal control markers and keep only the literal ending string.
    # Then we add the standard Nynorsk boundary marker explicitly below.
    code = raw_ending.strip()
    if code in {"", "-"}:
        return ""
    code = code.replace("+", "")
    code = code.replace("%", "")
    return code


def noun_gender_tags(pos_text: str) -> List[str]:
    p = pos_text.lower()
    if "mask" in p:
        return ["+Msc"]
    if "fem" in p:
        return ["+Fem"]
    if "nøyt" in p or "noyt" in p:
        return ["+Neu"]
    return []


def map_noun_tags(pos_text: str, morph_desc: str) -> List[str]:
    tags = ["+N"]
    if "prop" in pos_text.lower():
        tags.append("+Prop")
    tags.extend(noun_gender_tags(pos_text))

    md = morph_desc.strip().lower()
    if md == "eint ub":
        tags.extend(["+Sg", "+Indef"])
    elif md == "eint bu":
        tags.extend(["+Sg", "+Def"])
    elif md == "fl ub":
        tags.extend(["+Pl", "+Indef"])
    elif md == "fl bu":
        tags.extend(["+Pl", "+Def"])
    elif "ubøy" in md:
        tags.extend(["+Sg", "+Indef"])
    else:
        for tok in md.split():
            mapped = normalize_free_token(tok)
            if mapped:
                tags.append("+" + mapped)
    return ["".join(tags)]


def map_adj_tags(morph_desc: str) -> List[str]:
    md = morph_desc.strip().lower()
    if md == "pos m/f ub eint":
        return ["+A+Msc+Sg+Indef", "+A+Fem+Sg+Indef"]
    if md == "pos fl":
        return ["+A+Pl+Indef"]
    if md == "pos bu eint":
        return ["+A+Sg+Def"]
    if md == "pos nøyt ub eint" or md == "pos noyt ub eint":
        return ["+A+Neu+Sg+Indef"]
    if md == "komp":
        return ["+A+Comp"]
    if md == "sup ub":
        return ["+A+Superl+Indef"]
    if md == "sup bu":
        return ["+A+Superl+Def"]

    tags = ["+A"]
    for tok in md.split():
        mapped = normalize_free_token(tok)
        if mapped:
            tags.append("+" + mapped)
    return ["".join(tags)]


def map_verb_tags(morph_desc: str) -> List[str]:
    md = morph_desc.strip().lower()
    if md == "inf":
        return ["+V+Inf"]
    if md == "inf pass":
        return ["+V+Inf+Pass"]
    if md == "pres":
        return ["+V+Ind+Prs"]
    if md == "pret":
        return ["+V+Ind+Prt"]
    if md == "perf-part":
        return ["+V+PrfPtc"]
    if md.startswith("adj <perf-part>"):
        return ["+V+PrfPtc"]
    if md.startswith("adj <pres-part>"):
        return ["+V+PrsPtc"]
    if md == "imp":
        return ["+V+Imp"]

    tags = ["+V"]
    for tok in md.replace("<", " ").replace(">", " ").split():
        mapped = normalize_free_token(tok)
        if mapped:
            tags.append("+" + mapped)
    return ["".join(tags)]


def map_generic_tags(pos: str, morph_desc: str) -> List[str]:
    stem_tag = POS_TO_TAG.get(pos, "+X")
    tags = [stem_tag]
    for tok in morph_desc.strip().lower().split():
        mapped = normalize_free_token(tok)
        if mapped:
            tags.append("+" + mapped)
    return ["".join(tags)]


def map_affix_tags(pos_label: str, morph_desc: str) -> List[str]:
    pos_key = classify_pos(pos_label)
    if pos_key in {"subst", "subst_prop"}:
        return map_noun_tags(pos_label, morph_desc)
    if pos_key == "adj":
        return map_adj_tags(morph_desc)
    if pos_key == "verb":
        return map_verb_tags(morph_desc)
    return map_generic_tags(pos_key, morph_desc)


def stem_pos_tag(raw_pos_label: str) -> str:
    pos_key = classify_pos(raw_pos_label)
    if pos_key == "subst_prop":
        return "+N"
    return POS_TO_TAG.get(pos_key, "+X")


def write_stems(grouped_fullforms: Dict[str, List[FullformRow]], stem_dir: str) -> Dict[str, int]:
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
        pos_tag = stem_pos_tag(base.tags)
        line = (
            f"{escape_lexc_lexeme(base.wordform)}{pos_tag}:{escape_lexc_lexeme(stem)} {base.paradigm_id} ; "
            f"! LEMMA_ID={lemma_id} PARADIGME_ID={base.paradigm_id} "
            f"SOURCE_ROW={base.source_row} ROOT={root_lexicon}"
        )
        by_file[stem_file].append(line)
        counters[stem_file] += 1

    for stem_file, lines in by_file.items():
        lines.sort()
        root_lexicon = next((mapping[1] for mapping in POS_TO_STEM_FILE.values() if mapping[0] == stem_file), "OtherOrdbankNN")
        path = os.path.join(stem_dir, stem_file)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("! Generated from ordbank_nn/fullformer_2012.txt.zip (ISO-8859-1 -> UTF-8).\n")
            fh.write("! One lemma per LEMMA_ID, stem=longest common prefix, POS tag in stem line.\n")
            fh.write(f"LEXICON {root_lexicon}\n")
            for line in lines:
                fh.write(line + "\n")

    return counters


def write_affixes(grouped_paradigms: Dict[str, List[ParadigmRow]], affix_dir: str) -> Dict[str, int]:
    os.makedirs(affix_dir, exist_ok=True)

    by_file: Dict[str, List[str]] = defaultdict(list)
    counters: Dict[str, int] = defaultdict(int)

    for paradigm_id, rows in grouped_paradigms.items():
        pos = rows[0].pos if rows else ""
        affix_file = POS_TO_STEM_FILE[classify_pos(pos)][0]
        lexicon_header = f"LEXICON {paradigm_id}"
        lex_lines = [lexicon_header]
        for row in rows:
            if row.ending == "-":
                continue
            tags = map_affix_tags(row.pos, row.morph_desc)
            ending = parse_ending_code(row.ending)
            surf = "%>" + escape_affix_literal(ending)
            for tag in tags:
                lex_lines.append(
                    f" {tag}:{surf} # ; ! POS={row.pos} LINE={row.line_no} ENDING_RAW={row.ending}"
                )
                counters[affix_file] += 1
        by_file[affix_file].append("\n".join(lex_lines))

    for affix_file, blocks in by_file.items():
        path = os.path.join(affix_dir, affix_file)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("! Generated from ordbank_nn/paradigme_nn.txt (ISO-8859-1 -> UTF-8).\n")
            fh.write("! Continuation lexicon names are raw PARADIGME_ID values.\n")
            fh.write("! POS stays in stem entries; all other tags are here.\n\n")
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
    parser.add_argument("--stems-dir", default="../stems", help="Output directory for stem lexc files")
    parser.add_argument("--affixes-dir", default="../affixes", help="Output directory for affix lexc files")
    args = parser.parse_args()

    grouped_fullforms = parse_fullforms(args.fullforms_zip)
    grouped_paradigms = parse_paradigms(args.paradigms)

    stem_counts = write_stems(grouped_fullforms, args.stems_dir)
    affix_counts = write_affixes(grouped_paradigms, args.affixes_dir)

    print(f"Generated stems for {len(grouped_fullforms)} lemma IDs")
    for name in sorted(stem_counts):
        print(f"  stems/{name}: {stem_counts[name]} entries")

    print(f"Generated affix lexicons for {len(grouped_paradigms)} paradigm IDs")
    for name in sorted(affix_counts):
        print(f"  affixes/{name}: {affix_counts[name]} entries")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())