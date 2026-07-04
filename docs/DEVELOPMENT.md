# Dex Development Guide

## Prerequisites

- Git
- Python 3.11 or newer
- Node.js 22 or newer
- Docker Desktop

## Environment

Copy `.env.example` to `.env` for local development and fill in secrets such as `OPENAI_API_KEY`.

## Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

The API listens on `http://localhost:8000`.

Useful endpoints:

- `GET /health`
- `POST /projects`
- `GET /projects`

## Frontend

```bash
cd frontend
npm install
npm run dev
```

The dashboard listens on `http://localhost:3000`.

On Windows PowerShell, if script execution blocks `npm.ps1`, run commands through `npm.cmd` or adjust your execution policy.

## Full Local Stack

```bash
docker compose up --build
```

Services:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- PostgreSQL: `localhost:5432`
- Neo4j browser: `http://localhost:7474`
- Qdrant: `http://localhost:6333`

## Current Verification

The current repository has been verified with:

```bash
python -m compileall backend/app backend/tests
node -e "JSON.parse(require('fs').readFileSync('frontend/package.json','utf8'))"
```

Full backend tests and frontend builds require installing project dependencies.
