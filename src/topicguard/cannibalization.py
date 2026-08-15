"""Content-overlap ("cannibalization risk") detection.

Custom heuristic — clearly labeled, not a proprietary Google metric.

Content Overlap Score (0.0-1.0)
--------------------------------
For every page, we build a TF-IDF vector over its title (weighted 3x), H1s
(weighted 2x), and body text (weighted 1x), using pure-Python term
frequency / inverse document frequency (no numpy/sklearn dependency — see
docs/METHODOLOGY.md for why). For every pair of pages, we compute the
cosine similarity between their TF-IDF vectors. That similarity IS the
Content Overlap Score.

What it measures: lexical/topical similarity between two pages' visible
content, based only on word usage. Two pages can score high because they
legitimately cover the same subject with different intents (not
necessarily a problem) or because they are near-duplicates (usually a
problem).

What it does NOT measure: actual Google Search Console ranking overlap,
search intent, or click-through competition. A high score is a signal to
investigate, not a verdict. If a `gsc_export.csv` is supplied (see
gsc_enrich.py), overlapping actual ranking queries are shown alongside this
score for a much stronger signal — that enrichment is optional.

Severity bands (heuristic, tune with --cannibalization-threshold):
  >= 0.75  "high"
  >= 0.55  "medium"
  >= threshold (default 0.4) "low"
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

from .crawler import PageRecord
from .utils import tokenize


@dataclass
class OverlapPair:
    url_a: str
    url_b: str
    score: float
    severity: str
    shared_terms: list[str]


def _weighted_tokens(record: PageRecord) -> list[str]:
    tokens: list[str] = []
    tokens += tokenize(record.title) * 3
    for h1 in record.h1s:
        tokens += tokenize(h1) * 2
    tokens += tokenize(record.meta_description) * 2
    tokens += tokenize(record.text)
    return tokens


def _build_tfidf(pages: dict[str, PageRecord]) -> dict[str, Counter]:
    """Return {url: Counter(term -> tfidf_weight)}."""
    doc_tokens: dict[str, list[str]] = {}
    for url, record in pages.items():
        if record.error or not record.text:
            continue
        doc_tokens[url] = _weighted_tokens(record)

    n_docs = len(doc_tokens)
    if n_docs == 0:
        return {}

    doc_freq: Counter = Counter()
    for tokens in doc_tokens.values():
        doc_freq.update(set(tokens))

    tfidf: dict[str, Counter] = {}
    for url, tokens in doc_tokens.items():
        term_count = Counter(tokens)
        total = sum(term_count.values()) or 1
        weights: Counter = Counter()
        for term, count in term_count.items():
            tf = count / total
            idf = math.log((n_docs + 1) / (doc_freq[term] + 1)) + 1  # smoothed idf
            weights[term] = tf * idf
        tfidf[url] = weights
    return tfidf


def _cosine_similarity(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    shared = set(a) & set(b)
    dot = sum(a[t] * b[t] for t in shared)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _severity(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.55:
        return "medium"
    return "low"


def find_overlaps(
    pages: dict[str, PageRecord],
    threshold: float = 0.4,
    top_shared_terms: int = 8,
) -> list[OverlapPair]:
    """Compare every crawled page pair and return those at/above `threshold`.

    O(n^2) in page count. Fine for the intended use case (a few hundred
    pages); documented as a scaling limitation for very large sites.
    """
    tfidf = _build_tfidf(pages)
    urls = sorted(tfidf.keys())
    pairs: list[OverlapPair] = []

    for i in range(len(urls)):
        for j in range(i + 1, len(urls)):
            url_a, url_b = urls[i], urls[j]
            vec_a, vec_b = tfidf[url_a], tfidf[url_b]
            score = _cosine_similarity(vec_a, vec_b)
            if score >= threshold:
                shared = sorted(
                    set(vec_a) & set(vec_b),
                    key=lambda t: vec_a[t] * vec_b[t],
                    reverse=True,
                )[:top_shared_terms]
                pairs.append(
                    OverlapPair(
                        url_a=url_a,
                        url_b=url_b,
                        score=round(score, 4),
                        severity=_severity(score),
                        shared_terms=shared,
                    )
                )

    pairs.sort(key=lambda p: p.score, reverse=True)
    return pairs
