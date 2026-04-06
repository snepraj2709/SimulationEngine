import re
from collections import Counter


WHITESPACE_RE = re.compile(r"\s+")
PRICE_RE = re.compile(r"(₹|\$|€|£)\s?\d+(?:[\.,]\d+)?|\d+\s?(?:per month|/month|monthly|annual|yearly)", re.IGNORECASE)


def normalize_text(value: str) -> str:
    return WHITESPACE_RE.sub(" ", value).strip()


def dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        normalized = normalize_text(value)
        if not normalized:
            continue
        lowered = normalized.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        deduped.append(normalized)
    return deduped


def truncate_text(value: str, max_chars: int) -> str:
    normalized = normalize_text(value)
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 3].rstrip() + "..."


def top_keywords(chunks: list[str], *, limit: int = 8) -> list[str]:
    tokens: list[str] = []
    for chunk in chunks:
        tokens.extend(re.findall(r"[A-Za-z][A-Za-z\-]{3,}", chunk.lower()))
    stopwords = {
        "with",
        "from",
        "that",
        "this",
        "your",
        "have",
        "more",
        "stream",
        "watch",
        "plan",
        "plans",
        "learn",
        "about",
        "home",
        "page",
        "pricing",
    }
    ranked = Counter(token for token in tokens if token not in stopwords)
    return [token.replace("-", " ") for token, _ in ranked.most_common(limit)]


def extract_price_signals(chunks: list[str]) -> list[str]:
    matches: list[str] = []
    for chunk in chunks:
        matches.extend(match.group(0) for match in PRICE_RE.finditer(chunk))
    return dedupe_preserve_order(matches)
