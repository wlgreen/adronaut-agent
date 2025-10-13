# Contributing to Adronaut Agent

Thank you for your interest in contributing to Adronaut! This document provides guidelines and instructions for contributing to the project.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Project Architecture](#project-architecture)
5. [Making Changes](#making-changes)
6. [Testing](#testing)
7. [Pull Request Process](#pull-request-process)
8. [Coding Standards](#coding-standards)
9. [Documentation](#documentation)
10. [Communication](#communication)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of background or experience level.

### Expected Behavior

- Be respectful and considerate in all interactions
- Provide constructive feedback
- Accept constructive criticism gracefully
- Focus on what's best for the project and community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Trolling or personal attacks
- Publishing others' private information
- Other conduct that would be inappropriate in a professional setting

---

## Getting Started

### Prerequisites

Before contributing, make sure you have:

- **Python 3.10+** installed
- **Git** installed and configured
- **Supabase account** (for testing database features)
- **Gemini API key** (for testing LLM features)
- Familiarity with **LangGraph** (recommended but not required)

### Finding Issues to Work On

1. Check the [GitHub Issues](https://github.com/your-repo/issues) page
2. Look for issues labeled:
   - `good first issue` - Great for newcomers
   - `help wanted` - Maintainers need assistance
   - `bug` - Something isn't working
   - `enhancement` - New feature or improvement
3. Comment on the issue to express interest and ask questions

### Before You Start

- **Search existing issues** to avoid duplicates
- **Ask questions** if requirements are unclear
- **Discuss major changes** before implementation (open an issue first)

---

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/adronaut-agent.git
cd adronaut-agent

# Add upstream remote
git remote add upstream https://github.com/original-repo/adronaut-agent.git
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Install development dependencies (if available)
pip install -r requirements-dev.txt  # Optional
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Required environment variables:
```
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
TAVILY_API_KEY=your_tavily_key  # Optional
INTERACTIVE_MODE=true           # Optional
```

### 5. Setup Database

1. Go to your Supabase project SQL Editor
2. Run the schema: `src/database/schema.sql`
3. Verify tables created: `projects`, `sessions`, `react_cycles`
4. Create storage bucket: `campaign-files`

### 6. Verify Setup

```bash
# Test with sample data
python cli.py run --project-id test-setup
# Files: examples/sample_historical_data.csv

# Should complete without errors
```

---

## Project Architecture

### Key Directories

```
src/
├── agent/          # LangGraph workflow (graph.py, nodes.py, router.py, state.py)
├── modules/        # Business logic (insight.py, campaign.py, reflection.py, etc.)
├── database/       # Persistence (persistence.py, client.py, schema.sql)
├── storage/        # File management (file_manager.py)
├── llm/            # LLM integration (gemini.py)
└── utils/          # Utilities (progress.py)
```

### Important Files

- **`src/agent/graph.py`** - LangGraph workflow assembly
- **`src/agent/nodes.py`** - Node implementations
- **`src/agent/router.py`** - LLM-powered routing logic
- **`src/agent/state.py`** - AgentState schema
- **`src/modules/insight.py`** - Strategy generation
- **`src/modules/campaign.py`** - Config generation
- **`src/modules/reflection.py`** - Performance analysis
- **`src/llm/gemini.py`** - LLM wrapper

### Architecture Documents

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Comprehensive technical documentation
- **[CLAUDE.md](CLAUDE.md)** - Internal developer notes
- **[README.md](README.md)** - Project overview

---

## Making Changes

### 1. Create a Feature Branch

```bash
# Update your local main
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
# OR
git checkout -b fix/bug-description
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `refactor/` - Code refactoring
- `docs/` - Documentation updates
- `test/` - Test additions

### 2. Make Your Changes

Follow the appropriate guide below based on what you're changing:

#### Adding a New Node

**File:** `src/agent/nodes.py`

```python
from ..utils.progress import track_node

@track_node
def my_new_node(state: AgentState) -> AgentState:
    """
    Brief description of what this node does

    Input: What state fields this node reads
    Output: What state fields this node updates
    """
    # 1. Extract inputs from state
    input_data = state.get("some_field")

    # 2. Call business logic module (if complex logic)
    from ..modules.my_module import my_function
    result = my_function(input_data)

    # 3. Update state
    state["output_field"] = result
    state["messages"].append("My new node completed successfully")

    # 4. Handle errors gracefully
    try:
        # risky operation
        pass
    except Exception as e:
        state["errors"].append(f"Error in my_new_node: {str(e)}")

    return state
```

**Then add to graph** in `src/agent/graph.py`:

```python
workflow.add_node("my_new_node", my_new_node)
workflow.add_edge("previous_node", "my_new_node")
workflow.add_edge("my_new_node", "next_node")
```

#### Adding a New LLM Task

**File:** `src/modules/my_module.py`

```python
from ..llm.gemini import get_gemini

# Define prompt template
MY_TASK_PROMPT = """
Your instructions here...

Context:
{context}

Respond with JSON in this format:
{{
  "field1": "value",
  "field2": [...]
}}
"""

SYSTEM_INSTRUCTION = """
You are an expert in...

Key principles:
- Principle 1
- Principle 2
"""

def my_llm_task(context: Dict) -> Dict:
    """
    Description of task

    Args:
        context: Input data

    Returns:
        Structured output from LLM
    """
    gemini = get_gemini()

    prompt = MY_TASK_PROMPT.format(context=json.dumps(context))

    result = gemini.generate_json(
        prompt=prompt,
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.5,  # Choose based on task (0.3=precise, 0.7=creative)
        task_name="My Task Name"
    )

    return result
```

#### Modifying Database Schema

**File:** `src/database/schema.sql`

```sql
-- Add new column to projects table
ALTER TABLE projects
ADD COLUMN new_field JSONB DEFAULT '{}';

-- Create index if needed
CREATE INDEX idx_projects_new_field ON projects USING GIN (new_field);
```

**Important:** Also update:
- `src/agent/state.py` - Add field to `AgentState`
- `src/database/persistence.py` - Update `state_to_project_dict()` and `load_project_into_state()`

#### Adding a New Module

**File:** `src/modules/my_new_module.py`

```python
"""
Module description

This module handles...
"""

from typing import Dict, Any
import json

def my_function(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Function description

    Args:
        input_data: Description of input

    Returns:
        Description of output

    Example:
        >>> result = my_function({"key": "value"})
        >>> print(result)
        {"output": "result"}
    """
    # Pure function: no side effects, no state mutations
    # All logic should be testable independently

    result = {}
    # ... implementation ...
    return result
```

### 3. Write Tests

**File:** `tests/test_my_feature.py` (create tests/ directory if needed)

```python
import pytest
from src.agent.state import create_initial_state
from src.agent.nodes import my_new_node

def test_my_new_node():
    """Test my_new_node with valid input"""
    # Arrange
    state = create_initial_state(
        project_id="test-project",
        uploaded_files=[]
    )
    state["some_field"] = "test_value"

    # Act
    result = my_new_node(state)

    # Assert
    assert "output_field" in result
    assert len(result["messages"]) > 0
    assert result["output_field"] == "expected_value"

def test_my_new_node_error_handling():
    """Test my_new_node handles errors gracefully"""
    state = create_initial_state(
        project_id="test-project",
        uploaded_files=[]
    )
    state["some_field"] = None  # Invalid input

    result = my_new_node(state)

    assert len(result["errors"]) > 0
    assert "Error in my_new_node" in result["errors"][0]
```

Run tests:
```bash
pytest tests/
```

### 4. Update Documentation

If your change affects:
- **User-facing behavior** → Update README.md
- **Architecture** → Update ARCHITECTURE.md
- **API/functions** → Update docstrings
- **Examples** → Add to examples/ directory

### 5. Commit Your Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "Add feature: description of what you added

- Detailed point 1
- Detailed point 2
- Closes #issue_number"
```

Commit message format:
```
<type>: <short summary>

<detailed description>

<footer>
```

Types:
- `feat:` - New feature
- `fix:` - Bug fix
- `refactor:` - Code refactoring
- `docs:` - Documentation changes
- `test:` - Test additions
- `chore:` - Maintenance tasks

---

## Testing

### Manual Testing

```bash
# Test initialize path
python cli.py run --project-id test-init
# Files: examples/sample_historical_data.csv

# Test reflect path
python cli.py run --project-id test-init
# Files: examples/sample_experiment_results.csv

# Verify output
cat campaign_test-init_v0.json
cat campaign_test-init_v1.json
```

### Unit Testing

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_my_feature.py

# Run with coverage
pytest --cov=src tests/
```

### Integration Testing

```bash
# Test full workflow with sample data
python cli.py run --project-id integration-test
# Verify database state in Supabase
```

### Linting

```bash
# Format code
black src/

# Check types
mypy src/

# Lint
flake8 src/
```

---

## Pull Request Process

### 1. Push Your Branch

```bash
git push origin feature/your-feature-name
```

### 2. Create Pull Request

1. Go to GitHub and click "New Pull Request"
2. Select your branch
3. Fill out the PR template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Changes Made
- Detailed list of changes
- What was added/modified/removed

## Testing
- How you tested these changes
- Test cases covered

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-reviewed code
- [ ] Commented complex code
- [ ] Updated documentation
- [ ] Added tests
- [ ] All tests pass
- [ ] No new warnings

## Related Issues
Closes #issue_number
```

### 3. Code Review

- Maintainers will review your PR
- Address feedback by pushing new commits
- Engage in discussion constructively
- Make requested changes

### 4. Merge

Once approved:
- Maintainer will merge your PR
- Your contribution will be included in the next release
- Celebrate! 🎉

---

## Coding Standards

### Python Style

- Follow **PEP 8** style guide
- Use **type hints** for function arguments and returns
- Maximum line length: **88 characters** (Black default)
- Use **docstrings** for all modules, classes, and functions

### Docstring Format

```python
def my_function(arg1: str, arg2: int) -> Dict[str, Any]:
    """
    Brief one-line description

    Longer description if needed, explaining:
    - What the function does
    - When to use it
    - Any important notes

    Args:
        arg1: Description of arg1
        arg2: Description of arg2

    Returns:
        Description of return value

    Raises:
        ValueError: When this error occurs

    Example:
        >>> result = my_function("test", 42)
        >>> print(result)
        {"key": "value"}
    """
    pass
```

### Code Organization

- **Nodes** (in `nodes.py`): Orchestration only, minimal logic
- **Modules** (in `modules/`): Pure functions, testable
- **No circular imports**: Use relative imports carefully
- **Error handling**: Graceful degradation, no crashes

### State Management

- **Read-only state access**: `state.get("field", default)`
- **Explicit state updates**: `state["field"] = value`
- **Clear messages**: `state["messages"].append("Clear description")`
- **Error logging**: `state["errors"].append("Error: description")`

### LLM Best Practices

- **Clear prompts**: Be specific and provide examples
- **Appropriate temperature**: 0.3 for analysis, 0.7 for creativity
- **Structured output**: Use JSON mode for consistency
- **Error handling**: Retry on failure, fallback gracefully
- **Task names**: Descriptive for progress tracking

---

## Documentation

### What to Document

- **All new features**: User-facing behavior
- **All bug fixes**: What was broken, how it's fixed
- **API changes**: Breaking changes especially
- **Architecture changes**: Design decisions
- **Complex code**: Inline comments for non-obvious logic

### Where to Document

| Change | Document Here |
|--------|---------------|
| New feature | README.md + docstrings + ARCHITECTURE.md |
| Bug fix | Commit message + issue comment |
| API change | Docstrings + ARCHITECTURE.md |
| Architecture | ARCHITECTURE.md + code comments |
| User guide | README.md + examples/ |

### Documentation Style

- **Be concise** but complete
- **Use examples** to illustrate concepts
- **Link related docs** for context
- **Update promptly** when code changes

---

## Communication

### GitHub Issues

- **Bug reports**: Use issue template, include reproduction steps
- **Feature requests**: Describe use case and expected behavior
- **Questions**: Search existing issues first

### Pull Request Comments

- **Be respectful** and constructive
- **Provide context** for feedback
- **Suggest alternatives** when requesting changes

### Getting Help

- **Read documentation**: ARCHITECTURE.md, README.md, code comments
- **Search issues**: Someone may have asked already
- **Ask in issues**: Open a new issue with your question

---

## Release Process

(For maintainers)

### Versioning

We use [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward-compatible)
- **PATCH**: Bug fixes

### Release Checklist

1. Update version in `setup.py` (if applicable)
2. Update CHANGELOG.md
3. Merge all PRs for release
4. Tag release: `git tag v1.2.3`
5. Push tag: `git push origin v1.2.3`
6. Create GitHub Release with notes

---

## Recognition

All contributors will be:
- Listed in CONTRIBUTORS.md (if we create one)
- Mentioned in release notes
- Acknowledged in the README

Thank you for contributing to Adronaut! 🚀

---

## License

By contributing to Adronaut, you agree that your contributions will be licensed under the MIT License.

---

## Questions?

If you have questions about contributing:
1. Check [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
2. Search [GitHub Issues](https://github.com/your-repo/issues)
3. Open a new issue with the `question` label

We appreciate your contributions and look forward to collaborating with you!
