# Progress Tracking & LLM I/O Visibility

## Overview

The agent now includes comprehensive progress tracking with real-time visibility into:
- **Node execution progress** - See which nodes are running and how long they take
- **LLM I/O** - View prompts sent to Gemini and responses received
- **Color-coded output** - Easy-to-read terminal output with visual indicators
- **Timing information** - Duration for each node and LLM call

## Features

### Visual Progress Indicators

```
================================================================================
  🚀 Campaign Agent Execution Started
================================================================================

[1] Load Context
────────────────────────────────────────────────────────────────────────────────
✓ Completed in 0.52s
  → Loaded existing project: my-campaign-001

[2] Analyze Files
────────────────────────────────────────────────────────────────────────────────
✓ Completed in 1.23s
  → Analyzed data.csv: historical, 1500 rows

[3] Router
────────────────────────────────────────────────────────────────────────────────
  🤖 LLM Call: Router Decision
  Prompt: You are an intelligent router for a campaign optimization agent...
  ✓ LLM Response in 2.34s
  Response: {"decision": "initialize", "reasoning": "New project detected..."...
✓ Completed in 2.45s
  → Router decision: initialize
```

### Color Coding

- **Blue** - Node headers and structure
- **Green** - Success messages and completions
- **Magenta** - LLM operations
- **Yellow** - Warnings
- **Red** - Errors
- **Gray** - Supplementary information

### LLM Call Tracking

Every LLM call shows:
1. **Task name** - What the LLM is doing (e.g., "Strategy & Insights Generation")
2. **Prompt preview** - First 200 characters of the prompt
3. **Duration** - Time taken to get response
4. **Response preview** - First 200 characters of the response

## Usage

### Basic Usage (Automatic)

Progress tracking is enabled by default when you run the CLI:

```bash
cd /Users/liangwang/adronaut-agent
python cli.py run --project-id my-campaign
```

### Programmatic Usage

If you're using the agent programmatically:

```python
from src.agent.graph import get_campaign_agent
from src.agent.state import create_initial_state
from src.utils.progress import get_progress_tracker

# Initialize tracker
tracker = get_progress_tracker()
tracker.start()

# Create and run agent
state = create_initial_state(project_id="...", uploaded_files=[...])
agent = get_campaign_agent()
final_state = agent.invoke(state)

# Finish tracking
tracker.finish()
```

### Disable Progress Tracking

To run without progress output:

```python
from src.utils.progress import set_verbose

# Disable verbose output
set_verbose(False)
```

## LLM Tasks Tracked

The following LLM operations are tracked with descriptive names:

| Task Name | Temperature | Purpose |
|-----------|-------------|---------|
| Router Decision | 0.3 | Decides next workflow step |
| Strategy & Insights Generation | 0.7 | Creates campaign strategy |
| Campaign Configuration | 0.5 | Generates platform configs |
| Adjusted Campaign Configuration | 0.5 | Updates config with patches |
| Performance Analysis | 0.3 | Analyzes experiment results |
| Optimization Patch Generation | 0.6 | Creates optimization patches |

## Architecture

### Components

1. **ProgressTracker** (`src/utils/progress.py`)
   - Main tracking class
   - Handles node and LLM call timing
   - Formats colored terminal output

2. **Node Decorator** (`src/agent/nodes.py`, `src/agent/router.py`)
   - `@track_node` decorator wraps all node functions
   - Automatically tracks node start/end
   - Captures execution time

3. **Gemini Client Integration** (`src/llm/gemini.py`)
   - Updated `generate_json()` and `generate_text()` methods
   - Logs LLM call start/end with timing
   - Shows prompt and response previews

4. **Module Integration** (`src/modules/*.py`)
   - All module LLM calls pass meaningful `task_name` parameter
   - Enables descriptive progress output

### Lazy Loading

The progress tracker uses lazy importing to avoid circular dependencies:

