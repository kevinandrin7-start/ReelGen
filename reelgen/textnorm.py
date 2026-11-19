"""Text normalisation and word error rate for comparing narration with a transcript."""
from __future__ import annotations

import re
from typing import Iterable, List, Tuple

_ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen " \
        "sixteen seventeen eighteen nineteen".split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def num_words(n: int) -> str:
    if n < 20:
        return _ONES[n]
    if n < 100:
        return _TENS[n // 10] + ("" if n % 10 == 0 else " " + _ONES[n % 10])
    if n < 1000:
        return _ONES[n // 100] + " hundred" + ("" if n % 100 == 0 else " " + num_words(n % 100))
    if n < 1_000_000:
        return num_words(n // 1000) + " thousand" + ("" if n % 1000 == 0 else " " + num_words(n % 1000))
    return str(n)


def acronyms_in(texts: Iterable[str]) -> set[str]:
    out = set()
    for t in texts:
        for tok in re.findall(r"\b[A-Z][A-Z0-9]{1,5}s?\b", t):
            out.add(tok.rstrip("s").lower() if tok.endswith("s") and tok[:-1].isupper() else tok.lower())
    return out


def normalize(text: str, acronyms: set[str] = frozenset(), say_as_word: set[str] = frozenset()) -> List[str]:
    t = text.replace("’", "'").replace("‘", "'").replace("“", " ").replace("”", " ")
    t = re.sub(r"(\d+)%", r"\1 percent", t)
    t = re.sub(r"(\d),(\d)", r"\1\2", t)
    t = t.lower()
    t = re.sub(r"[-–—/]", " ", t)
    t = re.sub(r"[^a-z0-9' ]+", " ", t)
    out: List[str] = []
    for tok in t.split():
        tok = tok.strip("'")
        if not tok:
            continue
        if tok.isdigit():
            out += num_words(int(tok)).split()
            continue
        base = tok[:-1] if tok.endswith("s") and tok[:-1] in acronyms else tok
        if base in acronyms and base not in say_as_word:
            out += list(base)  # "llm" -> l l m (matches "L L M" read aloud)
            continue
        if tok.endswith("'s"):
            tok = tok[:-2]
        out.append(tok)
    return out


def align(ref: List[str], hyp: List[str]) -> Tuple[int, List[Tuple[str, str, str]]]:
    """Levenshtein alignment. Returns (edits, ops) where ops are (op, ref_word, hyp_word)."""
    n, m = len(ref), len(hyp)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)
    ops, i, j = [], n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and d[i][j] == d[i - 1][j - 1] + (0 if ref[i - 1] == hyp[j - 1] else 1):
            ops.append(("ok" if ref[i - 1] == hyp[j - 1] else "sub", ref[i - 1], hyp[j - 1]))
            i, j = i - 1, j - 1
        elif i > 0 and d[i][j] == d[i - 1][j] + 1:
            ops.append(("del", ref[i - 1], ""))
            i -= 1
        else:
            ops.append(("ins", "", hyp[j - 1]))
            j -= 1
    return d[n][m], list(reversed(ops))


def wer(ref: List[str], hyp: List[str]) -> float:
    if not ref:
        return 0.0 if not hyp else 1.0
    return align(ref, hyp)[0] / len(ref)
