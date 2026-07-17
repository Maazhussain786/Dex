# Dex — Current Status & Next Steps

> **Last updated:** 2026-07-09
> This file is the living status document for the Dex project. Update it every time a phase is completed or a significant decision is made.

---

## Current Phase: Phase 7 Complete — Moving to Phase 8

---

## ✅ What Is Already Built

### Phase 1 — Repository Foundation (Complete)
- `README.md` with project description and quick-start guide
- `docs/VISION.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`, `docs/DEVELOPMENT.md`
- `.gitignore` covering Python, Node, editors, Docker, runtime artifacts
- `.env.example` with all expected environment variables documented
- Git repository initialized with clean commit history

### Phase 2 — Backend Foundation (Complete)
- **FastAPI application** bootstrapped in `backend/app/main.py`
  - CORS middleware wired to `DEX_CORS_ORIGINS` env var
  - Routers registered: `/health` and `/projects`
- **Domain models** (`backend/app/domain/models.py`)
  - `Project`, `ExplorationSession`, `Evidence`, `GraphNode`, `GraphEdge`
  - `ProjectStatus`, `EvidenceType`, `AgentRole` enums
  - All frozen dataclasses with factory class methods
- **Agent system** (`backend/app/agents/`)
  - `AgentTask` and `AgentResult` contracts
  - `Agent` ABC with single `run()` method
  - `AgentRegistry` for plugging in agent implementations
  - `Coordinator` that dispatches to registered agents in role order
- **Core** (`backend/app/core/`)
  - `Settings` loaded from environment vars via `get_settings()` with `lru_cache`
  - Structured `get_logger()` with JSON-ready extra fields
- **API routes**
  - `GET /health` — basic alive check
  - `POST /projects`, `GET /projects`, `GET /projects/{id}` — DB-backed CRUD
- **Tests**
  - `test_domain_models.py` — unit tests for domain model factories
  - `test_link_extractor.py` — unit tests for the HTML link extractor
  - `test_browser_explorer.py` — integration tests with a local HTTP server fixture

### Phase 3 — Frontend Foundation (Complete)
- **Next.js app** at `frontend/`
  - Tailwind CSS with custom design tokens: `mint`, `brass`, `coral`, `violet`, `panel`, `line`, `ink`
  - Dark theme with subtle gradient background
  - Inter font via CSS
- **Dashboard shell** (`frontend/app/page.tsx`)
  - Header with Dex logo, target URL input, and "Start Exploration" button
  - Metrics row: Routes mapped, APIs classified, Security signals, Runtime evidence
  - **Live Browser Session** panel (placeholder, shows "waiting for backend events")
  - **Agent Runtime** panel showing agent names and states
  - **Knowledge Graph** panel with static example graph rows
  - **API Explorer** panel with example classified endpoints
  - **Risk and Performance** panel with security and performance notices
  - **Documentation** panel with report type buttons
  - **Reasoning Panel** with example Q&A layout

### Phase 4 — Local Runtime (Complete)
- **`docker-compose.yml`** defines five services:
  - `postgres:16-alpine` with health check, persistent volume
  - `neo4j:5-community` with bolt + HTTP ports
  - `qdrant:v1.12.4` with REST + gRPC ports
  - `backend` — builds from `backend/Dockerfile`, depends on postgres (healthy), neo4j, qdrant
  - `frontend` — builds from `frontend/Dockerfile`, depends on backend
- Environment variables passed to backend for all database connections

### Phase 5 — Browser Exploration Pipeline (Complete)
- **`PlaywrightExplorer`** (`backend/app/exploration/browser_explorer.py`)
  - Launches headless Chromium via `async_playwright`
  - Recursive page visitor respecting `max_depth`
  - Collects per-page: navigation events, DOM snapshots, screenshots (base64 PNG), console logs, network request/response pairs with timing
  - Detaches all listeners in `finally` blocks to prevent leaks
  - Wraps all failures gracefully; stores error messages in the report
- **`ExplorationTarget` / `ExplorationReport` / `ExplorationProgress`** contracts
  - `ExplorationTarget`: `project_id`, `session_id`, `url`, `max_depth`, optional `Credentials`, feature flags
  - `ExplorationReport`: immutable result with evidence tuple, route set, error tuple, page count
  - `ExplorationProgress`: mutable tracker shared during a run
- **`extract_links`** (`backend/app/exploration/link_extractor.py`)
  - Pure-function HTML parser that returns deduplicated, sorted, same-origin absolute URLs
  - Ignores `mailto:`, `tel:`, `javascript:`, `data:`, `blob:` schemes
  - Strips fragments and normalizes trailing slashes for deduplication
