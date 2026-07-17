"""Builds an API graph from network requests."""

from __future__ import annotations

import uuid
from typing import Sequence

from app.domain.models import EvidenceType, GraphEdge, GraphNode
from app.exploration.contracts import ExplorationReport
from app.graph.contracts import GraphBuilder


class ApiGraphBuilder(GraphBuilder):
    """Extracts Route and Endpoint nodes, and CALLS_API edges from network requests."""

    def build(self, report: ExplorationReport) -> tuple[Sequence[GraphNode], Sequence[GraphEdge]]:
        nodes: dict[str, GraphNode] = {}
        edges: list[GraphEdge] = []

        network_evidence = [e for e in report.evidence if e.evidence_type == EvidenceType.NETWORK_REQUEST]
        for e in network_evidence:
            page_url = str(e.payload.get("url", ""))
            calls = e.payload.get("calls", [])

            if not isinstance(calls, list):
                continue

            page_node_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"page:{page_url}"))
            if page_node_id not in nodes:
                nodes[page_node_id] = GraphNode(
                    id=page_node_id,
                    label="Page",
                    kind="Page",
                    properties={"url": page_url},
                )

            for call in calls:
                if not isinstance(call, dict):
                    continue
                url = str(call.get("url", ""))
                method = str(call.get("method", "")).upper()
                status = call.get("status")

                if not url or url.startswith("data:") or url.startswith("blob:"):
                    continue

                endpoint_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"endpoint:{method}:{url}"))
                if endpoint_id not in nodes:
                    nodes[endpoint_id] = GraphNode(
                        id=endpoint_id,
                        label="Endpoint",
                        kind="Endpoint",
                        properties={
                            "url": url,
                            "method": method,
                        },
                    )

                edges.append(GraphEdge(
                    source_id=page_node_id,
                    target_id=endpoint_id,
                    relationship="CALLS_API",
                    evidence_ids=(e.id,),
                ))

        return tuple(nodes.values()), tuple(edges)
