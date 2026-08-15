from topicguard.cannibalization import find_overlaps
from topicguard.crawler import PageRecord


def page(url, title, body, h1=None):
    return PageRecord(
        url=url,
        status_code=200,
        title=title,
        h1s=[h1] if h1 else [],
        text=body,
        word_count=len(body.split()),
    )


def test_near_duplicate_pages_score_high():
    pages = {
        "https://x.com/a": page(
            "https://x.com/a",
            "Best Running Shoes for Beginners",
            "Running shoes for beginners are lightweight and cushioned. "
            "The best running shoes offer good arch support for new runners.",
            h1="Best Running Shoes for Beginners",
        ),
        "https://x.com/b": page(
            "https://x.com/b",
            "Best Running Shoes for New Runners",
            "The best running shoes for new runners are lightweight with good cushioning "
            "and arch support for beginners.",
            h1="Best Running Shoes for New Runners",
        ),
    }
    pairs = find_overlaps(pages, threshold=0.3)
    assert len(pairs) == 1
    assert pairs[0].score > 0.3
    assert pairs[0].severity in {"low", "medium", "high"}
    assert len(pairs[0].shared_terms) > 0


def test_unrelated_pages_score_low_and_are_excluded():
    pages = {
        "https://x.com/a": page("https://x.com/a", "Running Shoes Guide", "Running shoes cushioning arch support."),
        "https://x.com/b": page("https://x.com/b", "Tax Filing Deadlines 2026", "File your taxes before the April deadline."),
    }
    pairs = find_overlaps(pages, threshold=0.4)
    assert pairs == []


def test_pages_with_errors_are_excluded_from_comparison():
    pages = {
        "https://x.com/a": page("https://x.com/a", "Shoes", "Running shoes are great."),
        "https://x.com/broken": PageRecord(url="https://x.com/broken", error="request_failed"),
    }
    pairs = find_overlaps(pages, threshold=0.1)
    assert pairs == []  # only one valid page, nothing to compare


def test_empty_page_set_returns_empty_list():
    assert find_overlaps({}, threshold=0.4) == []


def test_single_page_returns_no_pairs():
    pages = {"https://x.com/a": page("https://x.com/a", "Solo Page", "Just one page here with content.")}
    assert find_overlaps(pages, threshold=0.1) == []
