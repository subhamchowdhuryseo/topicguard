"""TopicGuard command-line interface.

Examples
--------
    topicguard analyze https://example.com
    topicguard analyze https://example.com --max-pages 100 --output-dir out/
    topicguard analyze https://example.com --gsc-export queries.csv
"""

from __future__ import annotations

import argparse
import os
import sys

from . import __version__
from .cannibalization import find_overlaps
from .crawler import Crawler
from .decay import score_all
from .graph import analyze_link_graph
from .report import build_page_rows, write_html_report, write_json, write_overlaps_csv, write_pages_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="topicguard",
        description="Local SEO auditor: keyword cannibalization, orphan pages, and content decay — no paid APIs required.",
    )
    parser.add_argument("--version", action="version", version=f"topicguard {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Crawl a site and generate a report.")
    analyze.add_argument("url", help="Start URL, e.g. https://example.com")
    analyze.add_argument("--max-pages", type=int, default=200, help="Maximum pages to crawl (default: 200)")
    analyze.add_argument("--delay", type=float, default=0.3, help="Seconds to wait between requests (default: 0.3)")
    analyze.add_argument("--timeout", type=int, default=10, help="Per-request timeout in seconds (default: 10)")
    analyze.add_argument(
        "--ignore-robots",
        action="store_true",
        help="Do not respect robots.txt (use only on sites you own/have permission to crawl).",
    )
    analyze.add_argument(
        "--cannibalization-threshold",
        type=float,
        default=0.4,
        help="Minimum content-overlap cosine similarity to report a pair (0.0-1.0, default: 0.4)",
    )
    analyze.add_argument("--fresh-days", type=int, default=180, help="Days before a page is no longer 'fresh' (default: 180)")
    analyze.add_argument("--stale-days", type=int, default=730, help="Days after which a page is maximally 'stale' (default: 730)")
    analyze.add_argument("--thin-word-count", type=int, default=300, help="Word count below which a page is flagged thin (default: 300)")
    analyze.add_argument("--output-dir", default="topicguard-report", help="Directory to write reports to (default: topicguard-report)")
    analyze.add_argument("--gsc-export", default=None, help="Optional path to a Google Search Console Performance CSV export to enrich cannibalization pairs with real query overlap.")
    analyze.add_argument("--formats", default="csv,json,html", help="Comma-separated export formats: csv,json,html (default: all three)")

    return parser


def run_analyze(args: argparse.Namespace) -> int:
    formats = {f.strip().lower() for f in args.formats.split(",") if f.strip()}
    valid_formats = {"csv", "json", "html"}
    invalid = formats - valid_formats
    if invalid:
        print(f"Error: unknown format(s) {sorted(invalid)}. Choose from {sorted(valid_formats)}.", file=sys.stderr)
        return 2

    try:
        crawler = Crawler(
            start_url=args.url,
            max_pages=args.max_pages,
            delay=args.delay,
            respect_robots=not args.ignore_robots,
            timeout=args.timeout,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(f"Crawling {crawler.start_url} (max {args.max_pages} pages)...")
    pages = crawler.crawl()
    ok_pages = sum(1 for p in pages.values() if not p.error)
    print(f"Crawled {len(pages)} URLs ({ok_pages} fetched successfully).")

    if ok_pages == 0:
        print(
            "Error: no pages were fetched successfully. Check the URL, your network connection, "
            "or robots.txt rules (try --ignore-robots only if you have permission to crawl this site).",
            file=sys.stderr,
        )
        return 1

    print("Analyzing internal link graph...")
    graph_metrics = analyze_link_graph(pages, crawler.start_url)

    print("Scoring content decay risk...")
    decay_results = score_all(
        pages,
        fresh_days=args.fresh_days,
        stale_days=args.stale_days,
        thin_word_count=args.thin_word_count,
    )

    print(f"Detecting content overlap (threshold={args.cannibalization_threshold})...")
    pairs = find_overlaps(pages, threshold=args.cannibalization_threshold)

    if args.gsc_export:
        from .gsc_enrich import load_gsc_export, shared_queries_for_pair

        try:
            gsc_data = load_gsc_export(args.gsc_export)
            print(f"Loaded GSC export: {len(gsc_data)} pages with query data.")
            for pair in pairs:
                shared = shared_queries_for_pair(gsc_data, pair.url_a, pair.url_b)
                if shared:
                    top = ", ".join(s.query for s in shared[:5])
                    print(f"  [GSC] {pair.url_a} <-> {pair.url_b}: shared queries -> {top}")
        except (FileNotFoundError, ValueError) as exc:
            print(f"Warning: could not load --gsc-export ({exc}). Continuing without it.", file=sys.stderr)

    os.makedirs(args.output_dir, exist_ok=True)
    rows = build_page_rows(pages, graph_metrics, decay_results)

    if "csv" in formats:
        write_pages_csv(rows, os.path.join(args.output_dir, "pages.csv"))
        write_overlaps_csv(pairs, os.path.join(args.output_dir, "content_overlap.csv"))
    if "json" in formats:
        write_json(rows, pairs, os.path.join(args.output_dir, "report.json"), crawler.start_url)
    if "html" in formats:
        write_html_report(rows, pairs, os.path.join(args.output_dir, "report.html"), crawler.start_url)

    orphan_count = sum(1 for r in rows if r.get("is_orphan"))
    high_overlap = sum(1 for p in pairs if p.severity == "high")
    print("\nSummary")
    print("-------")
    print(f"Pages analyzed:         {len(rows)}")
    print(f"Orphan pages:            {orphan_count}")
    print(f"Content overlap pairs:   {len(pairs)} ({high_overlap} high severity)")
    print(f"Reports written to:      {os.path.abspath(args.output_dir)}/")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "analyze":
        return run_analyze(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
