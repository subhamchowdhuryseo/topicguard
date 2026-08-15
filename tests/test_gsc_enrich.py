import csv

import pytest

from topicguard.gsc_enrich import load_gsc_export, shared_queries_for_pair


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_load_gsc_export_normal_case(tmp_path):
    path = tmp_path / "gsc.csv"
    write_csv(
        path,
        [
            {"query": "running shoes", "page": "https://x.com/a", "clicks": "10", "impressions": "100"},
            {"query": "best running shoes", "page": "https://x.com/b", "clicks": "5", "impressions": "50"},
        ],
        fieldnames=["query", "page", "clicks", "impressions"],
    )
    data = load_gsc_export(str(path))
    assert "https://x.com/a" in data
    assert data["https://x.com/a"]["running shoes"]["clicks"] == 10


def test_missing_required_column_raises_value_error(tmp_path):
    path = tmp_path / "bad.csv"
    write_csv(path, [{"query": "x", "clicks": "1"}], fieldnames=["query", "clicks"])
    with pytest.raises(ValueError):
        load_gsc_export(str(path))


def test_nonexistent_file_raises_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_gsc_export("/no/such/file.csv")


def test_shared_queries_for_pair_finds_overlap(tmp_path):
    path = tmp_path / "gsc.csv"
    write_csv(
        path,
        [
            {"query": "shoes", "page": "https://x.com/a", "clicks": "10", "impressions": "100"},
            {"query": "shoes", "page": "https://x.com/b", "clicks": "3", "impressions": "40"},
            {"query": "socks", "page": "https://x.com/a", "clicks": "1", "impressions": "10"},
        ],
        fieldnames=["query", "page", "clicks", "impressions"],
    )
    data = load_gsc_export(str(path))
    shared = shared_queries_for_pair(data, "https://x.com/a", "https://x.com/b")
    assert len(shared) == 1
    assert shared[0].query == "shoes"
    assert shared[0].clicks_a == 10
    assert shared[0].clicks_b == 3


def test_shared_queries_returns_empty_when_no_overlap(tmp_path):
    path = tmp_path / "gsc.csv"
    write_csv(
        path,
        [
            {"query": "shoes", "page": "https://x.com/a", "clicks": "10", "impressions": "100"},
            {"query": "socks", "page": "https://x.com/b", "clicks": "3", "impressions": "40"},
        ],
        fieldnames=["query", "page", "clicks", "impressions"],
    )
    data = load_gsc_export(str(path))
    assert shared_queries_for_pair(data, "https://x.com/a", "https://x.com/b") == []


def test_malformed_numeric_fields_default_to_zero(tmp_path):
    path = tmp_path / "gsc.csv"
    write_csv(
        path,
        [{"query": "shoes", "page": "https://x.com/a", "clicks": "N/A", "impressions": ""}],
        fieldnames=["query", "page", "clicks", "impressions"],
    )
    data = load_gsc_export(str(path))
    assert data["https://x.com/a"]["shoes"]["clicks"] == 0
    assert data["https://x.com/a"]["shoes"]["impressions"] == 0
