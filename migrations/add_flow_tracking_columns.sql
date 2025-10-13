-- Migration: Add flow tracking columns for incremental state saving and resumption
-- Date: 2025-10-13
-- Purpose: Enable auto-save after each node and resume from last checkpoint

-- Add flow tracking columns to projects table
ALTER TABLE projects ADD COLUMN IF NOT EXISTS last_completed_node TEXT;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS completed_nodes TEXT[] DEFAULT ARRAY[]::TEXT[];
ALTER TABLE projects ADD COLUMN IF NOT EXISTS flow_status TEXT DEFAULT 'not_started';
ALTER TABLE projects ADD COLUMN IF NOT EXISTS current_executing_node TEXT;

-- Add index for flow_status for faster queries
CREATE INDEX IF NOT EXISTS idx_projects_flow_status ON projects(flow_status);

-- Add comments for documentation
COMMENT ON COLUMN projects.last_completed_node IS 'Last successfully completed node in the workflow';
COMMENT ON COLUMN projects.completed_nodes IS 'Ordered array of all completed nodes for audit trail';
COMMENT ON COLUMN projects.flow_status IS 'Current flow status: not_started, in_progress, completed, failed';
COMMENT ON COLUMN projects.current_executing_node IS 'Node currently being executed (for debugging)';
