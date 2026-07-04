# Dex Architecture

Dex is built around evidence collection, structured modeling, and explanation.

## System Context

```mermaid
flowchart LR
  User[Developer] --> Frontend[Next.js Dashboard]
  Frontend --> Backend[FastAPI API]
  Backend --> Explorer[Playwright Explorer]
  Backend --> Agents[Agent Runtime]
  Backend --> Postgres[(PostgreSQL)]
  Backend --> Neo4j[(Neo4j)]
  Backend --> Vector[(Vector Store)]
  Explorer --> Target[Target Web App]
  Agents --> Postgres
  Agents --> Neo4j
  Agents --> Vector
```

## Backend Boundaries

- `api`: HTTP routes and request/response schemas.
- `core`: configuration, logging, and application wiring.
- `domain`: stable business concepts such as projects, sessions, evidence, graph nodes, and agents.
- `agents`: coordinator and specialist agent contracts.
- `exploration`: browser automation and runtime evidence collection.
- `storage`: database, graph, and vector store adapters.

## Evidence Model

Evidence is the core primitive. Every analysis result should point back to collected observations such as:

- DOM snapshots.
- Screenshots.
- Network requests and responses.
- Console logs.
- JavaScript errors.
- Navigation events.
- Source files.
- Dependency metadata.

## Agent Flow

```mermaid
sequenceDiagram
  participant D as Developer
  participant C as Coordinator
  participant B as Browser Explorer
  participant A as Specialist Agents
  participant G as Knowledge Graph
  participant R as Reasoning Agent

  D->>C: Start exploration
  C->>B: Explore target
  B->>C: Evidence events
  C->>A: Analyze evidence
  A->>G: Write nodes and edges
  D->>R: Ask question
  R->>G: Retrieve evidence and relationships
  R->>D: Evidence-backed answer
```

## Design Principles

- Evidence before explanation.
- Small modules with clear responsibilities.
- Explicit contracts between agents.
- Structured storage before LLM reasoning.
- Incremental exploration with resumable sessions.
- Plugin-friendly boundaries for future targets.
