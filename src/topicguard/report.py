"""Export crawl + analysis results to CSV, JSON, and a self-contained HTML
report (no external template engine — plain string formatting keeps the
dependency list at two packages: requests, beautifulsoup4).
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from datetime import datetime, timezone
from html import escape

from .cannibalization import OverlapPair
from .crawler import PageRecord
from .decay import DecayResult


def build_page_rows(
    pages: dict[str, PageRecord],
    graph_metrics: dict[str, dict],
    decay_results: dict[str, DecayResult],
) -> list[dict]:
    rows = []
    for url, record in sorted(pages.items()):
        g = graph_metrics.get(url, {})
        d = decay_results.get(url)
        rows.append(
            {
                "url": url,
                "status_code": record.status_code,
                "error": record.error or "",
                "title": record.title,
                "title_length": len(record.title),
                "meta_description": record.meta_description,
                "h1_count": len(record.h1s),
                "word_count": record.word_count,
                "canonical": record.canonical or "",
                "noindex": record.noindex,
                "inbound_links": g.get("inbound_links"),
                "is_orphan": g.get("is_orphan"),
                "click_depth": g.get("click_depth"),
                "decay_score": d.decay_score if d else None,
                "decay_last_modified_known": d.last_modified_known if d else None,
                "decay_days_since_modified": d.days_since_modified if d else None,
                "decay_is_thin": d.is_thin if d else None,
            }
        )
    return rows


def write_pages_csv(rows: list[dict], path: str) -> None:
    if not rows:
        with open(path, "w", newline="", encoding="utf-8") as fh:
            fh.write("")
        return
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_overlaps_csv(pairs: list[OverlapPair], path: str) -> None:
    fieldnames = ["url_a", "url_b", "score", "severity", "shared_terms"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for p in pairs:
            row = asdict(p)
            row["shared_terms"] = ", ".join(p.shared_terms)
            writer.writerow(row)


def write_json(
    rows: list[dict],
    pairs: list[OverlapPair],
    path: str,
    start_url: str,
) -> None:
    payload = {
        "tool": "TopicGuard",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "start_url": start_url,
        "pages": rows,
        "content_overlap_pairs": [
            {**asdict(p)} for p in pairs
        ],
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)


def write_html_report(
    rows: list[dict],
    pairs: list[OverlapPair],
    path: str,
    start_url: str,
) -> None:
    orphan_rows = [r for r in rows if r.get("is_orphan")]
    thin_or_stale_rows = sorted(
        [r for r in rows if (r.get("decay_score") or 0) >= 40],
        key=lambda r: r.get("decay_score") or 0,
        reverse=True,
    )

    def page_table(cols: list[str], data: list[dict]) -> str:
        head = "".join(f"<th>{escape(c)}</th>" for c in cols)
        body_rows = []
        for r in data:
            cells = "".join(f"<td>{escape(str(r.get(c, '')))}</td>" for c in cols)
            body_rows.append(f"<tr>{cells}</tr>")
        return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"

    overlap_rows_html = "".join(
        f"<tr><td>{escape(p.url_a)}</td><td>{escape(p.url_b)}</td>"
        f"<td class='sev-{p.severity}'>{p.severity}</td><td>{p.score:.2f}</td>"
        f"<td>{escape(', '.join(p.shared_terms))}</td></tr>"
        for p in pairs
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>TopicGuard SEO Report — {escape(start_url)}</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 2rem; color: #1a1a1a; background:#fafafa; }}
  h1 {{ font-size: 1.5rem; }}
  h2 {{ margin-top: 2.5rem; border-bottom: 2px solid #eee; padding-bottom: .4rem;}}
  table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; font-size: .85rem; background: #fff;}}
  th, td {{ border: 1px solid #ddd; padding: 6px 10px; text-align: left; word-break: break-word;}}
  th {{ background: #f0f0f0; position: sticky; top:0;}}
  tr:nth-child(even) {{ background: #fafafa; }}
  .sev-high {{ color: #b00020; font-weight: 600; }}
  .sev-medium {{ color: #b06a00; font-weight: 600; }}
  .sev-low {{ color: #6a6a6a; }}
  .summary {{ display:flex; gap:1.5rem; flex-wrap:wrap; margin-top:1rem;}}
  .stat {{ background:#fff; border:1px solid #ddd; border-radius:8px; padding:1rem 1.5rem; min-width:140px;}}
  .stat b {{ display:block; font-size:1.6rem; }}
  footer {{ margin-top:3rem; color:#888; font-size:.8rem; }}
</style>
</head>
<body>
<h1>TopicGuard SEO Report</h1>
<p>Site: <strong>{escape(start_url)}</strong> &middot; Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</p>

<div class="summary">
  <div class="stat"><b>{len(rows)}</b>Pages crawled</div>
  <div class="stat"><b>{len(orphan_rows)}</b>Orphan pages</div>
  <div class="stat"><b>{len(pairs)}</b>Content overlap pairs</div>
  <div class="stat"><b>{len(thin_or_stale_rows)}</b>Decay-risk pages (score &ge; 40)</div>
</div>

<h2>Content Overlap / Cannibalization Risk</h2>
<p>Custom heuristic (TF-IDF cosine similarity of title/H1/meta/body). See docs/METHODOLOGY.md. High &ge; 0.75, medium &ge; 0.55.</p>
<table><thead><tr><th>Page A</th><th>Page B</th><th>Severity</th><th>Score</th><th>Shared terms</th></tr></thead>
<tbody>{overlap_rows_html or '<tr><td colspan="5">No overlaps found at the configured threshold.</td></tr>'}</tbody></table>

<h2>Orphan Pages ({len(orphan_rows)})</h2>
<p>No crawled page links internally to these URLs. See docs/METHODOLOGY.md for what "orphan" means in a bounded crawl.</p>
{page_table(['url','status_code','click_depth','word_count'], orphan_rows) if orphan_rows else '<p>None found.</p>'}

<h2>Content Decay Risk (score &ge; 40)</h2>
<p>Custom heuristic combining HTTP Last-Modified staleness and thin-content word count. Not a substitute for real traffic data.</p>
{page_table(['url','decay_score','decay_last_modified_known','decay_days_since_modified','decay_is_thin','word_count'], thin_or_stale_rows) if thin_or_stale_rows else '<p>None found.</p>'}

<h2>All Crawled Pages</h2>
{page_table(['url','status_code','title','word_count','inbound_links','click_depth','decay_score'], rows)}

<footer>
  Generated by <strong>TopicGuard</strong> — an open-source, local-first SEO auditor.
  Created and maintained by Subham, an SEO specialist at
  <a href="https://seobysubham.com/">SEO by Subham</a>.
</footer>
</body>
</html>"""

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)
