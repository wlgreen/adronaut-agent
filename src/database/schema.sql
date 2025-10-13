-- Campaign Setup Agent Database Schema
-- Run this in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Projects table: Main persistent state for all campaigns
CREATE TABLE projects (
    project_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Project metadata
    project_name TEXT,
    product_description TEXT,
    target_budget DECIMAL(10, 2),

    -- State tracking
    current_phase TEXT DEFAULT 'initialized',
    -- Possible values: 'initialized', 'strategy_built', 'awaiting_results', 'optimizing', 'completed'
    iteration INT DEFAULT 0,

    -- Accumulated data
    historical_data JSONB DEFAULT '{}',
    market_data JSONB DEFAULT '{}',
    user_inputs JSONB DEFAULT '{}',
    knowledge_facts JSONB DEFAULT '{}',  -- Discovery system: facts with confidence scores and sources

    -- Strategy & experiments
    current_strategy JSONB DEFAULT '{}',
    experiment_plan JSONB DEFAULT '{}',
    experiment_results JSONB[] DEFAULT ARRAY[]::JSONB[],

    -- Campaign configurations
    current_config JSONB DEFAULT '{}',
    config_history JSONB[] DEFAULT ARRAY[]::JSONB[],

    -- Decision history
    patch_history JSONB[] DEFAULT ARRAY[]::JSONB[],
    metrics_timeline JSONB[] DEFAULT ARRAY[]::JSONB[],

    -- Performance tracking
    best_performers JSONB DEFAULT '{}',
    threshold_status TEXT,

    -- LangGraph checkpoint reference
    thread_id TEXT,
    last_checkpoint JSONB
);

-- Create index on user_id for faster lookups
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_projects_updated_at ON projects(updated_at DESC);

-- Sessions table: Log each interaction/session
CREATE TABLE sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    session_num INT NOT NULL,

    -- Session metadata
    uploaded_files JSONB DEFAULT '[]',
    file_analysis JSONB DEFAULT '{}',

    -- Router decision
    decision TEXT,  -- 'initialize', 'reflect', 'enrich', 'continue'
    decision_reasoning TEXT,

    -- Execution tracking
    nodes_executed TEXT[] DEFAULT ARRAY[]::TEXT[],
    execution_status TEXT DEFAULT 'running',  -- 'running', 'completed', 'failed'
    error_message TEXT,

    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes
CREATE INDEX idx_sessions_project_id ON sessions(project_id);
CREATE INDEX idx_sessions_started_at ON sessions(started_at DESC);

-- React cycles table: Audit trail for each node execution
CREATE TABLE react_cycles (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,

    -- Cycle metadata
    cycle_num INT NOT NULL,
    node_name TEXT NOT NULL,

    -- ReAct pattern components
    thought TEXT,
    action JSONB,
    observation JSONB,

    -- Execution details
    execution_time_ms INT,
    llm_tokens_used INT,

    -- Timestamp
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_react_cycles_session_id ON react_cycles(session_id);
CREATE INDEX idx_react_cycles_project_id ON react_cycles(project_id);
CREATE INDEX idx_react_cycles_timestamp ON react_cycles(timestamp DESC);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at on projects table
CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Uploaded files table: Track files in Supabase Storage with cached insights
CREATE TABLE uploaded_files (
    file_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    storage_path TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    file_type TEXT,  -- 'historical', 'experiment_results', 'enrichment'
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Cached analysis results
    file_metadata JSONB DEFAULT '{}',  -- row_count, columns, date_range
    insights_cache JSONB,  -- Cached insights from LLM analysis
    last_analyzed_at TIMESTAMP WITH TIME ZONE,

    -- Ensure unique files per project
    UNIQUE(project_id, storage_path)
);

-- Create indexes
CREATE INDEX idx_uploaded_files_project_id ON uploaded_files(project_id);
CREATE INDEX idx_uploaded_files_uploaded_at ON uploaded_files(uploaded_at DESC);
CREATE INDEX idx_uploaded_files_file_type ON uploaded_files(file_type);

-- Comments for documentation
COMMENT ON TABLE projects IS 'Main table storing complete campaign state across sessions';
COMMENT ON TABLE sessions IS 'Logs each user interaction with the agent';
COMMENT ON TABLE react_cycles IS 'Audit trail of all agent reasoning cycles';
COMMENT ON TABLE uploaded_files IS 'Track uploaded files in Supabase Storage with cached analysis and insights';

COMMENT ON COLUMN projects.current_phase IS 'Current stage of the campaign: initialized, strategy_built, awaiting_results, optimizing, completed';
COMMENT ON COLUMN projects.iteration IS 'Number of optimization iterations completed';
COMMENT ON COLUMN sessions.decision IS 'LLM router decision: initialize, reflect, enrich, continue';
COMMENT ON COLUMN uploaded_files.storage_path IS 'Path in Supabase Storage (format: project_id/filename)';
COMMENT ON COLUMN uploaded_files.insights_cache IS 'Cached LLM-generated insights to avoid re-analysis of same file';
