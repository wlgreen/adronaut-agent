# Cold Start Analysis: Key Files Reference

## Core Files Analyzed

### Agent Architecture
- **`src/agent/router.py`** (152 lines)
  - Lines 33-50: Router system instructions (no cold-start distinction)
  - Lines 79-151: Router logic (treats "no data" and "has data" identically)
  - Lines 154-280: Next node routing logic

- **`src/agent/nodes.py`** (1,227 lines) 
  - Lines 95-165: `load_context_node` - Project loading and resumption detection
  - Lines 168-284: `analyze_files_node` - File analysis with caching
  - Lines 533-671: `discovery_node` - THE CRITICAL COLD START NODE
    - Lines 558: Strategy 0 - Product URL scraping
    - Lines 574: Strategy 1 - LLM inference from historical data (FAILS when no data)
    - Lines 588-602: Strategy 2 - Web search (skipped if product_description missing)
    - Lines 605-627: Strategy 3 - User input (skipped if interactive mode disabled)
  - Lines 788-878: `data_collection_node` - Metadata collection (minimal for cold start)
  - Lines 934-1032: `insight_node` - Strategy generation (empty historical data fallback)

### Strategy & Config Generation
- **`src/modules/insight.py`** (209 lines)
  - Lines 23-102: INSIGHT_PROMPT_TEMPLATE (key issue: expects historical data)
  - Lines 148-154: **KEY GAP** - Fallback to "No historical campaign data available"
  - Lines 181-209: LLM call with empty data sections

- **`src/modules/campaign.py`** (100+ lines)
  - Lines 25-100: CAMPAIGN_PROMPT_TEMPLATE (generates generic configs)

- **`src/modules/execution_planner.py`** (150+ lines)
  - Lines 28-44: EXECUTION_PLANNER_PROMPT_TEMPLATE (expects historical data)
  - "For cold start, LLM must choose without knowing conversion volume or platform differences"

### Data Processing
- **`src/modules/data_loader.py`** (359 lines)
  - Lines 56-88: File type detection (historical vs experiment_results vs enrichment)
  - Lines 184-332: `get_detailed_analysis()` - Returns empty summary for cold start
  - Lines 195-196: Empty data fallback: `{"summary": "No campaign data available"}`

- **`src/modules/url_scraper.py`** (352 lines)
  - Lines 13-37: `fetch_url()` - HTML fetching with error handling
  - Lines 40-98: `extract_structured_data()` - JSON-LD, Open Graph extraction
  - Lines 147-286: `extract_with_llm()` - **Key strength for cold start** (confidence 0.7-0.95)
  - Lines 289-351: `scrape_product_url()` - Main entry point

### State & Flow
- **`src/agent/state.py`** (150 lines)
  - Lines 75-150: `create_initial_state()` - Initial state setup
  - Fields showing cold start support:
    - Line 101: `product_urls: Optional[List[str]]` - Supports URL input
    - Line 47: `knowledge_facts` - Stores discovered facts with confidence scores
    - Line 23: `product_urls` field for URL scraping

### CLI Interface
- **`cli.py`** (1,400+ lines)
  - Lines 490-650: `run_command()` - Main CLI entry point
  - Lines 534-560: File/URL input parsing
  - Lines 535-539: **User prompt** asks for "Files or URLs (comma-separated)"

---

## Key Findings by Location

### Problem 1: Web Search Skipped for Cold Start
**File**: `src/agent/nodes.py`, lines 596-602
```python
else:
    state["messages"].append("  ⊘ Web search skipped (no Tavily API key)")
```
**Issue**: If product_description isn't provided yet, web search is never attempted for benchmarks.

### Problem 2: Generic Fallback for No Data  
**File**: `src/modules/insight.py`, lines 148-154
```python
else:
    hist_summary = "No historical campaign data available"  # ← FALLBACK
```
**Impact**: LLM receives empty data section, generates generic strategy despite prompt saying "be data-driven"

### Problem 3: No Product Categorization
**File**: `src/modules/insight.py`, lines 124
```python
product_info = state.get("user_inputs", {}).get("product_description", "Not provided")
# LLM must infer category from this description alone
```
**Gap**: No lookup table for industry benchmarks by category

### Problem 4: Minimal User Questions
**File**: `src/agent/nodes.py`, lines 606-627
```python
critical_facts = ["product_description", "target_budget"]
```
**Gap**: Only 2 questions, regardless of product type. SaaS needs different info than e-commerce.

### Problem 5: No Confidence Scoring
**Files**: `src/modules/insight.py`, `src/modules/campaign.py`
**Gap**: Output JSON contains no metadata about confidence level or data sources used.

---

## Data Flow for Cold Start

```
User Input (No historical data)
    ↓
CLI: "Files or URLs: " → discovery_node
    ↓
discovery_node execution:
    1. Check for product URLs → scrape (confidence: 0.7-0.95)
    2. Check for historical data → EMPTY
    3. Web search → SKIPPED (if no product_desc yet)
    4. User questions → asked if interactive
    ↓
data_collection_node
    ├─ No historical metadata to collect
    ├─ Tavily search optional
    └─ Mark missing facts
    ↓
insight_node
    ├─ Lookup temp historical data
    ├─ Get fallback: "No historical campaign data available"
    └─ Call LLM with empty hist_summary
    ↓
LLM generates strategy (generic)
    ↓
campaign_setup_node
    └─ Generic TikTok/Meta configs (age 18-65, broad interests)
    ↓
execution_planner
    └─ 14-day timeline with equal budget split
    ↓
Output: LOW-CONFIDENCE STRATEGY
```

---

## Files That Need Changes for Better Cold Start

### High Priority
1. **`src/config/industry_benchmarks.py`** - NEW FILE
   - Create benchmark database by category

2. **`src/agent/nodes.py`** - MODIFY
   - Reorder discovery strategies (product info first)
   - Add product categorization

3. **`src/modules/insight.py`** - MODIFY  
   - Add confidence metadata to output
   - Reference industry benchmarks in prompt

### Medium Priority
4. **`src/modules/execution_planner.py`** - MODIFY
   - Adapt timeline length to confidence score
   - Different budget allocation based on data availability

5. **`src/modules/campaign.py`** - MODIFY
   - Add campaign templates by category
   - Quick-start vs full-analysis paths

### Low Priority
6. **`cli.py`** - MODIFY
   - Optional quick-start mode
   - Better guidance for cold start users

---

## Summary of Assessment

| Aspect | Current Status | Quality | Effort to Improve |
|--------|---|---|---|
| Product URL scraping | IMPLEMENTED | 0.9/10 | None needed |
| Web search for benchmarks | IMPLEMENTED | 0.4/10 (often skipped) | 2 hours |
| LLM strategy generation | IMPLEMENTED | 0.6/10 (generic) | Hard |
| Campaign config generation | IMPLEMENTED | 0.6/10 (generic) | Medium |
| User discovery flow | IMPLEMENTED | 0.7/10 (minimal) | 4 hours |
| Product categorization | MISSING | N/A | 4 hours |
| Industry benchmarks | MISSING | N/A | 8 hours |
| Confidence scoring | MISSING | N/A | 3 hours |
| Timeline adaptation | PARTIALLY | 0.4/10 | 6 hours |
| Progressive learning | IMPLEMENTED | 0.95/10 | None needed |

