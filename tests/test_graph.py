from topicguard.crawler import PageRecord
from topicguard.graph import analyze_link_graph


def test_orphan_page_detected_when_no_inbound_links():
    pages = {
        "https://x.com/": PageRecord(url="https://x.com/", outlinks=["https://x.com/about"]),
        "https://x.com/about": PageRecord(url="https://x.com/about", outlinks=[]),
        "https://x.com/secret": PageRecord(url="https://x.com/secret", outlinks=[]),  # nothing links to it
    }
    result = analyze_link_graph(pages, "https://x.com/")
    assert result["https://x.com/secret"]["is_orphan"] is True
    assert result["https://x.com/about"]["is_orphan"] is False
    assert result["https://x.com/"]["is_orphan"] is False  # homepage is never orphan


def test_click_depth_computed_via_bfs():
    pages = {
        "https://x.com/": PageRecord(url="https://x.com/", outlinks=["https://x.com/a"]),
        "https://x.com/a": PageRecord(url="https://x.com/a", outlinks=["https://x.com/b"]),
        "https://x.com/b": PageRecord(url="https://x.com/b", outlinks=[]),
    }
    result = analyze_link_graph(pages, "https://x.com/")
    assert result["https://x.com/"]["click_depth"] == 0
    assert result["https://x.com/a"]["click_depth"] == 1
    assert result["https://x.com/b"]["click_depth"] == 2


def test_unreachable_page_has_none_click_depth():
    pages = {
        "https://x.com/": PageRecord(url="https://x.com/", outlinks=[]),
        "https://x.com/isolated": PageRecord(url="https://x.com/isolated", outlinks=[]),
    }
    result = analyze_link_graph(pages, "https://x.com/")
    assert result["https://x.com/isolated"]["click_depth"] is None


def test_inbound_links_counts_multiple_referrers():
    pages = {
        "https://x.com/": PageRecord(url="https://x.com/", outlinks=["https://x.com/popular"]),
        "https://x.com/a": PageRecord(url="https://x.com/a", outlinks=["https://x.com/popular"]),
        "https://x.com/popular": PageRecord(url="https://x.com/popular", outlinks=[]),
    }
    result = analyze_link_graph(pages, "https://x.com/")
    assert result["https://x.com/popular"]["inbound_links"] == 2


def test_empty_page_set_returns_empty_dict():
    assert analyze_link_graph({}, "https://x.com/") == {}


def test_start_url_missing_from_pages_does_not_crash():
    pages = {"https://x.com/a": PageRecord(url="https://x.com/a", outlinks=[])}
    result = analyze_link_graph(pages, "https://x.com/")  # start_url not crawled
    assert result["https://x.com/a"]["click_depth"] is None
