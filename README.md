# Dex

Dex is an autonomous software understanding platform for developers. It explores applications, captures evidence, reconstructs architecture, maps runtime behavior, discovers APIs, and answers engineering questions from structured facts instead of loose guesses.

Dex is not a chatbot. It is a system for inspecting unfamiliar software like a senior engineer would: observe behavior, collect evidence, model relationships, and explain what is happening with traceable references.

## What Dex Will Do

- Explore web applications with Playwright.
- Capture DOM snapshots, screenshots, console logs, route transitions, and network traffic.
- Detect frontend frameworks, UI patterns, state management, APIs, and runtime dependencies.
- Build navigation, API, component, dependency, and knowledge graphs.
- Store structured evidence in PostgreSQL, Neo4j, and a vector database.
- Generate architecture, API, security, performance, and onboarding documentation.
- Answer developer questions using collected evidence.

## Planned Stack

- Backend: Python, FastAPI, LangGraph, LangChain
- Frontend: Next.js, React, TypeScript, Tailwind CSS
- Browser automation: Playwright
- Graph and analysis: Neo4j, NetworkX, Tree-sitter, AST parsing
- Storage: PostgreSQL, Qdrant or Chroma
- Visualization: React Flow, Mermaid, D3.js

## Repository Layout

```text
dex/
  backend/          FastAPI service, agents, domain models, storage adapters
  frontend/         Next.js dashboard and architecture explorers
  docs/             Product vision, architecture, roadmap, and developer guides
  infra/            Docker Compose and local infrastructure configuration
```

## Development Phases

1. Repository foundation and documentation.
2. Backend foundation with project/session APIs and agent contracts.
3. Frontend foundation with a live dashboard shell.
4. Local infrastructure with Docker Compose.
5. Browser exploration pipeline.
6. Evidence graph and retrieval pipeline.
7. Security, performance, and documentation agents.

## Current Status

This repository is being built incrementally. The first milestones focus on a clean, maintainable foundation before deep automation is added.

## License

License details are not finalized yet.
