"""Extract and normalize same-origin links from a page.

This module operates on raw HTML strings so it can be unit-tested without
a running Playwright browser.  The ``extract_links`` function returns a
deduplicated, sorted tuple of absolute URLs that belong to the same origin
as the page being analyzed.
"""

from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse


_IGNORED_SCHEMES = frozenset({"mailto", "tel", "javascript", "data", "blob"})


class _AnchorParser(HTMLParser):
    """Minimal HTML parser that collects ``href`` values from ``<a>`` tags."""

    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        for name, value in attrs:
            if name == "href" and value is not None:
                self.hrefs.append(value)


def _is_same_origin(base_url: str, candidate: str) -> bool:
    """Return *True* if *candidate* shares scheme+host+port with *base_url*."""
    base = urlparse(base_url)
    target = urlparse(candidate)
    return (base.scheme, base.hostname, base.port) == (
        target.scheme,
        target.hostname,
        target.port,
    )


def _normalize(url: str) -> str:
    """Strip fragments and trailing slashes for deduplication."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/") or "/"
    normalized = parsed._replace(fragment="", path=path)
    return normalized.geturl()


def extract_links(html: str, page_url: str) -> tuple[str, ...]:
    """Return deduplicated, sorted same-origin links found in *html*.

    Parameters
    ----------
    html:
        Raw HTML content of the page.
    page_url:
        The URL of the page, used to resolve relative hrefs and to
        determine the origin for filtering.

    Returns
    -------
    tuple[str, ...]
        Absolute URLs belonging to the same origin, sorted alphabetically.
    """
    parser = _AnchorParser()
    parser.feed(html)

    seen: set[str] = set()
    results: list[str] = []

    for href in parser.hrefs:
        # Skip empty and fragment-only links.
        stripped = href.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Skip ignored schemes.
        scheme = urlparse(stripped).scheme
        if scheme and scheme.lower() in _IGNORED_SCHEMES:
            continue

        absolute = urljoin(page_url, stripped)
        normalized = _normalize(absolute)

        if not _is_same_origin(page_url, normalized):
            continue

        if normalized not in seen:
            seen.add(normalized)
            results.append(normalized)

    results.sort()
    return tuple(results)
