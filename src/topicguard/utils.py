"""Small, dependency-free helper functions shared across TopicGuard modules."""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse, urlunparse

# A conservative English stopword list. Kept local (no NLTK/spaCy dependency)
# so the tool stays lightweight and works fully offline once pages are fetched.
STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an",
    "and", "any", "are", "aren't", "as", "at", "be", "because", "been",
    "before", "being", "below", "between", "both", "but", "by", "can",
    "cannot", "could", "did", "do", "does", "doing", "down", "during",
    "each", "few", "for", "from", "further", "had", "has", "have", "having",
    "he", "her", "here", "hers", "herself", "him", "himself", "his", "how",
    "i", "if", "in", "into", "is", "it", "its", "itself", "just", "me",
    "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off",
    "on", "once", "only", "or", "other", "our", "ours", "ourselves", "out",
    "over", "own", "same", "she", "should", "so", "some", "such", "than",
    "that", "the", "their", "theirs", "them", "themselves", "then", "there",
    "these", "they", "this", "those", "through", "to", "too", "under",
    "until", "up", "very", "was", "we", "were", "what", "when", "where",
    "which", "while", "who", "whom", "why", "will", "with", "you", "your",
    "yours", "yourself", "yourselves", "s", "t", "re", "ll", "ve", "don",
    "isn", "www", "com",
}

_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z'-]{1,}")


def tokenize(text: str) -> list[str]:
    """Lowercase, strip punctuation, and drop stopwords/short tokens.

    This is intentionally a simple regex tokenizer (not a full NLP
    pipeline). It is good enough for TF-IDF style comparison between pages
    on the same site but is NOT a substitute for real NLP keyword
    extraction. See docs/METHODOLOGY.md for limitations.
    """
    if not text:
        return []
    tokens = _TOKEN_RE.findall(text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 2]


def normalize_url(url: str, base: str | None = None) -> str:
    """Resolve relative URLs, strip fragments, and drop trailing slashes
    (except for the root path) so the same page isn't counted twice.
    """
    if base:
        url = urljoin(base, url)
    parsed = urlparse(url)
    path = parsed.path
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    normalized = urlunparse((parsed.scheme, parsed.netloc, path, "", parsed.query, ""))
    return normalized


def same_domain(url: str, root_netloc: str) -> bool:
    """Return True if `url` belongs to the same registrable host as the
    crawl's starting domain (simple netloc match, no PSL parsing)."""
    try:
        return urlparse(url).netloc == root_netloc
    except ValueError:
        return False


def truncate(text: str, length: int = 160) -> str:
    text = text or ""
    return text if len(text) <= length else text[: length - 1].rstrip() + "…"
