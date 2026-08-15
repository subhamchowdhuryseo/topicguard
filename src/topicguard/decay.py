"""Content decay heuristic.

Decay Risk Score (custom heuristic, 0-100, higher = more risk)
-----------------------------------------------------------------
Combines two signals available WITHOUT any paid API:

1. Staleness (0-70 pts): derived from the HTTP `Last-Modified` response
   header when the server provides one. Linearly scaled: 0 pts at
   `fresh_days` old or newer, 70 pts at `stale_days` old or older.
   IMPORTANT LIMITATION: many servers do not send `Last-Modified` for
   dynamically rendered pages. When absent, this component is scored 0
   (not penalized) and `last_modified_known=False` is reported so you can
   tell the difference between "confirmed fresh" and "unknown."

2. Thin content flag (0-30 pts): pages under `thin_word_count` words get
   30 pts, a common — though debatable — proxy for under-developed content.

This score is a triage aid to help you decide which pages deserve a manual
content-refresh review. It is NOT a measurement of actual organic traffic
decline, which requires Google Search Console or Analytics data. If you
provide `--gsc-export`, cross-reference real click trends there instead of
relying on this heuristic alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from .crawler import PageRecord


@dataclass
class DecayResult:
    url: str
    last_modified_known: bool
    days_since_modified: int | None
    word_count: int
    is_thin: bool
    decay_score: int  # 0-100


def _parse_http_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (TypeError, ValueError):
        return None


def score_decay(
    record: PageRecord,
    fresh_days: int = 180,
    stale_days: int = 730,
    thin_word_count: int = 300,
    now: datetime | None = None,
) -> DecayResult:
    now = now or datetime.now(timezone.utc)
    modified_dt = _parse_http_date(record.last_modified)

    days_since: int | None = None
    staleness_points = 0.0
    known = modified_dt is not None

    if modified_dt is not None:
        days_since = (now - modified_dt).days
        if days_since <= fresh_days:
            staleness_points = 0.0
        elif days_since >= stale_days:
            staleness_points = 70.0
        else:
            span = max(1, stale_days - fresh_days)
            staleness_points = 70.0 * (days_since - fresh_days) / span

    is_thin = record.word_count > 0 and record.word_count < thin_word_count
    thin_points = 30.0 if is_thin else 0.0

    total = int(round(staleness_points + thin_points))
    return DecayResult(
        url=record.url,
        last_modified_known=known,
        days_since_modified=days_since,
        word_count=record.word_count,
        is_thin=is_thin,
        decay_score=min(100, total),
    )


def score_all(
    pages: dict[str, PageRecord],
    fresh_days: int = 180,
    stale_days: int = 730,
    thin_word_count: int = 300,
) -> dict[str, DecayResult]:
    now = datetime.now(timezone.utc)
    return {
        url: score_decay(record, fresh_days, stale_days, thin_word_count, now)
        for url, record in pages.items()
        if not record.error
    }
