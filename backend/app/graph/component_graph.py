"""Builds a DOM component hierarchy graph."""

from __future__ import annotations

import uuid
from typing import Sequence

from app.domain.models import EvidenceType, GraphEdge, GraphNode
from app.exploration.contracts import ExplorationReport
from app.graph.contracts import GraphBuilder


class ComponentGraphBuilder(GraphBuilder):
    """Extracts Component nodes and CONTAINS edges from DOM snapshots."""

    def build(self, report: ExplorationReport) -> tuple[Sequence[GraphNode], Sequence[GraphEdge]]:
        nodes: dict[str, GraphNode] = {}
        edges: list[GraphEdge] = []

        # Placeholder: Real DOM component extraction will require BeautifulSoup or similar
        # For Phase 7, we'll just link the Page to a generic 'Document' component to establish the pattern.
        dom_evidence = [e for e in report.evidence if e.evidence_type == EvidenceType.DOM_SNAPSHOT]
        for e in dom_evidence:
            url = str(e.payload.get("url", ""))
            if not url:
                continue

            page_node_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"page:{url}"))
            if page_node_id not in nodes:
                nodes[page_node_id] = GraphNode(
                    id=page_node_id,
                    label="Page",
                    kind="Page",
                    properties={"url": url},
                )

            component_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"component:{url}:document"))
            nodes[component_id] = GraphNode(
                id=component_id,
                label="Document",
                kind="Component",
                properties={"type": "document"},
            )

            edges.append(GraphEdge(
                source_id=page_node_id,
                target_id=component_id,
                relationship="CONTAINS",
                evidence_ids=(e.id,),
            ))

        return tuple(nodes.values()), tuple(edges)
