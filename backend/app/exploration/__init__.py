"""Browser exploration pipeline.

Public API
----------
- ``ExplorationTarget``, ``ExplorationReport``, ``ExplorationStatus``,
  ``ExplorationProgress``, ``Credentials`` — data contracts.
- ``BrowserExplorer`` — abstract interface.
- ``PlaywrightExplorer`` — concrete Playwright implementation
  (requires ``playwright`` to be installed).
- ``extract_links`` — standalone link extraction utility.
"""

from app.exploration.contracts import (
    BrowserExplorer,
    Credentials,
    ExplorationProgress,
    ExplorationReport,
    ExplorationStatus,
    ExplorationTarget,
)
from app.exploration.link_extractor import extract_links

__all__ = [
    "BrowserExplorer",
    "Credentials",
    "ExplorationProgress",
    "ExplorationReport",
    "ExplorationStatus",
    "ExplorationTarget",
    "extract_links",
]


def __getattr__(name: str) -> object:
    """Lazily import ``PlaywrightExplorer`` to avoid hard dependency on playwright at import time."""
    if name == "PlaywrightExplorer":
        from app.exploration.browser_explorer import PlaywrightExplorer

        return PlaywrightExplorer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
