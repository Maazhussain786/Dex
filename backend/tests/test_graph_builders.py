import pytest
from app.domain.models import Evidence, EvidenceType
from app.exploration.contracts import ExplorationReport, ExplorationTarget
from app.graph.navigation_graph import NavigationGraphBuilder
from app.graph.api_graph import ApiGraphBuilder
from app.graph.component_graph import ComponentGraphBuilder

@pytest.fixture
def sample_report() -> ExplorationReport:
    target = ExplorationTarget(project_id="p1", session_id="s1", url="http://example.com")
    
    # 1 Navigation event
    nav_ev = Evidence.collect(
        project_id="p1", session_id="s1",
        evidence_type=EvidenceType.NAVIGATION_EVENT,
        summary="Nav to home",
        payload={"url": "http://example.com", "status": 200, "depth": 0}
    )
    
    # 1 DOM snapshot with a link
    dom_ev = Evidence.collect(
        project_id="p1", session_id="s1",
        evidence_type=EvidenceType.DOM_SNAPSHOT,
        summary="DOM",
        payload={"url": "http://example.com", "html": '<a href="/about">About</a>'}
    )
    
    # 1 Network request
    net_ev = Evidence.collect(
        project_id="p1", session_id="s1",
        evidence_type=EvidenceType.NETWORK_REQUEST,
        summary="Network",
        payload={
            "url": "http://example.com",
            "calls": [{"method": "GET", "url": "http://example.com/api/data", "status": 200}]
        }
    )
    
    return ExplorationReport(
        target=target,
        evidence=(nav_ev, dom_ev, net_ev),
        discovered_routes=("http://example.com/about",)
    )

def test_navigation_graph_builder(sample_report: ExplorationReport):
    builder = NavigationGraphBuilder()
    nodes, edges = builder.build(sample_report)
    
    assert len(nodes) == 2
    # One node is the visited page, one is the unvisited link target
    urls = {n.properties.get("url") for n in nodes}
    assert urls == {"http://example.com", "http://example.com/about"}
    
    assert len(edges) == 1
    assert edges[0].relationship == "LINKS_TO"

def test_api_graph_builder(sample_report: ExplorationReport):
    builder = ApiGraphBuilder()
    nodes, edges = builder.build(sample_report)
    
    assert len(nodes) == 2
    kinds = {n.kind for n in nodes}
    assert kinds == {"Page", "Endpoint"}
    
    assert len(edges) == 1
    assert edges[0].relationship == "CALLS_API"

def test_component_graph_builder(sample_report: ExplorationReport):
    builder = ComponentGraphBuilder()
    nodes, edges = builder.build(sample_report)
    
    assert len(nodes) == 2
    kinds = {n.kind for n in nodes}
    assert kinds == {"Page", "Component"}
    
    assert len(edges) == 1
    assert edges[0].relationship == "CONTAINS"
