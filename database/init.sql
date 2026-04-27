-- DFIReballz Database Schema
-- PostgreSQL 16 with pgcrypto

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ─── Cases ──────────────────────────────────────────────────────────

CREATE TABLE cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_number VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    case_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'open',
    classification VARCHAR(20) DEFAULT 'confidential',
    investigator VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_cases_case_type ON cases(case_type);
CREATE INDEX idx_cases_created_at ON cases(created_at DESC);

-- ─── Evidence ───────────────────────────────────────────────────────

CREATE TABLE evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    filename VARCHAR(500) NOT NULL,
    filepath VARCHAR(1000) NOT NULL,
    file_type VARCHAR(100),
    sha256 VARCHAR(64) NOT NULL,
    md5 VARCHAR(32),
    sha1 VARCHAR(40),
    size_bytes BIGINT,
    acquired_at TIMESTAMPTZ DEFAULT NOW(),
    acquired_by VARCHAR(100),
    acquisition_method VARCHAR(100),
    notes TEXT,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_evidence_case_id ON evidence(case_id);
CREATE INDEX idx_evidence_sha256 ON evidence(sha256);

-- ─── Chain of Custody Log ───────────────────────────────────────────

CREATE TABLE chain_of_custody_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evidence_id UUID REFERENCES evidence(id),
    case_id UUID REFERENCES cases(id),
    action VARCHAR(100) NOT NULL,
    actor VARCHAR(100) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    tool_used VARCHAR(200),
    tool_version VARCHAR(50),
    input_hash VARCHAR(64),
    output_hash VARCHAR(64),
    notes TEXT,
    mcp_tool_call JSONB
);

CREATE INDEX idx_coc_evidence_id ON chain_of_custody_log(evidence_id);
CREATE INDEX idx_coc_case_id ON chain_of_custody_log(case_id);
CREATE INDEX idx_coc_timestamp ON chain_of_custody_log(timestamp DESC);

-- Immutable CoC: prevent UPDATE and DELETE
CREATE OR REPLACE FUNCTION prevent_coc_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Chain of custody log entries are immutable. UPDATE and DELETE operations are prohibited.';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER coc_no_update
    BEFORE UPDATE ON chain_of_custody_log
    FOR EACH ROW
    EXECUTE FUNCTION prevent_coc_modification();

CREATE TRIGGER coc_no_delete
    BEFORE DELETE ON chain_of_custody_log
    FOR EACH ROW
    EXECUTE FUNCTION prevent_coc_modification();

-- ─── AI Tool Invocations (audit log for AI-driven tool execution) ──
-- Records every MCP tool call made by an AI host (Claude Code, ChatGPT
-- via mcpo, MCPHost+Ollama, …) so reviewers can verify, after the fact,
-- exactly what the AI did, when, with what inputs, and what came back.
-- Like chain_of_custody_log, rows are immutable once written.

CREATE TABLE ai_tool_invocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id),
    evidence_id UUID REFERENCES evidence(id),
    session_id VARCHAR(100),
    ai_actor VARCHAR(100) NOT NULL,
    mcp_server VARCHAR(100) NOT NULL,
    tool_name VARCHAR(200) NOT NULL,
    tool_args JSONB,
    input_sha256 VARCHAR(64),
    output_sha256 VARCHAR(64),
    exit_code INTEGER,
    duration_ms INTEGER,
    stdout_preview TEXT,
    stderr_preview TEXT,
    error TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    finished_at TIMESTAMPTZ
);

CREATE INDEX idx_ai_inv_case_id ON ai_tool_invocations(case_id);
CREATE INDEX idx_ai_inv_session_id ON ai_tool_invocations(session_id);
CREATE INDEX idx_ai_inv_started_at ON ai_tool_invocations(started_at DESC);
CREATE INDEX idx_ai_inv_tool_name ON ai_tool_invocations(tool_name);
CREATE INDEX idx_ai_inv_actor ON ai_tool_invocations(ai_actor);

-- Immutability: once an AI tool invocation is logged it cannot be
-- modified or deleted. Uses a dedicated function so the error message
-- correctly identifies the audit log (the CoC function's message would
-- be misleading for this table).
CREATE OR REPLACE FUNCTION prevent_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION
        'AI invocation log entries are immutable. UPDATE/DELETE on % is prohibited.',
        TG_TABLE_NAME;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ai_inv_no_update
    BEFORE UPDATE ON ai_tool_invocations
    FOR EACH ROW
    EXECUTE FUNCTION prevent_audit_modification();

CREATE TRIGGER ai_inv_no_delete
    BEFORE DELETE ON ai_tool_invocations
    FOR EACH ROW
    EXECUTE FUNCTION prevent_audit_modification();

-- ─── IOCs ───────────────────────────────────────────────────────────

CREATE TABLE iocs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    ioc_type VARCHAR(50) NOT NULL,
    value VARCHAR(1000) NOT NULL,
    confidence INTEGER DEFAULT 50,
    source VARCHAR(200),
    mitre_technique VARCHAR(20),
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    enrichment_data JSONB DEFAULT '{}',
    notes TEXT
);

CREATE INDEX idx_iocs_case_id ON iocs(case_id);
CREATE INDEX idx_iocs_ioc_type ON iocs(ioc_type);
CREATE INDEX idx_iocs_value ON iocs(value);

-- ─── Findings ───────────────────────────────────────────────────────

CREATE TABLE findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    finding_type VARCHAR(100),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    severity VARCHAR(20),
    evidence_ids UUID[],
    ioc_ids UUID[],
    mitre_techniques VARCHAR(20)[],
    timeline_timestamp TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    raw_output JSONB
);

CREATE INDEX idx_findings_case_id ON findings(case_id);
CREATE INDEX idx_findings_severity ON findings(severity);
CREATE INDEX idx_findings_timeline ON findings(timeline_timestamp);

-- ─── Playbook Runs ──────────────────────────────────────────────────

CREATE TABLE playbook_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id),
    playbook_name VARCHAR(200) NOT NULL,
    status VARCHAR(20) DEFAULT 'running',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    mcp_host VARCHAR(50),
    steps JSONB DEFAULT '[]',
    findings_generated UUID[],
    error_message TEXT
);

CREATE INDEX idx_playbook_runs_case_id ON playbook_runs(case_id);
CREATE INDEX idx_playbook_runs_status ON playbook_runs(status);

-- ─── API Keys (encrypted storage) ──────────────────────────────────

CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name VARCHAR(100) UNIQUE NOT NULL,
    encrypted_key BYTEA NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Updated-at trigger ─────────────────────────────────────────────

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER cases_updated_at
    BEFORE UPDATE ON cases
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER api_keys_updated_at
    BEFORE UPDATE ON api_keys
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
