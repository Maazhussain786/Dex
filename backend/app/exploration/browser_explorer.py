"""Playwright-based browser exploration engine.

``PlaywrightExplorer`` is the concrete implementation of ``BrowserExplorer``.
It launches a headless Chromium instance, navigates to a target URL, and
recursively discovers pages while collecting structured evidence at every
step:

* **Screenshots** — full-page PNG encoded as base64.
* **DOM snapshots** — raw HTML of the rendered page.
* **Network requests** — method, URL, status, headers, timing.
* **Console logs** — messages printed by the application.
* **JS errors** — uncaught exceptions from ``pageerror``.
* **Navigation events** — each page transition with source/target URL.

All evidence is wrapped in :class:`~app.domain.models.Evidence` and
returned as an :class:`ExplorationReport`.
"""

from __future__ import annotations

import base64
import time
from dataclasses import dataclass, field

from playwright.async_api import (
    Browser,
    BrowserContext,
    ConsoleMessage,
    Error as PlaywrightError,
    Page,
    Request,
    Response,
    async_playwright,
)

from app.core.logging import get_logger
from app.domain.models import Evidence, EvidenceType
from app.exploration.contracts import (
    BrowserExplorer,
    ExplorationProgress,
    ExplorationReport,
    ExplorationStatus,
    ExplorationTarget,
)
from app.exploration.link_extractor import extract_links

logger = get_logger("exploration.browser")


# ---------------------------------------------------------------------------
# Internal collection helpers
# ---------------------------------------------------------------------------

@dataclass
class _PageCollector:
    """Accumulates raw event data for a single page visit."""

    url: str
    console_messages: list[dict[str, str]] = field(default_factory=list)
    network_calls: list[dict[str, object]] = field(default_factory=list)
    js_errors: list[str] = field(default_factory=list)

    # Timing helpers
    _request_times: dict[str, float] = field(default_factory=dict)

    def on_console(self, msg: ConsoleMessage) -> None:
        self.console_messages.append({
            "type": msg.type,
            "text": msg.text,
        })

    def on_page_error(self, error: PlaywrightError) -> None:
        self.js_errors.append(str(error))

    def on_request(self, request: Request) -> None:
        self._request_times[request.url] = time.monotonic()

    def on_response(self, response: Response) -> None:
        elapsed_ms = 0.0
        if response.url in self._request_times:
            elapsed_ms = round(
                (time.monotonic() - self._request_times[response.url]) * 1000, 2
            )
        self.network_calls.append({
            "method": response.request.method,
            "url": response.url,
            "status": response.status,
            "content_type": response.headers.get("content-type", ""),
            "elapsed_ms": elapsed_ms,
        })


# ---------------------------------------------------------------------------
# Explorer implementation
# ---------------------------------------------------------------------------

