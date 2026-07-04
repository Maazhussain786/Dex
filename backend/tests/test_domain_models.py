from app.domain.models import Evidence, EvidenceType, ExplorationSession, Project, ProjectStatus


def test_project_create_defaults_to_draft() -> None:
    project = Project.create(name="Demo", target_url="https://example.com")

    assert project.name == "Demo"
    assert project.target_url == "https://example.com"
    assert project.status == ProjectStatus.DRAFT


def test_exploration_session_has_project_id() -> None:
    session = ExplorationSession.start(project_id="project-1")

    assert session.project_id == "project-1"
    assert session.completed_at is None


def test_evidence_collect_uses_payload_default() -> None:
    evidence = Evidence.collect(
        project_id="project-1",
        session_id="session-1",
        evidence_type=EvidenceType.DOM_SNAPSHOT,
        summary="Captured login page DOM",
    )

    assert evidence.payload == {}
    assert evidence.summary == "Captured login page DOM"
