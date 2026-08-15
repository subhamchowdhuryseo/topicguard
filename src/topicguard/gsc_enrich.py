"""Optional enrichment: cross-reference cannibalization pairs against a
Google Search Console *Performance* export (CSV downloaded manually from
the GSC UI: Performance > Export > CSV, with "Queries" and "Pages" both
selected, or a "Pages x Queries" table export).

This module does NOT call any Google API and needs no credentials — it
only reads a CSV file you already have. That keeps the core tool's
promise ("no paid APIs required") intact while still letting you plug in
real ranking-query overlap when you have Search Console access.

Expected CSV columns (case-insensitive, flexible order):
    query, page, clicks, impressions, ctr, position

If your export uses different header names, rename the columns before
importing, or pass --gsc-query-col / --gsc-page-col to override.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass

from .utils import normalize_url


@dataclass
class SharedQuery:
    query: str
    clicks_a: int
    clicks_b: int
    impressions_a: int
    impressions_b: int


def load_gsc_export(
    path: str,
    query_col: str = "query",
    page_col: str = "page",
    clicks_col: str = "clicks",
    impressions_col: str = "impressions",
) -> dict[str, dict[str, dict]]:
    """Return {normalized_page_url: {query: {"clicks": int, "impressions": int}}}."""
    data: dict[str, dict[str, dict]] = defaultdict(dict)

    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise ValueError(f"'{path}' has no header row / is empty")

        lower_map = {name.lower().strip(): name for name in reader.fieldnames}
        required = [query_col, page_col]
        missing = [c for c in required if c.lower() not in lower_map]
        if missing:
            raise ValueError(
                f"GSC export is missing required column(s): {missing}. "
                f"Found columns: {reader.fieldnames}"
            )

        q_key = lower_map[query_col.lower()]
        p_key = lower_map[page_col.lower()]
        c_key = lower_map.get(clicks_col.lower())
        i_key = lower_map.get(impressions_col.lower())

        for row in reader:
            page = normalize_url(row[p_key])
            query = row[q_key].strip()
            if not query:
                continue
            clicks = _safe_int(row.get(c_key)) if c_key else 0
            impressions = _safe_int(row.get(i_key)) if i_key else 0
            data[page][query] = {"clicks": clicks, "impressions": impressions}

    return data


def _safe_int(value) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def shared_queries_for_pair(
    gsc_data: dict[str, dict[str, dict]], url_a: str, url_b: str
) -> list[SharedQuery]:
    queries_a = gsc_data.get(url_a, {})
    queries_b = gsc_data.get(url_b, {})
    shared = set(queries_a) & set(queries_b)

    results = [
        SharedQuery(
            query=q,
            clicks_a=queries_a[q]["clicks"],
            clicks_b=queries_b[q]["clicks"],
            impressions_a=queries_a[q]["impressions"],
            impressions_b=queries_b[q]["impressions"],
        )
        for q in shared
    ]
    results.sort(key=lambda s: s.impressions_a + s.impressions_b, reverse=True)
    return results