class PlaywrightExplorer(BrowserExplorer):
    """Concrete Playwright-based explorer.

    Usage::

        explorer = PlaywrightExplorer()
        report = await explorer.explore(target)
    """

    async def explore(self, target: ExplorationTarget) -> ExplorationReport:
        """Explore the target URL up to ``max_depth`` levels."""

        progress = ExplorationProgress(status=ExplorationStatus.RUNNING)
        evidence_items: list[Evidence] = []
        visited: set[str] = set()
        discovered_routes: set[str] = set()
        errors: list[str] = []

        logger.info(
            "Starting exploration",
            extra={"data": {"url": target.url, "max_depth": target.max_depth}},
        )

        try:
            async with async_playwright() as pw:
                browser: Browser = await pw.chromium.launch(headless=True)
                context: BrowserContext = await browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36 Dex/0.1"
                    ),
                )

                page: Page = await context.new_page()

                await self._explore_recursive(
                    page=page,
                    url=target.url,
                    target=target,
                    depth=0,
                    visited=visited,
                    evidence=evidence_items,
                    discovered_routes=discovered_routes,
                    errors=errors,
                    progress=progress,
                )

                await browser.close()

            progress.status = ExplorationStatus.COMPLETED
            logger.info(
                "Exploration completed",
                extra={"data": {
                    "pages_visited": progress.pages_visited,
                    "evidence_collected": len(evidence_items),
                    "routes_discovered": len(discovered_routes),
                }},
            )

        except Exception as exc:
            progress.status = ExplorationStatus.FAILED
            errors.append(f"Exploration failed: {exc}")
            logger.exception("Exploration failed")

        return ExplorationReport(
            target=target,
            status=progress.status,
            evidence=tuple(evidence_items),
            discovered_routes=tuple(sorted(discovered_routes)),
            errors=tuple(errors),
            pages_visited=progress.pages_visited,
        )

    # ------------------------------------------------------------------
    # Recursive page visitor
    # ------------------------------------------------------------------

    async def _explore_recursive(
        self,
        *,
        page: Page,
        url: str,
        target: ExplorationTarget,
        depth: int,
        visited: set[str],
        evidence: list[Evidence],
        discovered_routes: set[str],
        errors: list[str],
        progress: ExplorationProgress,
    ) -> None:
        """Visit *url* and recursively follow same-origin links."""

        if url in visited or depth > target.max_depth:
            return

        visited.add(url)
        progress.current_url = url

        collector = _PageCollector(url=url)

        # Attach event listeners.
        page.on("console", collector.on_console)
        page.on("pageerror", collector.on_page_error)
        if target.network_capture_enabled:
            page.on("request", collector.on_request)
            page.on("response", collector.on_response)

        try:
            response = await page.goto(url, wait_until="networkidle", timeout=30_000)
            if response is None:
                errors.append(f"No response from {url}")
                return

            progress.pages_visited += 1

            # Record navigation event.
            evidence.append(Evidence.collect(
                project_id=target.project_id,
                session_id=target.session_id,
                evidence_type=EvidenceType.NAVIGATION_EVENT,
                summary=f"Navigated to {url}",
                payload={"url": url, "status": response.status, "depth": depth},
            ))

            # Capture DOM snapshot.
            html = await page.content()
            evidence.append(Evidence.collect(
                project_id=target.project_id,
                session_id=target.session_id,
                evidence_type=EvidenceType.DOM_SNAPSHOT,
                summary=f"DOM snapshot of {url}",
                payload={"url": url, "html_length": len(html), "html": html},
            ))

            # Capture screenshot.
            if target.screenshot_enabled:
                screenshot_bytes = await page.screenshot(full_page=True)
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode("ascii")
                evidence.append(Evidence.collect(
                    project_id=target.project_id,
                    session_id=target.session_id,
                    evidence_type=EvidenceType.SCREENSHOT,
                    summary=f"Screenshot of {url}",
                    payload={"url": url, "format": "png", "base64": screenshot_b64},
                ))

            # Flush console logs.
            if collector.console_messages:
                evidence.append(Evidence.collect(
                    project_id=target.project_id,
                    session_id=target.session_id,
                    evidence_type=EvidenceType.CONSOLE_LOG,
                    summary=f"{len(collector.console_messages)} console message(s) on {url}",
                    payload={"url": url, "messages": collector.console_messages},
                ))

            # Flush network calls.
            if collector.network_calls and target.network_capture_enabled:
                evidence.append(Evidence.collect(
                    project_id=target.project_id,
                    session_id=target.session_id,
                    evidence_type=EvidenceType.NETWORK_REQUEST,
                    summary=f"{len(collector.network_calls)} network call(s) on {url}",
                    payload={"url": url, "calls": collector.network_calls},
                ))

            # Flush JS errors.
            if collector.js_errors:
                evidence.append(Evidence.collect(
                    project_id=target.project_id,
                    session_id=target.session_id,
                    evidence_type=EvidenceType.ANALYSIS_FINDING,
                    summary=f"{len(collector.js_errors)} JS error(s) on {url}",
                    payload={"url": url, "errors": collector.js_errors},
                ))

            progress.evidence_collected = len(evidence)

            # Discover same-origin links and recurse.
            links = extract_links(html, url)
            for link in links:
                discovered_routes.add(link)
            for link in links:
                await self._explore_recursive(
                    page=page,
                    url=link,
                    target=target,
                    depth=depth + 1,
                    visited=visited,
                    evidence=evidence,
                    discovered_routes=discovered_routes,
                    errors=errors,
                    progress=progress,
                )

        except Exception as exc:
            msg = f"Error exploring {url}: {exc}"
            errors.append(msg)
            logger.warning(msg)

        finally:
            # Detach event listeners to prevent leaks.
            page.remove_listener("console", collector.on_console)
            page.remove_listener("pageerror", collector.on_page_error)
            if target.network_capture_enabled:
                page.remove_listener("request", collector.on_request)
                page.remove_listener("response", collector.on_response)
