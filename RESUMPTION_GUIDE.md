# Flow Resumption & Incremental State Saving Guide

## Overview

The agent now supports **incremental state saving** and **automatic flow resumption**. This means:
- ✅ State is saved after **every node** completes
- ✅ If the agent crashes, you can **resume from the last checkpoint**
- ✅ No data loss during long-running workflows
- ✅ Complete audit trail of node execution

---

## Database Migration

Before using this feature, you must run the database migration to add flow tracking columns.

### Steps:

1. **Open Supabase SQL Editor**
   - Go to your Supabase project
   - Navigate to SQL Editor

2. **Run the Migration**
   ```sql
   -- Copy and paste contents of migrations/add_flow_tracking_columns.sql
   ```

   Or manually run:
   ```sql
   ALTER TABLE projects ADD COLUMN IF NOT EXISTS last_completed_node TEXT;
   ALTER TABLE projects ADD COLUMN IF NOT EXISTS completed_nodes TEXT[] DEFAULT ARRAY[]::TEXT[];
   ALTER TABLE projects ADD COLUMN IF NOT EXISTS flow_status TEXT DEFAULT 'not_started';
   ALTER TABLE projects ADD COLUMN IF NOT EXISTS current_executing_node TEXT;

   CREATE INDEX IF NOT EXISTS idx_projects_flow_status ON projects(flow_status);
   ```

3. **Verify Migration**
   ```sql
   SELECT column_name, data_type
   FROM information_schema.columns
   WHERE table_name = 'projects'
   AND column_name IN ('last_completed_node', 'completed_nodes', 'flow_status', 'current_executing_node');
   ```

---

## Usage

### Normal Run (First Time)

```bash
python cli.py run --project-id my-campaign-001
```

**What happens:**
- Agent runs through all nodes: `load_context → analyze_files → router → discovery → data_collection → insight → campaign_setup → save`
- State is **auto-saved after each node**
- If it crashes at any point, progress is preserved

---

### Resume from Checkpoint (After Crash)

If the agent crashed or was interrupted:

```bash
# Same command - it will detect incomplete flow automatically
python cli.py run --project-id <existing-project-uuid>
```

**What you'll see:**
```
⚠️  INCOMPLETE FLOW DETECTED
Flow status: in_progress
Last completed node: insight
Completed nodes: ['load_context', 'analyze_files', 'router', 'discovery', 'data_collection', 'insight']
✓ Will resume from last checkpoint
  (Use --restart to force a fresh start)
```

**What happens:**
- Agent loads state from database
- Skips already-completed nodes
- Resumes from `campaign_setup` (next node after `insight`)
- Continues to completion

---

### Force Restart (Ignore Checkpoint)

If you want to start fresh even though a checkpoint exists:

```bash
python cli.py run --project-id <existing-project-uuid> --restart
```

**What happens:**
- Flow tracking state is cleared
- Agent starts from beginning
- All nodes execute again

---

## Flow States

| Status | Description | Resumable? |
|--------|-------------|------------|
| `not_started` | New project, no workflow executed yet | N/A |
| `in_progress` | Workflow running or interrupted mid-execution | ✅ Yes |
| `completed` | Workflow finished successfully | No (new session starts fresh) |
| `failed` | Node threw an exception | ✅ Yes (retries from failure point) |

---

## How It Works

### 1. Auto-Save After Each Node

Every node is wrapped with the `@track_node` decorator which:
- Marks node as "currently executing"
- Executes the node logic
- On success: updates `last_completed_node`, saves state
- On failure: marks flow as "failed", saves error state

### 2. Resumption Detection

When loading a project:
- `load_context_node` checks if `flow_status == "in_progress"`
- If yes, sets `is_resuming = True`
- Router uses `get_resume_node()` to determine next node

### 3. Skip Optimization

The graph has conditional edges:
- If resuming and `analyze_files` + `router` already completed → skip directly to next node
- Avoids re-running LLM calls unnecessarily

---

## Example Scenarios

### Scenario 1: Crash During Insight Generation

**First Run:**
```bash
python cli.py run --project-id test-001
# Uploads: historical.csv
# Completes: load_context, analyze_files, router, discovery, data_collection, insight
# CRASH at campaign_setup
```

**Resume:**
```bash
python cli.py run --project-id <uuid>
# Detects incomplete flow
# Resumes at: campaign_setup
# Completes: campaign_setup, save
# ✅ Success
```

---

### Scenario 2: Failed Node with Error

**First Run:**
```bash
python cli.py run --project-id test-002
# Completes: load_context, analyze_files, router, reflection
# ERROR in adjustment_node (API timeout)
# Flow status: failed
```

**Resume:**
```bash
python cli.py run --project-id <uuid>
# Detects failed flow
# Retries from: adjustment
# If succeeds: continues to save
```

---

### Scenario 3: Multiple Sessions

**Session 1:** Upload historical data
```bash
python cli.py run --project-id campaign-x
# Completes full flow
# Flow status: completed
```

**Session 2:** Upload experiment results
```bash
python cli.py run --project-id <campaign-x-uuid>
# New session (flow_status was "completed")
# Starts fresh workflow with new data
# Router decides: "reflect"
# Executes: reflection → adjustment → save
```

---

## Debugging

### View Flow Status

After running, check the output:
```
--- Flow Status ---
Status: completed
✓ Flow completed successfully
Completed nodes (7): load_context → analyze_files → router → discovery → data_collection → insight → campaign_setup
```

### Check Database

Query Supabase directly:
```sql
SELECT
  project_id,
  flow_status,
  last_completed_node,
  completed_nodes,
  current_executing_node
FROM projects
WHERE project_id = '<your-uuid>';
```

### Common Issues

**Issue:** "Auto-save failed: knowledge_facts"
- **Cause:** Database schema doesn't have `knowledge_facts` column
- **Fix:** Run migration: `migrations/add_knowledge_facts_column.sql`

**Issue:** Resume doesn't work
- **Cause:** `flow_status` columns not added
- **Fix:** Run migration: `migrations/add_flow_tracking_columns.sql`

---

## Benefits

✅ **No Data Loss:** State saved after every node
✅ **Fast Recovery:** Resume exactly where it left off
✅ **Debugging:** See which node failed and why
✅ **Audit Trail:** Complete history of node executions
✅ **Graceful Errors:** Failed nodes don't lose all progress
✅ **Multi-Session Continuity:** Resume across multiple runs

---

## Technical Details

### Files Modified

1. **src/agent/state.py** - Added flow tracking fields
2. **src/agent/nodes.py** - Enhanced `@track_node` decorator with auto-save
3. **src/agent/router.py** - Added `get_resume_node()` for resumption routing
4. **src/agent/graph.py** - Added conditional edges for skip optimization
5. **src/database/schema.sql** - Documented new columns
6. **migrations/add_flow_tracking_columns.sql** - Migration script
7. **cli.py** - Added resume display and `--restart` flag

### State Fields

```python
last_completed_node: Optional[str]      # Last successful node
completed_nodes: List[str]              # Audit trail
flow_status: str                        # not_started | in_progress | completed | failed
current_executing_node: Optional[str]   # For debugging crashes
is_resuming: bool                       # Runtime flag
force_restart: bool                     # CLI flag
```

---

## Questions?

If you encounter issues:
1. Check that database migration ran successfully
2. Verify `flow_status` column exists in `projects` table
3. Check agent logs for auto-save messages
4. Use `--restart` to bypass resumption if needed
