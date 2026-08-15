# Methodology & Limitations

TopicGuard makes three claims per page/pair, and this document explains
exactly how each is computed, what it assumes, and where it breaks down.
None of these are official Google metrics — all are clearly labeled custom
heuristics.

## 1. Content Overlap Score (cannibalization risk)

**What it is:** cosine similarity between two pages' TF-IDF vectors, built
from title (weighted ×3), H1s (×2), meta description (×2), and body text
(×1), using a pure-Python term-frequency / inverse-document-frequency
implementation (no numpy/sklearn — see "Why no ML libraries" below).

**Formula:** for pages A and B with term-weight vectors `Va`, `Vb`:

```
score = (Va · Vb) / (||Va|| * ||Vb||)
```

**Severity bands:** ≥0.75 high, ≥0.55 medium, otherwise low (only pairs at
or above `--cannibalization-threshold`, default 0.4, are reported at all).

**Assumptions:**
- Pages that legitimately cover the same subject (e.g., a pillar page and
  a supporting article) will score high even if that overlap is
  intentional and healthy. A high score is a prompt to investigate, not a
  verdict.
- Boilerplate (nav, footer) is not stripped before comparison. Sites with
  heavy boilerplate relative to unique content will see inflated scores
  across unrelated pages. If your results look noisy, that's usually why.

**Limitations:**
- This measures **lexical similarity**, not actual Google Search Console
  ranking overlap. Two pages can use different words for the same query
  intent (real cannibalization) and score low here. Conversely, two pages
  can share vocabulary without ever competing in search (false positive).
- O(n²) comparison cost — every page is compared to every other page. Fine
  for a few hundred pages; will get slow well before it gets wrong on
  very large sites (tens of thousands of pages).
- **Use `--gsc-export` to cross-reference actual overlapping ranking
  queries** (from a Search Console CSV export) whenever you have it. That
  signal is far stronger than lexical similarity alone.

## 2. Orphan Pages & Click Depth

**Inbound links:** count of distinct pages, *within this crawl*, that
contain an `<a href>` pointing at a given URL.

**Orphan:** `inbound_links == 0` and the URL isn't the crawl's start URL.

**Click depth:** shortest path (in link hops) from the homepage to a page,
computed via breadth-first search over the crawled link graph.

**Critical limitation:** these metrics are bounded by what was actually
crawled. If `--max-pages` truncated the crawl before every page was
visited, a page might show as "orphan" here simply because the page that
links to it wasn't reached yet — not because it's genuinely unlinked
site-wide. Increase `--max-pages` (or point at a sitemap-derived seed
list) for a more complete picture on large sites.

## 3. Content Decay Risk Score (0–100)

Combines two locally-available signals:

- **Staleness (0–70 pts):** derived from the HTTP `Last-Modified` response
  header. Linear scale: 0 pts at `--fresh-days` (default 180) or newer, 70
  pts at `--stale-days` (default 730) or older.
- **Thin content (0–30 pts):** flat 30 pts if word count is below
  `--thin-word-count` (default 300).

**Critical limitation:** many servers (especially anything behind a CDN or
a JS framework doing client-side rendering) never send `Last-Modified`. In
that case the staleness component scores 0 — **not** penalized — and
`decay_last_modified_known=False` is reported so you can tell "confirmed
fresh" apart from "unknown." This score is a triage aid for deciding what
to manually review, not a measurement of actual traffic decline. Real
decay requires Google Search Console or Analytics click-trend data, which
this tool does not fetch.

## Why no ML libraries (numpy/scikit-learn)?

TF-IDF and cosine similarity are implemented in ~60 lines of pure Python
(`cannibalization.py`) instead of pulling in scikit-learn or numpy. This
keeps the entire tool to two runtime dependencies (`requests`,
`beautifulsoup4`), which means `pip install -r requirements.txt` finishes
in seconds on any platform, with no compiled-wheel headaches on Windows
or ARM. The trade-off is documented, not hidden: pure-Python TF-IDF will
be slower than a vectorized numpy implementation on very large corpora.

## Why no headless browser (Playwright/Selenium)?

JavaScript-rendered content is invisible to this crawler — it only sees
server-rendered HTML. This is a real limitation for JS-heavy sites (many
SPA/React storefronts). It was a deliberate choice: adding Playwright
means shipping/downloading a full browser binary, which breaks the
"install and run in under a minute" goal for most users. If your site is
JS-rendered, TopicGuard will under-report content and links. See the
roadmap in the README for planned optional Playwright support.

## Why robots.txt matters here

By default, TopicGuard reads and obeys `robots.txt` disallow rules before
fetching any URL. `--ignore-robots` exists for auditing sites you own or
have explicit permission to crawl — using it against third-party sites
without permission is on you, not the tool.
