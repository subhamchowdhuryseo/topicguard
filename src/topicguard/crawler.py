"""Lightweight breadth-first site crawler.

Uses only `requests` + `BeautifulSoup`. No headless browser, so JavaScript-
rendered content will not be picked up (see docs/METHODOLOGY.md). This is a
deliberate trade-off: it keeps the tool installable with two pip packages
and no browser binaries, which matters for a project people will actually
run on the first try.
"""

from __future__ import annotations

import time
import urllib.robotparser as robotparser
from collections import deque
from dataclasses import dataclass, field
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from .utils import normalize_url, same_domain

USER_AGENT = "TopicGuardBot/1.0 (+https://github.com/subham-seo/topicguard)"
DEFAULT_TIMEOUT = 10


@dataclass
class PageRecord:
    url: str
    status_code: int | None = None
    error: str | None = None
    title: str = ""
    meta_description: str = ""
    h1s: list[str] = field(default_factory=list)
    word_count: int = 0
    canonical: str | None = None
    noindex: bool = False
    last_modified: str | None = None
    outlinks: list[str] = field(default_factory=list)  # internal, normalized
    text: str = ""  # visible body text, used for similarity comparisons


class Crawler:
    """Breadth-first crawler bounded by `max_pages` and same-domain scope."""

    def __init__(
        self,
        start_url: str,
        max_pages: int = 200,
        delay: float = 0.3,
        respect_robots: bool = True,
        timeout: int = DEFAULT_TIMEOUT,
        session: requests.Session | None = None,
    ) -> None:
        self.start_url = normalize_url(start_url)
        parsed = urlparse(self.start_url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"Start URL must be http(s): {start_url!r}")
        self.root_netloc = parsed.netloc
        self.max_pages = max(1, max_pages)
        self.delay = max(0.0, delay)
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

        self.robot_parser: robotparser.RobotFileParser | None = None
        if respect_robots:
            self.robot_parser = self._load_robots(parsed)

    def _load_robots(self, parsed) -> robotparser.RobotFileParser | None:
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = robotparser.RobotFileParser()
        try:
            resp = self.session.get(robots_url, timeout=self.timeout)
            if resp.status_code == 200:
                rp.parse(resp.text.splitlines())
                return rp
        except requests.RequestException:
            pass
        return None

    def _allowed(self, url: str) -> bool:
        if self.robot_parser is None:
            return True
        try:
            return self.robot_parser.can_fetch(USER_AGENT, url)
        except Exception:
            return True

    def crawl(self, extra_seed_urls: list[str] | None = None) -> dict[str, PageRecord]:
        """Run the crawl and return {normalized_url: PageRecord}."""
        queue: deque[str] = deque([self.start_url])
        for u in extra_seed_urls or []:
            nu = normalize_url(u, base=self.start_url)
            if same_domain(nu, self.root_netloc):
                queue.append(nu)

        visited: dict[str, PageRecord] = {}
        seen: set[str] = set()

        while queue and len(visited) < self.max_pages:
            url = queue.popleft()
            if url in seen:
                continue
            seen.add(url)

            if not self._allowed(url):
                visited[url] = PageRecord(url=url, error="blocked_by_robots_txt")
                continue

            record = self._fetch_and_parse(url)
            visited[url] = record

            for link in record.outlinks:
                if link not in seen and len(visited) + len(queue) < self.max_pages * 3:
                    queue.append(link)

            if self.delay:
                time.sleep(self.delay)

        return visited

    def _fetch_and_parse(self, url: str) -> PageRecord:
        record = PageRecord(url=url)
        try:
            resp = self.session.get(url, timeout=self.timeout, allow_redirects=True)
        except requests.RequestException as exc:
            record.error = f"request_failed: {exc.__class__.__name__}"
            return record

        record.status_code = resp.status_code
        record.last_modified = resp.headers.get("Last-Modified")

        content_type = resp.headers.get("Content-Type", "")
        if resp.status_code >= 400 or "text/html" not in content_type:
            return record

        soup = BeautifulSoup(resp.text, "html.parser")

        title_tag = soup.find("title")
        record.title = title_tag.get_text(strip=True) if title_tag else ""

        meta_desc = soup.find("meta", attrs={"name": "description"})
        record.meta_description = (meta_desc.get("content", "") if meta_desc else "").strip()

        record.h1s = [h.get_text(strip=True) for h in soup.find_all("h1")]

        canonical_tag = soup.find("link", attrs={"rel": "canonical"})
        record.canonical = canonical_tag.get("href") if canonical_tag else None

        robots_meta = soup.find("meta", attrs={"name": "robots"})
        if robots_meta and "noindex" in (robots_meta.get("content", "").lower()):
            record.noindex = True

        for tag in soup(["script", "style", "noscript", "svg"]):
            tag.decompose()
        body_text = soup.get_text(separator=" ", strip=True)
        record.text = body_text
        record.word_count = len(body_text.split())

        internal = set()
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith(("mailto:", "tel:", "javascript:", "#")):
                continue
            resolved = normalize_url(href, base=url)
            if same_domain(resolved, self.root_netloc) and resolved.startswith(("http://", "https://")):
                internal.add(resolved)
        record.outlinks = sorted(internal)

        return record
