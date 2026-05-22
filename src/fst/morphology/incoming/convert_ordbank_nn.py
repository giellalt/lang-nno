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


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FULLFORMS_ZIP = os.path.join(SCRIPT_DIR, "ordbank_nn", "fullformer_2012.txt.zip")
DEFAULT_PARADIGMS = os.path.join(SCRIPT_DIR, "ordbank_nn", "paradigme_nn.txt")
DEFAULT_STEMS_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "stems"))
DEFAULT_AFFIXES_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "affixes"))


@dataclass(frozen=True)
class FullformRow:
    source_row: int
    lemma_id: str
    wordform: str
    tags: str
    status: str
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
    "subst": "nouns.lexc",
    "subst_prop": "propernouns.lexc",
    "verb": "verbs.lexc",
    "adj": "adjectives.lexc",
    "adv": "adverbs.lexc",
    "pron": "pronouns.lexc",
    "det": "determiners.lexc",
    "prep": "prepositions.lexc",
    "pref": "prefixes.lexc",
    "fork": "abbreviations.lexc",
    "interj": "interjections.lexc",
    "konj": "conjunctions.lexc",
    "sbu": "subjunctions.lexc",
    "symb": "symbols.lexc",
    "i": "multiword.lexc",
    "other": "other.lexc",
}

STEM_ROOT_LEXICONS = {
    "nouns.lexc": "NounRoot",
    "propernouns.lexc": "ProperNoun",
    "adjectives.lexc": "AdjectiveRoot",
    "verbs.lexc": "VerbRoot",
}

LEGACY_ROOT_TO_EXISTING = {
    "NounOrdbankNN": "NounRoot",
    "ProperNounOrdbankNN": "ProperNoun",
    "AdjectiveOrdbankNN": "AdjectiveRoot",
    "VerbOrdbankNN": "VerbRoot",
}

MANAGED_STEM_FILES = set(STEM_ROOT_LEXICONS.keys())
MANAGED_AFFIX_FILES = {"nouns.lexc", "propernouns.lexc", "adjectives.lexc", "verbs.lexc"}

STEM_BLOCK_BEGIN = "! BEGIN ORDBANK_NN AUTO"
STEM_BLOCK_END = "! END ORDBANK_NN AUTO"
AFFIX_BLOCK_BEGIN = "! BEGIN ORDBANK_NN AUTO"
AFFIX_BLOCK_END = "! END ORDBANK_NN AUTO"

LEMMA_ID_RE = re.compile(r"\bLEMMA_ID=([^\s]+)")

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
        status = cols[-1].strip()
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
                status=status,
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


def pos_bucket(raw_label: str) -> str:
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
    tags: List[str] = []
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
    return ["".join(tags)] if tags else ["+X"]


def map_adj_tags(morph_desc: str) -> List[str]:
    md = morph_desc.strip().lower()
    if md == "pos m/f ub eint":
        return ["+Msc+Sg+Indef", "+Fem+Sg+Indef"]
    if md == "pos fl":
        return ["+Pl+Indef"]
    if md == "pos bu eint":
        return ["+Sg+Def"]
    if md == "pos nøyt ub eint" or md == "pos noyt ub eint":
        return ["+Neu+Sg+Indef"]
    if md == "komp":
        return ["+Comp"]
    if md == "sup ub":
        return ["+Superl+Indef"]
    if md == "sup bu":
        return ["+Superl+Def"]

    tags: List[str] = []
    for tok in md.split():
        mapped = normalize_free_token(tok)
        if mapped:
            tags.append("+" + mapped)
    return ["".join(tags)] if tags else ["+X"]


def map_verb_tags(morph_desc: str) -> List[str]:
    md = morph_desc.strip().lower()
    if md == "inf":
        return ["+Inf"]
    if md == "inf pass":
        return ["+Inf+Pass"]
    if md == "pres":
        return ["+Ind+Prs"]
    if md == "pret":
        return ["+Ind+Prt"]
    if md == "perf-part":
        return ["+PrfPtc"]
    if md.startswith("adj <perf-part>"):
        return ["+PrfPtc"]
    if md.startswith("adj <pres-part>"):
        return ["+PrsPtc"]
    if md == "imp":
        return ["+Imp"]

    tags: List[str] = []
    for tok in md.replace("<", " ").replace(">", " ").split():
        mapped = normalize_free_token(tok)
        if mapped:
            tags.append("+" + mapped)
    return ["".join(tags)] if tags else ["+X"]


def map_generic_tags(pos: str, morph_desc: str) -> List[str]:
    tags: List[str] = []
    for tok in morph_desc.strip().lower().split():
        mapped = normalize_free_token(tok)
        if mapped:
            tags.append("+" + mapped)
    return ["".join(tags)] if tags else ["+X"]


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


def has_err_orth_marker(rows: List[FullformRow]) -> bool:
    for row in rows:
        low = row.status.lower()
        if "unormert" in low or "unomert" in low:
            return True
    return False


