CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS diseases (
    id BIGSERIAL PRIMARY KEY,
    canonical_name TEXT NOT NULL UNIQUE,
    synonyms TEXT[] NOT NULL DEFAULT '{}',
    identifiers JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS evidence_items (
    id TEXT PRIMARY KEY,
    disease_id BIGINT REFERENCES diseases(id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    source_id TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    url TEXT NOT NULL DEFAULT '',
    evidence_type TEXT NOT NULL,
    targets TEXT[] NOT NULL DEFAULT '{}',
    drugs TEXT[] NOT NULL DEFAULT '{}',
    confidence NUMERIC(4, 3) NOT NULL DEFAULT 0,
    raw_payload JSONB NOT NULL DEFAULT '{}',
    embedding vector(1536),
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS analysis_runs (
    id UUID PRIMARY KEY,
    disease_id BIGINT REFERENCES diseases(id) ON DELETE SET NULL,
    input_text TEXT NOT NULL,
    mode TEXT NOT NULL DEFAULT 'demo',
    model_version TEXT,
    result_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS drug_candidates (
    id BIGSERIAL PRIMARY KEY,
    analysis_run_id UUID REFERENCES analysis_runs(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    mechanism TEXT NOT NULL,
    candidate_type TEXT NOT NULL,
    evidence_ids TEXT[] NOT NULL DEFAULT '{}',
    score_breakdown JSONB NOT NULL DEFAULT '{}',
    overall_score NUMERIC(5, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_evidence_items_disease_id ON evidence_items(disease_id);
CREATE INDEX IF NOT EXISTS idx_evidence_items_source ON evidence_items(source, source_id);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_created_at ON analysis_runs(created_at);