- **Integration tests** with a self-contained `HTTPServer` fixture covering:
  - Evidence collection (navigation, DOM, screenshot)
  - Same-origin link discovery
  - `max_depth=0` constraint
  - Screenshot disabled
  - Network capture disabled

### Phase 6 — Storage Adapters & Session API (Complete)
- **Storage contracts** (`backend/app/storage/contracts.py`)
  - `ProjectRepository` ABC — `save()`, `get()`, `list_all()`, `update_status()`
  - `SessionRepository` ABC — `save()`, `get()`, `list_by_project()`, `mark_completed()`
  - `EvidenceRepository` ABC — `save_many()`, `get()`, `list_by_session()` with `limit`/`offset` pagination
  - `GraphRepository` ABC — `save_node()`, `save_edge()`, `get_node()`, `get_neighbours()`, `query()`
  - `VectorRepository` ABC — `upsert()`, `search()` with `VectorSearchResult` dataclass
- **PostgreSQL adapter** (`backend/app/storage/postgres/`)
  - `connection.py` — asyncpg pool management with auto-migration on startup
  - `project_repo.py` — `PgProjectRepository` with parameterized SQL
  - `session_repo.py` — `PgSessionRepository` with completion marking
  - `evidence_repo.py` — `PgEvidenceRepository` with bulk insert and JSONB payload
  - `migrations/001_init.sql` — DDL for `projects`, `exploration_sessions`, `evidence` tables
- **Neo4j adapter** (`backend/app/storage/neo4j/`)
  - `graph_repo.py` — `Neo4jGraphRepository` with MERGE-based upserts, neighbour queries with direction filtering, raw Cypher support, and label sanitization
- **Qdrant adapter** (`backend/app/storage/qdrant/`)
  - `vector_repo.py` — `QdrantVectorRepository` with lazy collection creation, cosine similarity search
- **Config updates** (`backend/app/core/config.py`)
  - Added `postgres_host`, `postgres_port`, `postgres_db`, `postgres_user`, `postgres_password` with `postgres_dsn` property
  - Added `neo4j_uri`, `neo4j_user`, `neo4j_password`
  - Added `qdrant_url`
- **FastAPI lifespan** (`backend/app/main.py`)
  - Async context manager creates PostgreSQL pool and all repositories on startup
  - Neo4j and Qdrant connections attempted but non-fatal if unavailable
  - Graceful shutdown of all connections
  - Repositories stored on `app.state` for dependency injection
- **Projects API refactored** (`backend/app/api/routes/projects.py`)
  - Removed in-memory `_PROJECTS` dict
  - All handlers now `async`, inject `ProjectRepository` from `app.state`
- **Session API** (`backend/app/api/routes/sessions.py`)
  - `POST /projects/{id}/sessions` — create session and trigger async Playwright exploration
  - `GET /projects/{id}/sessions/{sid}` — session status
  - `GET /projects/{id}/sessions/{sid}/evidence` — paginated evidence list
  - `WS /projects/{id}/sessions/{sid}/stream` — WebSocket live progress streaming
  - Background exploration task: runs PlaywrightExplorer, persists evidence, updates project/session status
- **Dependency updates** (`backend/pyproject.toml`)
  - Added `asyncpg>=0.29.0`, `neo4j>=5.20.0`, `qdrant-client>=1.9.0`
  - Added `httpx>=0.27.0` to dev dependencies
  - Added `asyncio_mode = "auto"` to pytest config (fixes tech debt)
- **Tests**
  - `test_storage_contracts.py` — 16 unit tests with in-memory fakes covering all 5 repositories
  - `test_sessions_api.py` — 8 API tests for projects and sessions endpoints

### Phase 7 — Knowledge Graph Builder (Complete)
- **Graph Contracts** (`backend/app/graph/contracts.py`)
  - `GraphBuilder` abstract base class
- **Navigation Graph** (`backend/app/graph/navigation_graph.py`)
  - Extracts Page nodes and LINKS_TO edges from navigation and DOM evidence
- **API Graph** (`backend/app/graph/api_graph.py`)
  - Extracts Endpoint nodes and CALLS_API edges from network requests
- **Component Graph** (`backend/app/graph/component_graph.py`)
  - Extracts Component nodes and CONTAINS edges from DOM snapshots
- **API Wiring** (`backend/app/api/routes/sessions.py`)
  - Graph builders run automatically after exploration task completes
- **Tests** (`backend/tests/test_graph_builders.py`)
  - Unit tests for navigation, API, and component graph builders


---

## 🔲 What Is NOT Yet Built

