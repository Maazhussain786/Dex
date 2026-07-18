"""Neo4j implementation of :class:`GraphRepository`.

Uses the official ``neo4j`` async driver to persist and query the
knowledge graph.  Nodes are labelled by their ``kind`` and edges carry
the ``relationship`` name.
"""

from __future__ import annotations

from neo4j import AsyncDriver, AsyncGraphDatabase

from app.core.config import Settings
from app.core.logging import get_logger
from app.domain.models import GraphEdge, GraphNode
from app.storage.contracts import GraphRepository

logger = get_logger("storage.neo4j")


class Neo4jGraphRepository(GraphRepository):
    """Concrete knowledge-graph repository backed by Neo4j."""

    def __init__(self, driver: AsyncDriver) -> None:
        self._driver = driver

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------

    @classmethod
    async def create(cls, settings: Settings) -> "Neo4jGraphRepository":
        """Construct a repository with an open driver connection."""
        driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        logger.info("Connected to Neo4j", extra={"data": {"uri": settings.neo4j_uri}})
        return cls(driver)

    async def close(self) -> None:
        """Close the underlying driver."""
        await self._driver.close()
        logger.info("Neo4j driver closed")

    # ------------------------------------------------------------------
    # Node operations
    # ------------------------------------------------------------------

    async def save_node(self, node: GraphNode) -> None:
        """Create or merge a graph node.

        The node is labelled with its ``kind`` (e.g. ``Page``, ``APIEndpoint``)
        and all ``properties`` are set as Neo4j properties.
        """
        cypher = (
            f"MERGE (n:{_safe_label(node.kind)} {{id: $id}}) "
            "SET n.label = $label, n += $props"
        )
        params = {
            "id": node.id,
            "label": node.label,
            "props": {k: str(v) for k, v in node.properties.items()},
        }
        async with self._driver.session() as session:
            await session.run(cypher, params)

    async def save_edge(self, edge: GraphEdge) -> None:
        """Create or merge a graph edge.

        Both source and target nodes must already exist.  The relationship
        type is taken from ``edge.relationship``.
        """
        cypher = (
            "MATCH (a {id: $source_id}), (b {id: $target_id}) "
            f"MERGE (a)-[r:{_safe_label(edge.relationship)}]->(b) "
            "SET r.evidence_ids = $evidence_ids"
        )
        params = {
            "source_id": edge.source_id,
            "target_id": edge.target_id,
            "evidence_ids": list(edge.evidence_ids),
        }
        async with self._driver.session() as session:
            await session.run(cypher, params)

    # ------------------------------------------------------------------
    # Query operations
    # ------------------------------------------------------------------

    async def get_node(self, node_id: str) -> GraphNode | None:
        """Return a node by ID, or ``None``."""
        cypher = "MATCH (n {id: $id}) RETURN n, labels(n) AS labels"
        async with self._driver.session() as session:
            result = await session.run(cypher, {"id": node_id})
            record = await result.single()
        if record is None:
            return None
        node_data = dict(record["n"])
        labels = record["labels"]
        kind = labels[0] if labels else "Unknown"
        return GraphNode(
            id=node_data.pop("id"),
            label=node_data.pop("label", ""),
            kind=kind,
            properties=node_data,
        )

    async def get_neighbours(
        self,
        node_id: str,
        *,
        relationship: str | None = None,
        direction: str = "both",
    ) -> list[GraphNode]:
        """Return nodes connected to *node_id*.

        ``direction`` may be ``"in"``, ``"out"``, or ``"both"``.
        """
        if relationship:
            rel_clause = f"[:{_safe_label(relationship)}]"
        else:
            rel_clause = "[]"

        if direction == "out":
            pattern = f"(a {{id: $id}})-{rel_clause}->(b)"
        elif direction == "in":
            pattern = f"(a {{id: $id}})<-{rel_clause}-(b)"
        else:
            pattern = f"(a {{id: $id}})-{rel_clause}-(b)"

        cypher = f"MATCH {pattern} RETURN b, labels(b) AS labels"
        async with self._driver.session() as session:
            result = await session.run(cypher, {"id": node_id})
            records = [r async for r in result]

        nodes: list[GraphNode] = []
        for record in records:
            data = dict(record["b"])
            labels = record["labels"]
            kind = labels[0] if labels else "Unknown"
            nodes.append(GraphNode(
                id=data.pop("id"),
                label=data.pop("label", ""),
                kind=kind,
                properties=data,
            ))
        return nodes

    async def query(self, cypher: str, parameters: dict[str, object] | None = None) -> list[dict[str, object]]:
        """Execute a raw Cypher query and return rows as dicts."""
        async with self._driver.session() as session:
            result = await session.run(cypher, parameters or {})
            return [dict(record) async for record in result]


def _safe_label(value: str) -> str:
    """Sanitise a string for use as a Neo4j label or relationship type.

    Only keeps alphanumeric characters and underscores to prevent
    Cypher injection.
    """
    return "".join(c if c.isalnum() or c == "_" else "_" for c in value)
