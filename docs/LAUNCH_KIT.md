# TopicGuard — GitHub Launch Kit

Everything here is for *you* to paste into GitHub settings or your profile
— none of it ships inside the installed package.

---

## 1. GitHub profile README section

Paste into your `subham-seo/subham-seo` profile README:

```markdown
## Hi, I'm Subham 👋

I work in technical SEO — link building, backlinks, crawlability, and
turning repetitive SEO workflows into automation instead of spreadsheets.

🛠️ I build open-source SEO tools, starting with **TopicGuard** — a local,
API-free auditor for keyword cannibalization, orphan pages, and content
decay.

🌐 Website: [SEO by Subham](https://seobysubham.com/)
📦 Latest project: [TopicGuard](https://github.com/subham-seo/topicguard)
```

## 2. Repository "About" section

**Description** (350 char limit, this is ~140):
> Local, no-paid-API SEO auditor: keyword cannibalization, orphan pages, and content decay in one crawl. CSV/JSON/HTML export.

**Website field:** `https://seobysubham.com/`

**Topics** (GitHub allows up to 20 — these are the relevant ones, not a generic dump):
```
seo, technical-seo, seo-tools, seo-audit, python, open-source,
web-crawler, keyword-research, internal-linking, content-strategy,
seo-automation, cli-tool
```

## 3. Screenshots to add to `assets/` and embed in the README

1. **`screenshot-report-overview.png`** — the top of `report.html`: the four summary stat cards (pages crawled, orphan count, overlap pairs, decay-risk count). This is the single most important image — it's what people see first.
2. **`screenshot-cli-run.png`** — terminal output of `topicguard analyze https://example.com` mid-run, showing the step-by-step progress lines (crawling → link graph → decay → overlap → summary).
3. **`screenshot-overlap-table.png`** — the Content Overlap table in the HTML report, showing severity color-coding (red=high, orange=medium).
4. **`screenshot-orphan-table.png`** — the Orphan Pages section.
5. *(optional)* **`demo.gif`** — a ~15 second terminal recording (use `asciinema` + `agg`, or `terminalizer`) of a full `analyze` run from command to opening `report.html`.

To generate #1, #3, #4: run `topicguard analyze` against the included demo
server or any real site, open `report.html`, and screenshot each section.
To generate #2: run the CLI in a clean terminal and screenshot the output.

## 4. GitHub social preview image (1280×640px)

Go to repo **Settings → Social preview → Edit** and upload an image sized
1280×640px. Prompt for an AI image tool or a quick Figma/Canva template:

> A modern, minimal tech-product social card, 1280x640px, dark navy
> background (#0f1420), the text "TopicGuard" in a bold clean sans-serif
> (white), subtitle below in smaller light-gray text: "Local SEO auditor:
> cannibalization · orphan pages · content decay". Include a subtle
> abstract graph/network-node illustration (representing a site's internal
> link graph) in teal/cyan accent color on the right side. No stock photos,
> no faces, no clutter — flat, developer-tool aesthetic similar to a
> GitHub trending open-source project card. Leave breathing room; avoid
> placing text near the very edges since GitHub crops slightly.

## 5. Launch checklist

- [ ] Repo name: `topicguard` (lowercase, matches package name and CLI command)
- [ ] Set description + website + topics (section 2 above)
- [ ] Push code, confirm `pytest` passes in a fresh clone + fresh venv
- [ ] Add the 4-5 screenshots to `assets/`, uncomment the image line in `README.md`
- [ ] Upload the 1280×640 social preview image (section 4)
- [ ] Tag first release: `v1.0.0`, semantic versioning from here (MAJOR.MINOR.PATCH — breaking CLI flag changes bump MAJOR)
- [ ] Write release notes for `v1.0.0`: summarize the 4 core features, link to `docs/METHODOLOGY.md`, note the 2-dependency install
- [ ] Pin the repo on your GitHub profile
- [ ] Add the profile README section (section 1 above)
- [ ] Record and add the demo GIF (optional but strongly increases star conversion)
- [ ] Share it where it's actually welcome and on-topic — not a mass-post:
  - r/SEO or r/TechSEO (only if their rules allow tool shares; check pinned rules first)
  - Indie Hackers "What I built" / Show HN style post (Hacker News "Show HN: TopicGuard — local SEO cannibalization/orphan/decay auditor")
  - Relevant SEO Slack/Discord communities you're already a genuine member of
  - Your own site, [SEO by Subham](https://seobysubham.com/), as a natural blog post ("I built a tool because every cannibalization script required GSC access")

## 6. First 10 GitHub issues to open (seed for contributors)

1. **Add sitemap.xml-based seeding** — let `--seed-sitemap urls.xml` feed the crawler exact URLs instead of relying only on link discovery. *(good first issue)*
2. **Add `--exclude` URL pattern flag** — skip paths matching a regex/glob (e.g. `/tag/*`, `/wp-json/*`) during crawl. *(good first issue)*
3. **Redirect chain detection** — flag 3xx chains longer than 1 hop during the crawl, export as `redirects.csv`.
4. **Config file support** — allow a `.topicguard.yml` to set default flags instead of long CLI invocations.
5. **Progress bar for large crawls** — replace the plain print statements with a lightweight stdlib-only progress indicator for `--max-pages` > 100.
6. **Historical diff mode** — `topicguard diff old-report/ new-report/` to show what changed between two runs (new orphans, resolved overlaps, decay score deltas).
7. **Optional headless-browser crawl mode** — Playwright-based fetch behind a `--render-js` flag for JS-heavy sites, kept fully optional so the default install stays 2 dependencies.
8. **Anchor text extraction for internal links** — capture the anchor text used in each internal link (not just the target URL) for a future internal-anchor-diversity report.
9. **Dockerfile + `docker run` one-liner** — for people who don't want a local Python environment.
10. **Simple local web dashboard** — a minimal Flask app that serves `report.json` interactively instead of (or alongside) the static HTML report. *(bigger scope — good for a contributor wanting a meatier project)*
