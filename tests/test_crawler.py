import pytest
import requests

from topicguard.crawler import Crawler, PageRecord

HOME_HTML = """
<html><head><title>Home | Example</title>
<meta name="description" content="Welcome to Example.">
<link rel="canonical" href="https://example.com/">
</head><body>
<h1>Welcome</h1>
<p>This is the homepage with some example content about widgets and gadgets.</p>
<a href="/about">About</a>
<a href="/products">Products</a>
<a href="https://external.com/page">External</a>
<a href="mailto:hi@example.com">Email</a>
</body></html>
"""

ABOUT_HTML = """
<html><head><title>About | Example</title></head>
<body><h1>About Us</h1><p>We make widgets.</p>
<a href="/">Home</a>
</body></html>
"""


class FakeResponse:
    def __init__(self, text="", status_code=200, headers=None):
        self.text = text
        self.status_code = status_code
        self.headers = headers or {"Content-Type": "text/html"}


class FakeSession:
    """Minimal stand-in for requests.Session with canned responses."""

    def __init__(self, routes: dict[str, FakeResponse]):
        self.routes = routes
        self.headers = {}

    def get(self, url, timeout=None, allow_redirects=True):
        if url in self.routes:
            return self.routes[url]
        raise requests.exceptions.ConnectionError(f"no route for {url}")


def make_crawler(routes, **kwargs):
    session = FakeSession(routes)
    crawler = Crawler(
        start_url="https://example.com/",
        respect_robots=False,
        session=session,
        **kwargs,
    )
    return crawler


def test_crawl_normal_case_extracts_pages_and_links():
    routes = {
        "https://example.com/": FakeResponse(HOME_HTML),
        "https://example.com/about": FakeResponse(ABOUT_HTML),
        "https://example.com/products": FakeResponse("<html><head><title>Products</title></head><body>Products page.</body></html>"),
    }
    crawler = make_crawler(routes, max_pages=10, delay=0)
    pages = crawler.crawl()

    home = pages["https://example.com/"]
    assert home.title == "Home | Example"
    assert home.meta_description == "Welcome to Example."
    assert home.h1s == ["Welcome"]
    assert home.canonical == "https://example.com/"
    assert "https://example.com/about" in home.outlinks
    assert "https://external.com/page" not in home.outlinks  # external excluded
    assert not any(link.startswith("mailto:") for link in home.outlinks)

    assert "https://example.com/about" in pages
    assert pages["https://example.com/about"].title == "About | Example"


def test_crawl_respects_max_pages():
    routes = {
        "https://example.com/": FakeResponse(HOME_HTML),
        "https://example.com/about": FakeResponse(ABOUT_HTML),
        "https://example.com/products": FakeResponse("<html><body>x</body></html>"),
    }
    crawler = make_crawler(routes, max_pages=1, delay=0)
    pages = crawler.crawl()
    assert len(pages) == 1


def test_http_error_status_recorded_without_crash():
    routes = {
        "https://example.com/": FakeResponse("Not found", status_code=404, headers={"Content-Type": "text/html"}),
    }
    crawler = make_crawler(routes, max_pages=5, delay=0)
    pages = crawler.crawl()
    record = pages["https://example.com/"]
    assert record.status_code == 404
    assert record.title == ""  # error pages aren't parsed for content


def test_connection_failure_is_captured_as_error_not_exception():
    crawler = make_crawler({}, max_pages=5, delay=0)  # no routes registered at all
    pages = crawler.crawl()
    record = pages["https://example.com/"]
    assert record.error is not None
    assert record.status_code is None


def test_non_html_content_type_is_skipped_gracefully():
    routes = {
        "https://example.com/": FakeResponse(
            "%PDF-1.4 binary data", status_code=200, headers={"Content-Type": "application/pdf"}
        )
    }
    crawler = make_crawler(routes, max_pages=5, delay=0)
    pages = crawler.crawl()
    record = pages["https://example.com/"]
    assert record.status_code == 200
    assert record.title == ""


def test_invalid_start_url_raises_value_error():
    with pytest.raises(ValueError):
        Crawler(start_url="not-a-url", respect_robots=False)


def test_empty_html_page_has_zero_word_count():
    routes = {"https://example.com/": FakeResponse("<html><head><title></title></head><body></body></html>")}
    crawler = make_crawler(routes, max_pages=1, delay=0)
    pages = crawler.crawl()
    assert pages["https://example.com/"].word_count == 0
