# Dex Vision

Dex is a professional developer tool for understanding complex software systems.

The goal is to make Dex behave like a senior software engineer inspecting an unfamiliar application. It should explore the application, collect evidence, reconstruct architecture, and explain behavior with references to what it observed.

## Core Objectives

Dex should automatically:

- Explore web applications.
- Understand application structure.
- Map navigation flows.
- Capture network requests.
- Discover APIs.
- Detect frameworks.
- Analyze frontend architecture.
- Build dependency graphs.
- Build knowledge graphs.
- Generate documentation.
- Explain application behavior.
- Answer developer questions using evidence.
- Visualize architecture.
- Suggest improvements.
- Detect security issues.
- Detect performance bottlenecks.

Every explanation must reference collected evidence rather than relying on assumptions.

## Multi-Agent Architecture

Dex is designed as a multi-agent system.

### Coordinator Agent

Plans exploration tasks and coordinates specialist agents.

### UI Agent

Explores pages, detects components, captures DOM, detects layouts, and discovers reusable UI patterns.

### Navigation Agent

Clicks controls, follows menus, explores routes, records user flows, and builds navigation graphs.

### Network Agent

Captures REST APIs, GraphQL, WebSockets, request headers, responses, and endpoint groups.

### Framework Agent

Detects technologies such as React, Vue, Angular, Next.js, Nuxt, Svelte, Tailwind, Bootstrap, Redux, and Zustand.

### Architecture Agent

Generates component hierarchies, layered architecture views, dependency graphs, module relationships, and service interactions.

### Security Agent

Analyzes authentication flows, JWT usage, local storage, cookies, CSP, CORS, sensitive endpoints, exposed secrets, and missing protections.

### Performance Agent

Analyzes bundle sizes, lazy loading, render performance, network waterfalls, duplicate requests, and unused assets.

### Documentation Agent

Generates README files, architecture documentation, API documentation, component documentation, and onboarding guides.

### Reasoning Agent

Answers developer questions using structured evidence collected by the other agents.

## Evidence Pipeline

Dex should avoid sending raw application data directly to an LLM. Instead, it should transform observations into structured evidence first.

```text
Application
  -> Browser Exploration
  -> DOM Extraction
  -> Runtime Analysis
  -> Network Capture
  -> Knowledge Graph
  -> Embeddings
  -> Retriever
  -> Reasoning Agent
  -> Final Answer
```

## User Interface

Dex should provide a modern dark dashboard containing:

- Live browser session.
- Navigation graph.
- Knowledge graph.
- API explorer.
- Component explorer.
- Security dashboard.
- Performance dashboard.
- Documentation panel.
- AI reasoning panel.

Everything should update live as Dex explores the application.