```python
def _get_progress_tracker():
    """Lazy import to avoid circular dependency"""
    try:
        from ..utils.progress import get_progress_tracker
        return get_progress_tracker()
    except ImportError:
        return None
```

This means the progress tracker is optional - if it's not available, the system continues without progress tracking.

## Example Output

Here's what you'll see when running the agent:

```
================================================================================
  🚀 Campaign Agent Execution Started
================================================================================

[1] Load Context
────────────────────────────────────────────────────────────────────────────────
✓ Completed in 0.12s
  → New project: 8f7a2b1c-4e3d-9a5f-1b2c-3d4e5f6a7b8c

[2] Analyze Files
────────────────────────────────────────────────────────────────────────────────
✓ Completed in 0.85s
  → Analyzed historical_data.csv: historical, 1245 rows

[3] Router
────────────────────────────────────────────────────────────────────────────────
  🤖 LLM Call: Router Decision
  Prompt: You are an intelligent router for a campaign optimization agent. Your job is to analyze the current project st...
  ✓ LLM Response in 1.87s
  Response: {"decision": "initialize", "reasoning": "This is a new project with historical data. We should start by col...
✓ Completed in 1.92s
  → Router decision: initialize

[4] Data Collection
────────────────────────────────────────────────────────────────────────────────
  ℹ Web search skipped: No Tavily API key
✓ Completed in 0.34s
  → Data collection completed

[5] Insight
────────────────────────────────────────────────────────────────────────────────
  🤖 LLM Call: Strategy & Insights Generation
  Prompt: You are an expert campaign strategist specializing in digital advertising optimization. Your job is to analyz...
  ✓ LLM Response in 8.45s
  Response: {"insights": {"patterns": ["CTR varies significantly by platform", "Mobile performs 30% better than deskt...
✓ Completed in 8.52s
  → Strategy and experiment plan generated

[6] Campaign Setup
────────────────────────────────────────────────────────────────────────────────
  🤖 LLM Call: Campaign Configuration
  Prompt: You are an expert in digital advertising campaign configuration. Your job is to convert strategic recommendat...
  ✓ LLM Response in 6.12s
  Response: {"tiktok": {"campaign_name": "Product Launch - TikTok", "objective": "CONVERSIONS", "daily_budget": 300.0...
✓ Completed in 6.18s
  → Campaign configuration generated

[7] Save
────────────────────────────────────────────────────────────────────────────────
✓ Completed in 0.28s
  → State saved to database

================================================================================
  ✓ Execution Complete
  Total time: 18.23s
  Nodes executed: 7
================================================================================
```

## Customization

### Custom Task Names

When adding new LLM calls, always provide a descriptive `task_name`:

```python
response = gemini.generate_json(
    prompt=prompt,
    system_instruction=system_instruction,
    temperature=0.5,
    task_name="My Custom Task",  # Descriptive name shown in progress
)
```

### Custom Progress Messages

Log custom messages at different levels:

```python
from src.utils.progress import get_progress_tracker

tracker = get_progress_tracker()

tracker.log_message("Processing data...", "info")
tracker.log_message("Success!", "success")
tracker.log_message("Warning: Low confidence", "warning")
tracker.log_message("Error occurred", "error")
tracker.log_message("Debug info", "debug")
```

## Benefits

1. **Transparency** - See exactly what the agent is doing at each step
2. **Debugging** - Quickly identify slow nodes or failed LLM calls
3. **User Experience** - Users know the system is working and not stuck
4. **Performance Analysis** - Timing data helps identify optimization opportunities
5. **LLM Visibility** - Understand what prompts are sent and what responses come back

## Future Enhancements

Potential improvements:
- [ ] Save progress logs to file
- [ ] Add progress bars for long-running operations
- [ ] Web dashboard for real-time monitoring
- [ ] Token usage tracking per LLM call
- [ ] Cost estimation based on token usage
- [ ] Export logs in JSON format for analysis
