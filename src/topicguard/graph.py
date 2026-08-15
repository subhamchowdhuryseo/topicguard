"""Internal link graph analysis: orphan page detection and crawl-depth
(click distance from the homepage) computation.

Metric definitions
-------------------
inbound_links (int): count of distinct crawled pages that contain at least
    one <a href> pointing at this URL. This only counts links found DURING
    THIS CRAWL — it is not a full-site link audit if `max_pages` truncated
    the crawl before reaching every page.

is_orphan (bool): True if inbound_links == 0 AND the page is not the crawl's
    start URL. An orphan page found this way means "no other crawled page
    links to it," which is a strong technical-SEO signal but is NOT proof
    the page is unreachable site-wide (it could be linked from a page this
    crawl didn't visit, e.g. beyond max_pages).

click_depth (int | None): shortest number of link-hops from the homepage to
    this page, computed via breadth-first search over the crawled link
    graph. None if unreachable from the homepage within the crawled set.
"""

from __future__ import annotations

from collections import defaultdict, deque

from .crawler import PageRecord


def build_inbound_counts(pages: dict[str, PageRecord]) -> dict[str, int]:
    inbound: dict[str, int] = defaultdict(int)
    for record in pages.values():
        for target in set(record.outlinks):
            if target in pages:
                inbound[target] += 1
    return inbound


def compute_click_depth(pages: dict[str, PageRecord], start_url: str) -> dict[str, int | None]:
    depth: dict[str, int | None] = {url: None for url in pages}
    if start_url not in pages:
        return depth

    depth[start_url] = 0
    queue = deque([start_url])
    while queue:
        current = queue.popleft()
        current_depth = depth[current]
        for neighbor in pages[current].outlinks:
            if neighbor in pages and depth[neighbor] is None:
                depth[neighbor] = current_depth + 1
                queue.append(neighbor)
    return depth


def analyze_link_graph(pages: dict[str, PageRecord], start_url: str) -> dict[str, dict]:
    """Return per-URL graph metrics: inbound_links, is_orphan, click_depth."""
    inbound = build_inbound_counts(pages)
    depth = compute_click_depth(pages, start_url)

    results: dict[str, dict] = {}
    for url in pages:
        inbound_count = inbound.get(url, 0)
        results[url] = {
            "inbound_links": inbound_count,
            "is_orphan": inbound_count == 0 and url != start_url,
            "click_depth": depth.get(url),
        }
    return results