### RAG Pipeline (Phase 8 — Next Priority)
- [ ] Evidence embedding with a local model (e.g., `sentence-transformers`)
- [ ] Qdrant collection setup and document upsert
- [ ] Retriever: semantic search over evidence + graph-neighbour expansion
- [ ] `ReasoningAgent` implementation using LangChain + LLM
- [ ] Q&A API endpoint: `POST /projects/{id}/qa`

### Specialist Agents (Phase 9)
- [ ] `FrameworkAgent` — detect React, Vue, Angular, Next.js, Nuxt, Svelte, Tailwind, Redux
- [ ] `ArchitectureAgent` — produce component hierarchy and dependency graph
- [ ] `SecurityAgent` — auth flow, JWT, localStorage, CSP, CORS, exposed secrets
- [ ] `PerformanceAgent` — bundle analysis, waterfall, lazy loading, duplicates
- [ ] `DocumentationAgent` — generate README, API docs, onboarding guide
- [ ] Register all agents in coordinator and wire to session API

### Interactive Visualizations (Phase 10)
- [ ] Install `reactflow` in frontend
- [ ] Replace static knowledge graph panel with live `<ReactFlow>` component
- [ ] Navigation graph view
- [ ] API dependency graph view
- [ ] Component hierarchy view
- [ ] WebSocket hook to subscribe to live graph updates during exploration

### Q&A Interface (Phase 11)
- [ ] Replace static Reasoning Panel with real chat input
- [ ] Wire to `POST /projects/{id}/qa` backend endpoint
- [ ] Stream answers with evidence citation cards
- [ ] Highlight referenced graph nodes on click

### Report Generation (Phase 12)
- [ ] Connect report buttons to actual generation endpoints
- [ ] `DocumentationAgent` writes structured Markdown
- [ ] API to download as `.md` or `.pdf`
- [ ] Downloadable bundle of all reports for a session

---

## 🐛 Known Gaps & Tech Debt

| Item | Description |
|---|---|
| Frontend is fully static | All metrics and graph rows are hardcoded. Needs real API wiring. |
| No auth on API | All endpoints are open. Should add API key auth before any external deployment. |
| No BeautifulSoup yet | `pyproject.toml` does not list `beautifulsoup4`. Needed in Phase 9 for richer DOM parsing. |
| No LangChain/LangGraph yet | Not in dependencies — add when starting Phase 8. |
| WebSocket progress is poll-based | Session stream endpoint sends periodic status polls rather than true event-driven pushes. |

---

## ✅ Tech Debt Resolved in Phase 6

| Item | Resolution |
|---|---|
| In-memory project store | Replaced with `PgProjectRepository` backed by asyncpg |
| No session API | Full session CRUD + exploration trigger endpoints added |
| Missing `asyncio_mode` config | Added `asyncio_mode = "auto"` to `[tool.pytest.ini_options]` |

---

## 🗂 Phase 8 Plan (RAG Pipeline) — Detailed

This is the immediate next phase to execute.

### New Files to Create
```
backend/app/rag/
├── __init__.py
├── embeddings.py       — Local embedding generator
├── retriever.py        — Qdrant search + graph expansion
└── reasoning_agent.py  — LangChain LLM integration
```

### Files to Modify
- `backend/app/api/routes/projects.py` — add Q&A endpoint

### Tests to Add
- Unit tests for retriever
- Integration tests with Qdrant

---

## 📌 Decisions Made

| Decision | Rationale |
|---|---|
| Qdrant chosen over Chroma | Better production readiness, runs as a standalone service in Docker |
| Frozen dataclasses for domain models | Immutable value objects enforce clean boundaries and avoid accidental mutation |
| `lru_cache` on `get_settings()` | Ensures config is read once; avoids env var lookup on every request |
| Async Playwright | Matches FastAPI's async model; avoids thread blocking during exploration |
| Separate `link_extractor` module | Pure function → trivially unit-testable without a browser |
| Agent registry over DI framework | Lightweight; avoids framework coupling in the agent layer |
| asyncpg over SQLAlchemy | Direct async PostgreSQL access; lighter weight, better control over queries |
| Non-fatal Neo4j/Qdrant connections | App starts even if graph or vector DBs are unavailable; progressive feature enablement |
| Repos on `app.state` | Simple DI pattern for FastAPI; avoids complex DI container setup |
| Background task for exploration | Uses FastAPI's `BackgroundTasks` to avoid blocking session creation |

---

## 📅 Commit Convention

```
type(scope): short description

Types: feat, fix, refactor, test, docs, chore, ci
Scope: backend, frontend, storage, agents, exploration, docs, infra
```

Examples:
- `feat(storage): add PostgreSQL project and evidence repositories`
- `feat(api): add session creation and exploration trigger endpoints`
- `test(storage): add integration tests for PostgreSQL evidence repo`
- `feat(agents): implement FrameworkAgent with JS bundle detection`
