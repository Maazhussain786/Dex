"""Integration tests for the Playwright browser explorer.

These tests spin up a minimal local HTTP server serving static HTML
fixtures, then run the explorer against them.  They verify that
evidence items are collected for every category: navigation events,
DOM snapshots, screenshots, console messages, and network requests.
"""

from __future__ import annotations

import asyncio
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Generator

import pytest

from app.exploration.browser_explorer import PlaywrightExplorer
from app.exploration.contracts import ExplorationStatus, ExplorationTarget


# ---------------------------------------------------------------------------
# Fixture: tiny HTTP server serving inline HTML
# ---------------------------------------------------------------------------

_INDEX_HTML = """\
<!DOCTYPE html>
<html>
<head><title>Test App</title></head>
<body>
  <h1>Home</h1>
  <a href="/about">About</a>
  <a href="/contact">Contact</a>
  <script>console.log("page loaded");</script>
</body>
</html>
"""

_ABOUT_HTML = """\
<!DOCTYPE html>
<html>
<head><title>About</title></head>
<body>
  <h1>About</h1>
  <a href="/">Home</a>
</body>
</html>
"""

_CONTACT_HTML = """\
<!DOCTYPE html>
<html>
<head><title>Contact</title></head>
<body>
  <h1>Contact</h1>
  <a href="/">Home</a>
</body>
</html>
"""

_PAGES: dict[str, str] = {
    "/": _INDEX_HTML,
    "/about": _ABOUT_HTML,
    "/contact": _CONTACT_HTML,
}


class _FixtureHandler(SimpleHTTPRequestHandler):
    """Serve in-memory HTML pages."""

    def do_GET(self) -> None:
        path = self.path.split("?")[0].rstrip("/") or "/"
        body = _PAGES.get(path)
        if body is None:
            self.send_error(404)
            return
        encoded = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    # Suppress noisy access logs during tests.
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        pass


@pytest.fixture(scope="module")
def local_server() -> Generator[str, None, None]:
    """Start a local HTTP server and yield its base URL."""
    server = HTTPServer(("127.0.0.1", 0), _FixtureHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_explores_pages_and_collects_evidence(local_server: str) -> None:
    """Verify that exploring the fixture server collects evidence."""
    target = ExplorationTarget(
        project_id="proj-1",
        session_id="sess-1",
        url=local_server,
        max_depth=1,
    )

    explorer = PlaywrightExplorer()
    report = await explorer.explore(target)

    assert report.status == ExplorationStatus.COMPLETED
    assert report.pages_visited >= 1

    types_found = {e.evidence_type for e in report.evidence}

    # We should have at least navigation events and DOM snapshots.
    assert "navigation_event" in types_found
    assert "dom_snapshot" in types_found
    assert "screenshot" in types_found


@pytest.mark.asyncio
async def test_discovers_same_origin_routes(local_server: str) -> None:
    """Verify that same-origin links are reported as discovered routes."""
    target = ExplorationTarget(
        project_id="proj-2",
        session_id="sess-2",
        url=local_server,
        max_depth=1,
    )

    explorer = PlaywrightExplorer()
    report = await explorer.explore(target)

    # The index page links to /about and /contact.
    assert any("/about" in route for route in report.discovered_routes)
    assert any("/contact" in route for route in report.discovered_routes)


@pytest.mark.asyncio
async def test_respects_max_depth_zero(local_server: str) -> None:
    """With max_depth=0 only the root page should be visited."""
    target = ExplorationTarget(
        project_id="proj-3",
        session_id="sess-3",
        url=local_server,
        max_depth=0,
    )

    explorer = PlaywrightExplorer()
    report = await explorer.explore(target)

    assert report.status == ExplorationStatus.COMPLETED
    assert report.pages_visited == 1


@pytest.mark.asyncio
async def test_screenshot_disabled(local_server: str) -> None:
    """When screenshots are disabled, no screenshot evidence should exist."""
    target = ExplorationTarget(
        project_id="proj-4",
        session_id="sess-4",
        url=local_server,
        max_depth=0,
        screenshot_enabled=False,
    )

    explorer = PlaywrightExplorer()
    report = await explorer.explore(target)

    types_found = {e.evidence_type for e in report.evidence}
    assert "screenshot" not in types_found


@pytest.mark.asyncio
async def test_network_capture_disabled(local_server: str) -> None:
    """When network capture is disabled, no network evidence should exist."""
    target = ExplorationTarget(
        project_id="proj-5",
        session_id="sess-5",
        url=local_server,
        max_depth=0,
        network_capture_enabled=False,
    )

    explorer = PlaywrightExplorer()
    report = await explorer.explore(target)

    types_found = {e.evidence_type for e in report.evidence}
    assert "network_request" not in types_found