def split_unescaped_plus(left: str) -> Tuple[str, List[str]]:
    parts = re.split(r"(?<!%)\+", left)
    lemma = parts[0]
    tags = ["+" + part for part in parts[1:] if part]
    return lemma, tags


def parse_lexc_entry(line: str) -> Tuple[str, str, str, str, str] | None:
    comment = ""
    code = line.rstrip("\n")
    if "!" in code:
        code, comment = code.split("!", 1)
        comment = comment.strip()
    code = code.strip()
    if not code or ":" not in code or ";" not in code:
        return None
    code = code.split(";", 1)[0].rstrip()
    left, right = code.split(":", 1)
    right = right.strip()
    if not right:
        return None
    if " " not in right:
        return None
    stem, cont_lex = right.rsplit(None, 1)
    lead = line[: len(line) - len(line.lstrip())]
    return lead, left.strip(), stem, cont_lex, comment


def extract_lemma_id(comment: str) -> str:
    match = LEMMA_ID_RE.search(comment)
    return match.group(1) if match else ""


def strip_managed_comment_fields(comment: str) -> str:
    out = re.sub(r"\bLEMMA_ID=[^\s]+", "", comment)
    out = re.sub(r"\bPARADIGME_ID=[^\s]+", "", out)
    out = re.sub(r"\bSOURCE_ROW=[^\s]+", "", out)
    out = re.sub(r"\bROOT=[^\s]+", "", out)
    return re.sub(r"\s+", " ", out).strip()


def format_stem_line(
    left: str,
    stem: str,
    cont_lex: str,
    lemma_id: str,
    extra_comment: str,
) -> str:
    base_comment = f"LEMMA_ID={lemma_id}"
    if extra_comment:
        base_comment += " " + extra_comment
    return f"{left}:{stem} {cont_lex} ; ! {base_comment}"


def find_lexicon_bounds(lines: List[str], lexicon_name: str) -> Tuple[int, int]:
    start = -1
    for idx, line in enumerate(lines):
        if line.strip() == f"LEXICON {lexicon_name}":
            start = idx
            break
    if start < 0:
        for idx, line in enumerate(lines):
            if not line_starts_lexicon(line):
                continue
            name = line.strip().split(maxsplit=1)[1]
            if LEGACY_ROOT_TO_EXISTING.get(name) == lexicon_name:
                lines[idx] = f"LEXICON {lexicon_name}"
                start = idx
                break
    if start < 0:
        lines.extend(["", f"LEXICON {lexicon_name}"])
        start = len(lines) - 1

    end = len(lines)
    for idx in range(start + 1, len(lines)):
        if line_starts_lexicon(lines[idx]):
            end = idx
            break
    return start, end


def line_starts_lexicon(line: str) -> bool:
    return line.lstrip().startswith("LEXICON ")


def ensure_managed_block(lines: List[str], start: int, end: int, begin: str, finish: str) -> Tuple[int, int]:
    begin_idx = -1
    end_idx = -1
    for idx in range(start + 1, end):
        if lines[idx].strip() == begin:
            begin_idx = idx
        if lines[idx].strip() == finish and begin_idx >= 0:
            end_idx = idx
            break

    if begin_idx >= 0 and end_idx >= 0:
        return begin_idx, end_idx

    insert_at = start + 1
    block = [begin, finish]
    lines[insert_at:insert_at] = block
    return insert_at, insert_at + 1


def merge_stem_file(path: str, root_lexicon: str, generated: Dict[str, Tuple[str, str, str, bool]]) -> int:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            lines = [line.rstrip("\n") for line in fh]
    else:
        lines = [
            "! Generated from ordbank_nn/fullformer_2012.txt.zip (ISO-8859-1 -> UTF-8).",
            f"LEXICON {root_lexicon}",
        ]

    if lines and "Generated from ordbank_nn/" in lines[0] and STEM_BLOCK_BEGIN not in lines:
        lines = [f"LEXICON {root_lexicon}"]

    start, end = find_lexicon_bounds(lines, root_lexicon)
    begin_idx, end_idx = ensure_managed_block(lines, start, end, STEM_BLOCK_BEGIN, STEM_BLOCK_END)

    existing_by_id: Dict[str, str] = {}
    for line in lines[begin_idx + 1 : end_idx]:
        parsed = parse_lexc_entry(line)
        if not parsed:
            continue
        lemma_id = extract_lemma_id(parsed[4])
        if lemma_id:
            existing_by_id[lemma_id] = line

    merged_lines: List[str] = []
    for lemma_id in sorted(generated.keys(), key=to_int):
        new_left, new_stem, new_cont, needs_err_orth = generated[lemma_id]
        extra_comment = ""
        if lemma_id in existing_by_id:
            parsed = parse_lexc_entry(existing_by_id[lemma_id])
            if parsed:
                _, existing_left, _, _, existing_comment = parsed
                new_lemma, new_tags = split_unescaped_plus(new_left)
                pos_tag = new_tags[0] if new_tags else ""
                _, existing_tags = split_unescaped_plus(existing_left)
                kept_tags = [tag for tag in existing_tags if tag != pos_tag]
                if needs_err_orth and "+Err/Orth" not in kept_tags:
                    kept_tags.append("+Err/Orth")
                new_left = new_lemma + pos_tag + "".join(kept_tags)
                extra_comment = strip_managed_comment_fields(existing_comment)
        elif needs_err_orth and "+Err/Orth" not in new_left:
            new_left += "+Err/Orth"

        merged_lines.append(
            format_stem_line(
                left=new_left,
                stem=new_stem,
                cont_lex=new_cont,
                lemma_id=lemma_id,
                extra_comment=extra_comment,
            )
        )

    lines[begin_idx + 1 : end_idx] = merged_lines
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for line in lines:
            fh.write(line + "\n")

    return len(merged_lines)


