# Contributing to TopicGuard

Thanks for considering a contribution — this project is small on purpose,
and PRs that keep it that way (few dependencies, readable modules, honest
documentation of limitations) are especially welcome.

## Getting set up

```bash
git clone https://github.com/subham-seo/topicguard.git
cd topicguard
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Running tests

```bash
pytest
```

Tests are organized by module (`tests/test_crawler.py`,
`tests/test_cannibalization.py`, etc.) and use mocked HTTP responses — no
test hits the live network, so `pytest` should be fast and deterministic.
Please add tests for new behavior, including at least one "bad input" or
edge case per feature (malformed HTML, missing headers, empty files —
see existing tests for the pattern).

## Code style

- Standard library / `requests` / `beautifulsoup4` only for the core
  crawl-and-analyze path. New *required* dependencies need a strong
  justification in the PR description — the "install in under a minute"
  goal is a project value, not a suggestion. Optional features (like the
  GSC CSV enrichment) that only activate via a flag are more flexible.
- Type hints on public functions.
- Every custom metric or heuristic must be documented in
  `docs/METHODOLOGY.md` — what it measures, the formula, assumptions, and
  limitations. PRs adding a new metric without a methodology entry will
  be asked to add one before merge.

## Reporting bugs / requesting features

Please use the issue templates — they ask for the specific info needed to
reproduce or scope the work (crawled URL patterns, Python version, OS,
expected vs. actual output).

## Pull requests

1. Fork, branch from `main`, keep PRs focused on one change.
2. Make sure `pytest` passes locally.
3. Update `docs/METHODOLOGY.md` or `README.md` if behavior/metrics change.
4. Open the PR using the provided template — link the issue it resolves,
   if any.

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md).
