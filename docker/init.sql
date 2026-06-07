-- Agent Platform metadata schema

CREATE TABLE IF NOT EXISTS sessions (
    session_id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS workflows (
    request_id UUID PRIMARY KEY,
    session_id UUID REFERENCES sessions(session_id),
    status VARCHAR(50) NOT NULL,
    query TEXT NOT NULL,
    state JSONB DEFAULT '{}',
    total_tokens INTEGER DEFAULT 0,
    total_cost_usd DECIMAL(10, 6) DEFAULT 0,
    latency_ms DECIMAL(10, 2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    event_type VARCHAR(100) NOT NULL,
    actor VARCHAR(100) NOT NULL,
    request_id UUID,
    details JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS agent_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID REFERENCES workflows(request_id),
    agent_name VARCHAR(100) NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    latency_ms DECIMAL(10, 2) DEFAULT 0,
    success BOOLEAN DEFAULT TRUE,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_workflows_session ON workflows(session_id);
CREATE INDEX idx_audit_request ON audit_log(request_id);
CREATE INDEX idx_agent_exec_request ON agent_executions(request_id);
