# Dex Roadmap

## Phase 1: Repository Foundation

- Define product vision.
- Establish repository structure.
- Add environment templates and ignore rules.
- Document architecture direction.

## Phase 2: Backend Foundation

- Create FastAPI application structure.
- Define project and exploration session domain models.
- Add agent interfaces.
- Add health and project APIs.
- Add unit tests for core contracts.

## Phase 3: Frontend Foundation

- Create Next.js app shell.
- Add dashboard layout.
- Add placeholder panels for browser, graph, API, security, performance, documentation, and reasoning views.
- Wire frontend configuration to the backend API base URL.

## Phase 4: Local Runtime

- Add Docker Compose for PostgreSQL, Neo4j, Qdrant, backend, and frontend.
- Document local development commands.
- Add basic logging and configuration guidance.

## Phase 5: Browser Exploration

- Add Playwright exploration runner.
- Capture screenshots, DOM snapshots, console logs, route transitions, and network events.
- Persist evidence records.

## Phase 6: Knowledge Graph

- Model pages, components, APIs, actions, storage, and runtime relationships.
- Persist graph nodes and edges in Neo4j.
- Generate navigation and component graphs.

## Phase 7: Retrieval and Reasoning

- Embed structured evidence.
- Add retrievers for evidence, graph neighbors, and documentation.
- Answer developer questions with citations.

## Phase 8: Specialist Agents

- Add framework, architecture, security, performance, and documentation agents.
- Generate downloadable reports.
- Support plugin extension points.
