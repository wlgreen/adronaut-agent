-- Migration: Add knowledge_facts column to projects table
-- Run this in your Supabase SQL Editor if you have an existing database

-- Add knowledge_facts column to projects table
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS knowledge_facts JSONB DEFAULT '{}';

-- Add comment for documentation
COMMENT ON COLUMN projects.knowledge_facts IS 'Discovery system: facts with confidence scores and sources (format: {fact_key: {value, confidence, source}})';

-- Verify the column was added
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'projects' AND column_name = 'knowledge_facts';
