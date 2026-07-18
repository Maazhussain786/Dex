-- Dex — Initial database schema
-- Migration 001: Create core tables for projects, sessions, and evidence.

BEGIN;

-- -------------------------------------------------------------------
-- Projects
-- -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS projects (
    id          TEXT PRIMARY KEY,
    name        TEXT        NOT NULL,
    target_url  TEXT        NOT NULL,
    description TEXT,
    status      TEXT        NOT NULL DEFAULT 'draft',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_projects_status ON projects (status);

-- -------------------------------------------------------------------
-- Exploration Sessions
-- -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS exploration_sessions (
    id           TEXT PRIMARY KEY,
    project_id   TEXT        NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    started_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_sessions_project ON exploration_sessions (project_id);

-- -------------------------------------------------------------------
-- Evidence
-- -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS evidence (
    id            TEXT PRIMARY KEY,
    project_id    TEXT        NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    session_id    TEXT        NOT NULL REFERENCES exploration_sessions(id) ON DELETE CASCADE,
    evidence_type TEXT        NOT NULL,
    summary       TEXT        NOT NULL,
    payload       JSONB       NOT NULL DEFAULT '{}',
    collected_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_evidence_session ON evidence (session_id);
CREATE INDEX IF NOT EXISTS idx_evidence_type    ON evidence (evidence_type);

COMMIT;
