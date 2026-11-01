import re

_AR_DIGITS = "٠١٢٣٤٥٦٧٨٩"
_EN_DIGITS = "0123456789"
_AR_TO_EN = str.maketrans({ord(_AR_DIGITS[i]): _EN_DIGITS[i] for i in range(10)})

def normalize_ar_digits(s: str) -> str:
    """Convert Arabic-Indic digits to ASCII digits."""
    if not isinstance(s, str):
        return s
    return s.translate(_AR_TO_EN)

def strip_tatweel(s: str) -> str:
    """Remove Arabic tatweel (kashida) character to stabilize OCR/LLM parsing."""
    if not isinstance(s, str):
        return s
    return s.replace("ـ", "")

def clean_spaces(s: str) -> str:
    """Collapse whitespace and tidy punctuation spacing for RAG/LLM input."""
    if not isinstance(s, str):
        return s
    s = s.replace("\r", "\n")
    # squash multiple spaces/newlines
    s = re.sub(r"[ \t\f\v]+", " ", s)
    s = re.sub(r"\n{2,}", "\n\n", s)
    s = s.strip()
    return s

def squeeze_newlines(s: str, max_consecutive: int = 2) -> str:
    """Limit consecutive newlines to improve chunking."""
    if not isinstance(s, str):
        return s
    pat = r"\n{" + str(max_consecutive + 1) + r",}"
    return re.sub(pat, "\n" * max_consecutive, s)

def normalize_whitespace(s: str) -> str:
    """One-liner normalization: digits + tatweel + spaces + limited newlines."""
    s = normalize_ar_digits(s)
    s = strip_tatweel(s)
    s = clean_spaces(s)
    s = squeeze_newlines(s, 2)
    return s

def safe_truncate(s: str, n: int) -> str:
    """Truncate without splitting surrogate pairs; add ellipsis if needed."""
    if not isinstance(s, str):
        return s
    return s if len(s) <= n else (s[: max(0, n - 1)] + "…")

import re

def strip_long_underscores(s: str, min_run: int = 5) -> str:
    """Remove signature-line underscores (e.g., '__________') to avoid fake entity extraction."""
    if not isinstance(s, str):
        return s
    return re.sub(rf"[_]{{{min_run},}}", " ", s)


from difflib import SequenceMatcher

# One-to-one replacements so offsets in the normalized text match the original
_QUOTE_FOLD = str.maketrans({"“": '"', "”": '"', "„": '"', "«": '"', "»": '"', "‘": "'", "’": "'", "`": "'"})


def _fold(s: str) -> str:
    return s.translate(_QUOTE_FOLD).lower()


def locate_quote(text: str, quote: str, min_match: int = 25):
    """
    Find a model-supplied quote in the source text and return the matching span
    copied from the source (never the model's wording). Tolerates curly vs straight
    quotes, case and small paraphrases. Returns None when nothing close enough exists.
    """
    src = " ".join((text or "").split())
    q = " ".join((quote or "").split()) if isinstance(quote, str) else ""
    if not src or not q:
        return None
    fs, fq = _fold(src), _fold(q)
    idx = fs.find(fq)
    if idx != -1:
        return src[idx : idx + len(q)]
    m = SequenceMatcher(None, fs, fq, autojunk=False).find_longest_match(0, len(fs), 0, len(fq))
    if m.size < max(min_match, int(len(fq) * 0.4)):
        return None
    start = max(0, m.a - m.b)
    end = min(len(src), start + len(q))
    # Snap to word boundaries
    while start > 0 and src[start - 1] != " ":
        start -= 1
    while end < len(src) and src[end] != " ":
        end += 1
    return src[start:end].strip()


def grounded_snippet(text: str, quote, max_len: int = 240) -> str:
    """The quoted span when it can be found in the source text, else the opening of the text."""
    snippet = locate_quote(text, quote) or " ".join((text or "").split())
    return snippet if len(snippet) <= max_len else snippet[: max_len - 1].rstrip() + "…"
