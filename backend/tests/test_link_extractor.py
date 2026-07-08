"""Unit tests for the link extractor utility."""

from app.exploration.link_extractor import extract_links


BASE_URL = "https://example.com/app"


def test_extracts_absolute_same_origin_links() -> None:
    html = '<a href="https://example.com/about">About</a>'
    result = extract_links(html, BASE_URL)
    assert result == ("https://example.com/about",)


def test_resolves_relative_links() -> None:
    html = '<a href="/dashboard">Dashboard</a><a href="settings">Settings</a>'
    result = extract_links(html, BASE_URL)
    assert "https://example.com/dashboard" in result
    assert "https://example.com/settings" in result


def test_filters_cross_origin_links() -> None:
    html = (
        '<a href="https://other-site.com/page">Other</a>'
        '<a href="https://example.com/ok">OK</a>'
    )
    result = extract_links(html, BASE_URL)
    assert result == ("https://example.com/ok",)


def test_filters_ignored_schemes() -> None:
    html = (
        '<a href="mailto:user@example.com">Email</a>'
        '<a href="tel:+1234567890">Call</a>'
        '<a href="javascript:void(0)">JS</a>'
        '<a href="data:text/html,<h1>Hi</h1>">Data</a>'
    )
    result = extract_links(html, BASE_URL)
    assert result == ()


def test_filters_fragment_only_links() -> None:
    html = '<a href="#">Top</a><a href="#section">Section</a>'
    result = extract_links(html, BASE_URL)
    assert result == ()


def test_deduplicates_links() -> None:
    html = (
        '<a href="/page">Page</a>'
        '<a href="/page">Page again</a>'
        '<a href="/page#section">Page with fragment</a>'
    )
    result = extract_links(html, BASE_URL)
    assert result == ("https://example.com/page",)


def test_strips_trailing_slashes_for_dedup() -> None:
    html = '<a href="/about/">About</a><a href="/about">About</a>'
    result = extract_links(html, BASE_URL)
    assert result == ("https://example.com/about",)


def test_returns_sorted_results() -> None:
    html = '<a href="/z">Z</a><a href="/a">A</a><a href="/m">M</a>'
    result = extract_links(html, BASE_URL)
    assert result == (
        "https://example.com/a",
        "https://example.com/m",
        "https://example.com/z",
    )


def test_handles_empty_html() -> None:
    result = extract_links("", BASE_URL)
    assert result == ()


def test_handles_links_without_href() -> None:
    html = '<a name="anchor">No href</a><a href="/ok">OK</a>'
    result = extract_links(html, BASE_URL)
    assert result == ("https://example.com/ok",)


def test_skips_empty_href() -> None:
    html = '<a href="">Empty</a><a href="  ">Whitespace</a>'
    result = extract_links(html, BASE_URL)
    assert result == ()
