"""Contracts for Knowledge Graph extraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from app.domain.models import GraphEdge, GraphNode
from app.exploration.contracts import ExplorationReport


class GraphBuilder(ABC):
    """Abstract base class for extracting a Knowledge Graph from exploration evidence."""

    @abstractmethod
    def build(self, report: ExplorationReport) -> tuple[Sequence[GraphNode], Sequence[GraphEdge]]:
        """Process the report and return a tuple of nodes and edges."""
        pass
