-- Test Creative Results Table (OPTIONAL - NOT REQUIRED)
--
-- NOTE: The test-creative workflow runs entirely locally and does NOT require database access.
-- This schema is provided as an optional reference if you want to store test results in a database.
-- By default, test results are saved to JSON files in output/test_creatives/
--
-- Only run this schema if you specifically want database storage for test creative results.
-- Run this after the main schema.sql if needed.

-- Test creatives table: Store test creative workflow results
CREATE TABLE test_creatives (
    test_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(project_id) ON DELETE SET NULL,
    -- project_id is optional - test creatives can be standalone or linked to a project

    -- Test metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    product_description TEXT NOT NULL,
    product_image_path TEXT,

    -- Platform and targeting
    platform TEXT NOT NULL,  -- 'Meta', 'TikTok', 'Google'
    audience TEXT,
    creative_style TEXT,

    -- Workflow step results
    step1_generation JSONB DEFAULT '{}',
    -- Contains: original_prompt, copy_primary_text, copy_headline, copy_cta, hooks, technical_specs

    step2_review JSONB DEFAULT '{}',
    -- Contains: reviewed_prompt, changed (bool), review_notes

    step3_creative JSONB DEFAULT '{}',
    -- Contains: final_visual_prompt, copy variants, hooks, technical_specs, validation

    step4_rating JSONB DEFAULT '{}',
    -- Contains: overall_score, category_scores, keyword_analysis, brand_presence, strengths, weaknesses, suggestions

    -- Quick access fields (denormalized for querying)
    overall_score INT,  -- 0-100, extracted from step4_rating
    prompt_changed BOOLEAN DEFAULT false,  -- Whether review changed the prompt
    validation_passed BOOLEAN DEFAULT true,  -- Whether final creative passed validation

    -- Context tracking
    has_project_context BOOLEAN DEFAULT false,  -- Whether loaded from project context
    context_metadata JSONB DEFAULT '{}',  -- Strategy, insights, iteration from project

    -- Test parameters
    required_keywords TEXT[],
    brand_name TEXT,

    -- Full workflow result
    full_result JSONB DEFAULT '{}'  -- Complete workflow output for reference
);

-- Create indexes for common queries
CREATE INDEX idx_test_creatives_project_id ON test_creatives(project_id);
CREATE INDEX idx_test_creatives_created_at ON test_creatives(created_at DESC);
CREATE INDEX idx_test_creatives_platform ON test_creatives(platform);
CREATE INDEX idx_test_creatives_overall_score ON test_creatives(overall_score DESC);
CREATE INDEX idx_test_creatives_validation_passed ON test_creatives(validation_passed);

-- Create GIN index for JSONB fields to enable efficient querying
CREATE INDEX idx_test_creatives_step4_rating ON test_creatives USING GIN (step4_rating);
CREATE INDEX idx_test_creatives_full_result ON test_creatives USING GIN (full_result);

-- Comments for documentation
COMMENT ON TABLE test_creatives IS 'Stores results from standalone test creative workflow executions';
COMMENT ON COLUMN test_creatives.project_id IS 'Optional reference to parent project for context-aware tests';
COMMENT ON COLUMN test_creatives.step1_generation IS 'Initial LLM-generated creative prompt and copy';
COMMENT ON COLUMN test_creatives.step2_review IS 'Reviewed and upgraded prompt with change notes';
COMMENT ON COLUMN test_creatives.step3_creative IS 'Final creative output ready for image generation';
COMMENT ON COLUMN test_creatives.step4_rating IS 'LLM-based quality rating with detailed scores';
COMMENT ON COLUMN test_creatives.overall_score IS 'Denormalized score (0-100) for quick filtering';
COMMENT ON COLUMN test_creatives.prompt_changed IS 'Whether review step modified the original prompt';
COMMENT ON COLUMN test_creatives.validation_passed IS 'Whether final creative passed platform validation';
COMMENT ON COLUMN test_creatives.has_project_context IS 'Whether test used context from an existing project';

-- Create view for quick analysis
CREATE OR REPLACE VIEW test_creative_analytics AS
SELECT
    platform,
    COUNT(*) as total_tests,
    ROUND(AVG(overall_score), 2) as avg_score,
    ROUND(MIN(overall_score), 2) as min_score,
    ROUND(MAX(overall_score), 2) as max_score,
    SUM(CASE WHEN validation_passed THEN 1 ELSE 0 END) as passed_validation,
    SUM(CASE WHEN prompt_changed THEN 1 ELSE 0 END) as prompts_changed,
    ROUND(
        100.0 * SUM(CASE WHEN validation_passed THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) as validation_pass_rate,
    ROUND(
        100.0 * SUM(CASE WHEN prompt_changed THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) as prompt_change_rate
FROM test_creatives
GROUP BY platform;

COMMENT ON VIEW test_creative_analytics IS 'Analytics view for test creative performance by platform';
