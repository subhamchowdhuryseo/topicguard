from datetime import datetime, timedelta, timezone

from topicguard.crawler import PageRecord
from topicguard.decay import score_all, score_decay


def http_date(dt: datetime) -> str:
    return dt.strftime("%a, %d %b %Y %H:%M:%S GMT")


def test_fresh_page_scores_zero_staleness():
    now = datetime(2026, 8, 15, tzinfo=timezone.utc)
    record = PageRecord(
        url="https://x.com/",
        last_modified=http_date(now - timedelta(days=10)),
        word_count=1000,
    )
    result = score_decay(record, now=now)
    assert result.last_modified_known is True
    assert result.decay_score == 0


def test_stale_and_thin_page_scores_near_max():
    now = datetime(2026, 8, 15, tzinfo=timezone.utc)
    record = PageRecord(
        url="https://x.com/old",
        last_modified=http_date(now - timedelta(days=1000)),
        word_count=100,
    )
    result = score_decay(record, now=now)
    assert result.is_thin is True
    assert result.decay_score == 100  # 70 (max staleness) + 30 (thin)


def test_missing_last_modified_is_not_penalized_but_flagged_unknown():
    record = PageRecord(url="https://x.com/nodate", last_modified=None, word_count=1000)
    result = score_decay(record)
    assert result.last_modified_known is False
    assert result.days_since_modified is None
    assert result.decay_score == 0  # staleness component not penalized when unknown


def test_malformed_last_modified_header_handled_gracefully():
    record = PageRecord(url="https://x.com/bad", last_modified="not-a-date", word_count=500)
    result = score_decay(record)
    assert result.last_modified_known is False
    assert result.decay_score == 0


def test_zero_word_count_is_not_flagged_thin():
    # word_count of 0 usually means the page failed to parse, not that it's thin content
    record = PageRecord(url="https://x.com/empty", word_count=0)
    result = score_decay(record)
    assert result.is_thin is False


def test_score_all_skips_pages_with_errors():
    pages = {
        "https://x.com/ok": PageRecord(url="https://x.com/ok", word_count=1000),
        "https://x.com/broken": PageRecord(url="https://x.com/broken", error="request_failed"),
    }
    results = score_all(pages)
    assert "https://x.com/ok" in results
    assert "https://x.com/broken" not in results
