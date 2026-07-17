"""Builds a navigation graph connecting Page nodes via LINKS_TO edges."""

from __future__ import annotations

import uuid
from typing import Sequence

from app.domain.models import EvidenceType, GraphEdge, GraphNode
from app.exploration.contracts import ExplorationReport
from app.exploration.link_extractor import extract_links
from app.graph.contracts import GraphBuilder


class NavigationGraphBuilder(GraphBuilder):
    """Extracts Page nodes and LINKS_TO edges from navigation and DOM evidence."""

    def build(self, report: ExplorationReport) -> tuple[Sequence[GraphNode], Sequence[GraphEdge]]:
        nodes_by_url: dict[str, GraphNode] = {}
        edges: list[GraphEdge] = []

        # 1. Create nodes for all visited pages from NAVIGATION_EVENT
        nav_evidence = [e for e in report.evidence if e.evidence_type == EvidenceType.NAVIGATION_EVENT]
        for e in nav_evidence:
            url = str(e.payload.get("url", ""))
            status = e.payload.get("status")
            if url and url not in nodes_by_url:
                nodes_by_url[url] = GraphNode(
                    id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"page:{url}")),
                    label="Page",
                    kind="Page",
                    properties={"url": url, "status": status, "visited": True},
                )

        # 2. Extract links from DOM_SNAPSHOT to create edges and unvisited nodes
        dom_evidence = [e for e in report.evidence if e.evidence_type == EvidenceType.DOM_SNAPSHOT]
        for e in dom_evidence:
            url = str(e.payload.get("url", ""))
            html = str(e.payload.get("html", ""))
            if not url or not html:
                continue

            source_node = nodes_by_url.get(url)
            if not source_node:
                # Fallback if DOM snapshot exists but navigation event didn't
                source_node = GraphNode(
                    id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"page:{url}")),
                    label="Page",
                    kind="Page",
                    properties={"url": url, "visited": True},
                )
                nodes_by_url[url] = source_node

            links = extract_links(html, url)
            for link in links:
                target_node = nodes_by_url.get(link)
                if not target_node:
                    # Target node wasn't visited, but we found a link to it
                    target_node = GraphNode(
                        id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"page:{link}")),
                        label="Page",
                        kind="Page",
                        properties={"url": link, "visited": False},
                    )
                    nodes_by_url[link] = target_node

                edges.append(GraphEdge(
                    source_id=source_node.id,
                    target_id=target_node.id,
                    relationship="LINKS_TO",
                    evidence_ids=(e.id,),
                ))

        return tuple(nodes_by_url.values()), tuple(edges)
