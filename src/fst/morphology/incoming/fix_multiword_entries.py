#!/usr/bin/env python3
"""Fix broken multi-word entries produced by convert_entry.

When an old-format entry was multi-word (e.g. `agnus% Dei N1 ;`), convert_entry
only grabbed the first whitespace-token as the lemma, giving:
    agnus%+N:agnus% Dei N1 ;

The `%` in lexc escapes the following space, so `agnus% Dei` is lexc for
the form "agnus Dei". The lemma part should match the full stem.

This script detects the pattern `word%+POS:` in the first whitespace-token
(the `%` was originally escaping a space that got absorbed) and rebuilds
the entry as:
    agnus% Dei+N:agnus% Dei N1 ;
"""
import re
from pathlib import Path

# First whitespace-token of a broken entry: something%+POS:something
# The % immediately before +POS: is the telltale sign.
BROKEN_RE = re.compile(r'^(.*%)(\+[A-Z][^:]*:)(\S*)$')

FILES = [
    "stems/verbs.lexc",
    "stems/adjectives.lexc",
    "stems/nouns.lexc",
    "stems/propernouns.lexc",
]


def fix_line(line: str) -> str:
    s = line.rstrip('\n')
    stripped = s.strip()

    if not stripped or stripped.startswith('!') or stripped.startswith('LEXICON'):
        return s + '\n'

    # Split off trailing comment (` ! ...`)
    if ' ! ' in stripped:
        idx = stripped.index(' ! ')
        body    = stripped[:idx]
        comment = stripped[idx:]
    else:
        body    = stripped
        comment = ''

    # Remove trailing semicolon and whitespace for token analysis
    body_core = body.rstrip().rstrip(';').rstrip()
    tokens = body_core.split()

    # Need first_token + at least one middle word + contlex
    if len(tokens) < 3:
        return s + '\n'

    first_token = tokens[0]
    m = BROKEN_RE.match(first_token)
    if not m:
        return s + '\n'

    lemma_head = m.group(1)   # e.g. 'agnus%'
    pos_colon  = m.group(2)   # e.g. '+N:'
    stem_start = m.group(3)   # e.g. 'agnus%'

    contlex       = tokens[-1]
    middle_tokens = tokens[1:-1]  # words between first_token and contlex

    if not middle_tokens:
        return s + '\n'

    middle_str = ' '.join(middle_tokens)
    full_lemma = f'{lemma_head} {middle_str}'   # e.g. 'agnus% Dei'
    full_stem  = f'{stem_start} {middle_str}'   # e.g. 'agnus% Dei'

    new_line = f'{full_lemma}{pos_colon}{full_stem} {contlex} ;{comment}'
    return new_line + '\n'


def process_file(path: Path) -> int:
    lines = path.read_text(encoding='utf-8').splitlines(keepends=True)
    out   = []
    fixed = 0
    for line in lines:
        new = fix_line(line)
        if new.rstrip('\n') != line.rstrip('\n'):
            fixed += 1
        out.append(new)
    path.write_text(''.join(out), encoding='utf-8')
    return fixed


def main():
    base  = Path(__file__).parent.parent
    total = 0
    for rel in FILES:
        path = base / rel
        n = process_file(path)
        print(f'  {path.name}: {n} fixed')
        total += n
    print(f'  Total: {total} entries fixed')


if __name__ == '__main__':
    main()
