# TopicGuard

**Find keyword cannibalization, orphan pages, and content decay in one local crawl — no paid APIs required.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-36%20passing-brightgreen.svg)](tests/)
[![Dependencies: 2](https://img.shields.io/badge/dependencies-2-blue.svg)](requirements.txt)

<!-- Screenshot: HTML report overview (summary stat cards + overlap table) -->
<!-- ![TopicGuard HTML report](assets/screenshot-report-overview.png) -->

## Why this exists

Every open-source keyword-cannibalization script that exists today requires
a live Google Search Console connection to work at all — no GSC account, no
output. Orphan-page and internal-link analysis mostly live as one feature
buried inside paid platforms like Ahrefs or Semrush. Content decay is
barely tooled at all; it's a blog-post concept, not something you can run.

TopicGuard crawls your site once and gives you all three, using only
signals available from the HTML and HTTP headers themselves — no API key,
no login, no monthly bill. If you *do* have a Search Console export, you
can optionally feed it in to cross-reference real overlapping ranking
queries — that's an enhancement, not a requirement.

## Key features

- 🕷️ **Local crawler** — breadth-first, robots.txt-respecting, same-domain scoped. Two dependencies (`requests`, `beautifulsoup4`).
- 🥊 **Keyword cannibalization detection** — TF-IDF cosine similarity across title/H1/meta/body flags pages likely competing for the same topic, with shared-term explanations and a severity rating.
- 🕳️ **Orphan page & click-depth analysis** — builds an internal link graph from the crawl to find pages nothing links to, and how many clicks deep every page sits from the homepage.
- 📉 **Content decay risk score** — combines HTTP `Last-Modified` staleness with thin-content word-count flags to triage what needs a refresh.
- 📊 **Optional GSC enrichment** — point it at a Search Console CSV export and cannibalization pairs get annotated with real shared ranking queries, clicks, and impressions. No API/OAuth setup needed.
- 📁 **CSV / JSON / HTML export** — pipe into a spreadsheet, another script, or open a self-contained HTML report directly.
- 🐍 **Every heuristic documented** — see [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) for the exact formula, assumptions, and limitations behind every score. No invented "authority" metrics.

## Installation

Requires Python 3.10+.

```bash
git clone https://github.com/subham-seo/topicguard.git
cd topicguard
pip install -r requirements.txt
```

Or install as a CLI command:

```bash
pip install -e .
```

## Usage

```bash
topicguard analyze https://example.com
```

That's it — crawls up to 200 pages by default and writes `pages.csv`,
`content_overlap.csv`, `report.json`, and `report.html` to
`./topicguard-report/`.

### More examples

```bash
# Crawl more pages, slower (be a good citizen)
topicguard analyze https://example.com --max-pages 500 --delay 0.5

# Only export JSON
topicguard analyze https://example.com --formats json

# Lower the cannibalization sensitivity threshold (default 0.4, 0.0-1.0)
topicguard analyze https://example.com --cannibalization-threshold 0.3

# Enrich cannibalization pairs with real Search Console query overlap
topicguard analyze https://example.com --gsc-export queries.csv

# Custom output location
topicguard analyze https://example.com --output-dir reports/2026-08-audit
```

Run `topicguard analyze --help` for the full flag list (decay thresholds,
timeout, robots.txt override, etc.).

### Without installing

```bash
PYTHONPATH=src python -m topicguard.cli analyze https://example.com
```

## Try it on the included demo

No live site needed — `examples/sample-report/` contains real output from
a demo run (three pages, two of which deliberately overlap on "running
shoes" content) so you can see exactly what the tool produces before
running it yourself. Open `examples/sample-report/report.html` in a
browser.

`examples/sample_gsc_export.csv` is a matching demo Search Console export
you can point `--gsc-export` at to see the query-overlap enrichment in
action.

## Sample output

`content_overlap.csv`:

| url_a | url_b | score | severity | shared_terms |
|---|---|---|---|---|
| /best-running-shoes | /running-shoes-for-beginners | 0.73 | medium | running, shoes, beginners, cushioning, support |

`pages.csv` (columns trimmed for display):

| url | status_code | inbound_links | is_orphan | decay_score |
|---|---|---|---|---|
| / | 200 | 2 | False | 0 |
| /best-running-shoes | 200 | 1 | False | 0 |
| /clearance-old-page | 200 | 0 | **True** | 62 |

## Methodology & limitations

Every score in this tool is a **documented custom heuristic**, not a
proprietary Google metric. Before you trust (or argue with) a result,
read [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) — it explains exactly
what's measured, the formula, and where each metric breaks down (e.g.
orphan detection is bounded by `--max-pages`, decay scoring can't see
real traffic without a GSC export, JS-rendered sites are under-crawled
since there's no headless browser).

## Roadmap

**Shipped in v1.0 (MVP):**
- Local crawler, cannibalization detection, orphan/click-depth analysis, content decay scoring, optional GSC CSV enrichment, CSV/JSON/HTML export.

**Planned:**
- Sitemap.xml-based seeding (crawl exactly the URLs Google is told about)
- Optional headless-browser mode for JS-rendered sites
- Redirect chain detection during crawl
- Historical diffing (compare two runs to see what changed)
- Config file support (`.topicguard.yml`) instead of long CLI flags
- Simple local web dashboard (Flask) as an alternative to the static HTML report

See [open issues](https://github.com/subham-seo/topicguard/issues) for
the current list, or the "first issues" suggestions below if you want to
contribute.

## Contributing

Contributions welcome — see [`CONTRIBUTING.md`](CONTRIBUTING.md) for setup,
test instructions, and PR guidelines. Please read
[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) too.

## Tests

```bash
pip install -e ".[dev]"
pytest
```

36 tests, mocked HTTP throughout (no live network calls in the suite).

## License

MIT — see [`LICENSE`](LICENSE).

## Author

Created and maintained by Subham, an SEO specialist at
[SEO by Subham](https://seobysubham.com/).

For more practical SEO resources, link-building insights, and SEO guides,
visit [SEO by Subham](https://seobysubham.com/).
