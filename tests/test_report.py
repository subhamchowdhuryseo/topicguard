import json

from topicguard.cannibalization import OverlapPair
from topicguard.crawler import PageRecord
from topicguard.decay import DecayResult
from topicguard.graph import analyze_link_graph
from topicguard.report import (
    build_page_rows,
    write_html_report,
    write_json,
    write_overlaps_csv,
    write_pages_csv,
)


def sample_pages():
    return {
        "https://x.com/": PageRecord(
            url="https://x.com/", status_code=200, title="Home", word_count=500, outlinks=["https://x.com/a"]
        ),
        "https://x.com/a": PageRecord(url="https://x.com/a", status_code=200, title="Page A", word_count=200),
    }


def test_build_page_rows_includes_all_expected_fields():
    pages = sample_pages()
    graph = analyze_link_graph(pages, "https://x.com/")
    decay = {u: DecayResult(url=u, last_modified_known=False, days_since_modified=None, word_count=p.word_count, is_thin=False, decay_score=0) for u, p in pages.items()}
    rows = build_page_rows(pages, graph, decay)
    assert len(rows) == 2
    assert {"url", "status_code", "title", "is_orphan", "decay_score"}.issubset(rows[0].keys())


def test_write_pages_csv_handles_empty_rows(tmp_path):
    path = tmp_path / "pages.csv"
    write_pages_csv([], str(path))
    assert path.exists()
    assert path.read_text() == ""


def test_write_pages_csv_normal_case(tmp_path):
    pages = sample_pages()
    graph = analyze_link_graph(pages, "https://x.com/")
    decay = {u: DecayResult(url=u, last_modified_known=False, days_since_modified=None, word_count=p.word_count, is_thin=False, decay_score=0) for u, p in pages.items()}
    rows = build_page_rows(pages, graph, decay)
    path = tmp_path / "pages.csv"
    write_pages_csv(rows, str(path))
    content = path.read_text()
    assert "https://x.com/" in content
    assert "url" in content.splitlines()[0]


def test_write_overlaps_csv(tmp_path):
    pairs = [OverlapPair(url_a="https://x.com/a", url_b="https://x.com/b", score=0.8, severity="high", shared_terms=["shoes", "running"])]
    path = tmp_path / "overlap.csv"
    write_overlaps_csv(pairs, str(path))
    content = path.read_text()
    assert "shoes, running" in content or "shoes" in content


def test_write_json_produces_valid_json(tmp_path):
    rows = [{"url": "https://x.com/", "status_code": 200}]
    pairs = [OverlapPair(url_a="https://x.com/a", url_b="https://x.com/b", score=0.5, severity="medium", shared_terms=["a"])]
    path = tmp_path / "report.json"
    write_json(rows, pairs, str(path), "https://x.com/")
    data = json.loads(path.read_text())
    assert data["tool"] == "TopicGuard"
    assert data["start_url"] == "https://x.com/"
    assert len(data["pages"]) == 1
    assert len(data["content_overlap_pairs"]) == 1


def test_write_html_report_escapes_content_and_includes_sections(tmp_path):
    rows = [{"url": "https://x.com/<script>", "status_code": 200, "is_orphan": True, "decay_score": 60, "title": "T", "word_count": 10, "click_depth": 1, "inbound_links": 0, "decay_last_modified_known": True, "decay_days_since_modified": 900, "decay_is_thin": True}]
    pairs = []
    path = tmp_path / "report.html"
    write_html_report(rows, pairs, str(path), "https://x.com/")
    html = path.read_text()
    assert "<script>" not in html  # must be escaped
    assert "Orphan Pages" in html
    assert "Content Decay Risk" in html