def write_stems(grouped_fullforms: Dict[str, List[FullformRow]], stem_dir: str) -> Dict[str, int]:
    os.makedirs(stem_dir, exist_ok=True)

    generated_by_file: Dict[str, Dict[str, Tuple[str, str, str, bool]]] = defaultdict(dict)
    counters: Dict[str, int] = defaultdict(int)

    for lemma_id, rows in grouped_fullforms.items():
        base = choose_base_row(rows)
        stem_file = pos_bucket(base.tags)
        if stem_file not in MANAGED_STEM_FILES:
            continue

        forms = sorted({row.wordform for row in rows})
        stem = longest_common_prefix(forms) or base.wordform
        pos_tag = stem_pos_tag(base.tags)
        left = f"{escape_lexc_lexeme(base.wordform)}{pos_tag}"
        err_orth = has_err_orth_marker(rows)
        if err_orth:
            left += "+Err/Orth"
        generated_by_file[stem_file][lemma_id] = (
            left,
            escape_lexc_lexeme(stem),
            base.paradigm_id,
            err_orth,
        )

    for stem_file, generated in generated_by_file.items():
        path = os.path.join(stem_dir, stem_file)
        root_lexicon = STEM_ROOT_LEXICONS[stem_file]
        counters[stem_file] = merge_stem_file(path, root_lexicon, generated)

    return counters


def merge_affix_file(path: str, generated_blocks: Sequence[str]) -> int:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            lines = [line.rstrip("\n") for line in fh]
    else:
        lines = []

    if lines and "Generated from ordbank_nn/" in lines[0] and AFFIX_BLOCK_BEGIN not in lines:
        lines = []

    begin_idx = -1
    end_idx = -1
    for idx, line in enumerate(lines):
        if line.strip() == AFFIX_BLOCK_BEGIN:
            begin_idx = idx
        if line.strip() == AFFIX_BLOCK_END and begin_idx >= 0:
            end_idx = idx
            break

    block_lines: List[str] = [AFFIX_BLOCK_BEGIN]
    if generated_blocks:
        block_lines.append("! Generated from ordbank_nn/paradigme_nn.txt (ISO-8859-1 -> UTF-8).")
        block_lines.append("! Continuation lexicon names are raw PARADIGME_ID values.")
        block_lines.append("! POS stays in stem entries; all other tags are here.")
        block_lines.append("")
        for i, block in enumerate(sorted(generated_blocks)):
            block_lines.extend(block.split("\n"))
            if i != len(generated_blocks) - 1:
                block_lines.append("")
    block_lines.append(AFFIX_BLOCK_END)

    if begin_idx >= 0 and end_idx >= 0:
        lines[begin_idx : end_idx + 1] = block_lines
    else:
        if lines and lines[-1] != "":
            lines.append("")
        lines.extend(block_lines)

    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for line in lines:
            fh.write(line + "\n")

    return sum(1 for block in generated_blocks for line in block.split("\n") if line.startswith(" "))


def write_affixes(grouped_paradigms: Dict[str, List[ParadigmRow]], affix_dir: str) -> Dict[str, int]:
    os.makedirs(affix_dir, exist_ok=True)

    by_file: Dict[str, List[str]] = defaultdict(list)
    counters: Dict[str, int] = defaultdict(int)

    for paradigm_id, rows in grouped_paradigms.items():
        pos = rows[0].pos if rows else ""
        affix_file = POS_TO_STEM_FILE[classify_pos(pos)]
        if affix_file not in MANAGED_AFFIX_FILES:
            continue

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
        by_file[affix_file].append("\n".join(lex_lines))

    for affix_file in MANAGED_AFFIX_FILES:
        blocks = by_file.get(affix_file, [])
        path = os.path.join(affix_dir, affix_file)
        counters[affix_file] = merge_affix_file(path, blocks)

    return counters


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fullforms-zip",
        default=DEFAULT_FULLFORMS_ZIP,
        help="Path to fullform zip export",
    )
    parser.add_argument(
        "--paradigms",
        default=DEFAULT_PARADIGMS,
        help="Path to paradigm export",
    )
    parser.add_argument("--stems-dir", default=DEFAULT_STEMS_DIR, help="Output directory for stem lexc files")
    parser.add_argument("--affixes-dir", default=DEFAULT_AFFIXES_DIR, help="Output directory for affix lexc files")
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