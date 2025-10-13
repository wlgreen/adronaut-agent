# Adronaut Agent - UI Design Document

**Version:** 1.0
**Date:** 2025-10-13
**Purpose:** High-level design specification for building a web-based UI for the Adronaut campaign optimization agent

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Core User Workflows](#core-user-workflows)
3. [Data Architecture](#data-architecture)
4. [Screen Architecture](#screen-architecture)
5. [Component Library](#component-library)
6. [State Management](#state-management)
7. [API Integration](#api-integration)
8. [Visual Design System](#visual-design-system)
9. [Real-time Updates](#real-time-updates)
10. [Technical Recommendations](#technical-recommendations)

---

## 1. System Overview

### What is Adronaut?

Adronaut is an AI-powered campaign optimization agent that:
- Analyzes historical advertising data
- Generates intelligent campaign strategies
- Creates platform-specific configurations (TikTok, Meta)
- Continuously optimizes based on experiment results
- Learns from each iteration to improve performance

### Key Capabilities

1. **Multi-Session Continuity**: Projects persist across sessions with full state restoration
2. **Flexible Execution Timelines**: Adaptive 7-30 day test plans based on complexity
3. **LLM-Powered Decision Making**: Gemini 2.0 Flash drives all strategic decisions
4. **Data-Driven Insights**: Extracts patterns from historical performance data
5. **Automated Optimization**: Generates patches and new configs based on results

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Web UI (React)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Projects │  │ Sessions │  │ Strategy │  │ Timeline │   │
│  │   View   │  │   View   │  │   View   │  │   View   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                    Backend API (FastAPI)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Auth   │  │ Projects │  │ Sessions │  │  Files   │   │
│  │   API    │  │   API    │  │   API    │  │   API    │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                   LangGraph Agent (Core)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Router  │→ │Discovery │→ │ Insight  │→ │ Campaign │   │
│  │   Node   │  │   Node   │  │   Node   │  │   Setup  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
│  ┌──────────┐  ┌──────────┐                                │
│  │Reflection│→ │Adjustment│→ Save                          │
│  │   Node   │  │   Node   │                                │
│  └──────────┘  └──────────┘                                │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                   Data Layer (Supabase)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Projects │  │ Sessions │  │  React   │  │ Uploaded │   │
│  │  Table   │  │  Table   │  │  Cycles  │  │  Files   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
│                    Supabase Storage (Files)                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Core User Workflows

### Workflow 1: Create New Campaign (Initialize Path)

**User Journey:**
1. User lands on dashboard → clicks "New Project"
2. Fills project form (name, description, budget)
3. Uploads historical data CSV(s)
4. Agent analyzes data → generates strategy → creates timeline → produces config
5. User reviews strategy and timeline → downloads config

**States & Transitions:**
```
Project Creation → File Upload → Agent Running → Strategy Review → Config Ready
     (form)         (dropzone)     (progress)      (dashboard)      (download)
```

**Key UI Moments:**
- **Upload**: Drag-and-drop with file validation and preview
- **Processing**: Real-time node execution progress with LLM activity logs
- **Strategy**: Interactive cards showing insights, audience, creative, platform split
- **Timeline**: Gantt-style visualization with phases, checkpoints, and combinations
- **Config**: JSON viewer with platform tabs (TikTok/Meta) and copy buttons

---

### Workflow 2: Upload Experiment Results (Reflect Path)

**User Journey:**
1. User opens existing project → sees current iteration
2. Clicks "Upload Results" → uploads experiment CSV
3. Agent analyzes performance → identifies winners/losers → generates optimization patch
4. User reviews reflection analysis → sees new adjusted config
5. Downloads v2 config and repeats

**States & Transitions:**
```
Project Dashboard → Upload Results → Agent Running → Reflection View → New Config
   (iteration N)      (dropzone)       (progress)     (performance)    (iteration N+1)
```

**Key UI Moments:**
- **Performance Dashboard**: Metrics timeline showing CPA/ROAS trends across iterations
- **Comparison View**: Side-by-side diff of old vs new config with highlighted changes
- **Patch History**: Accordion showing all optimization decisions with reasoning
- **Winners/Losers**: Table with color-coded performance vs thresholds

---

### Workflow 3: Browse Projects & History

**User Journey:**
1. User lands on dashboard → sees all projects
2. Filters by phase/status → clicks project card
3. Views project timeline → sees all sessions
4. Clicks session → sees detailed execution log

**States & Transitions:**
```
Dashboard → Project List → Project Detail → Session Detail → Node Logs
  (grid)      (filtered)     (timeline)       (steps)        (audit trail)
```

---

## 3. Data Architecture

### Core Data Models

#### Project (Main Entity)
```typescript
interface Project {
  // Identity
  project_id: string;              // UUID
  user_id: string;
  project_name: string;
  product_description: string;
  target_budget: number;

  // State
  current_phase: 'initialized' | 'strategy_built' | 'awaiting_results' | 'optimizing' | 'completed';
  iteration: number;               // 0 = initial, 1+ = optimization cycles

  // Timestamps
  created_at: string;
  updated_at: string;

  // Accumulated Data (JSONB)
  historical_data: HistoricalData;
  market_data: MarketData;
  user_inputs: Record<string, any>;
  knowledge_facts: Record<string, KnowledgeFact>;

  // Strategy & Experiments
  current_strategy: Strategy;
  experiment_plan: ExecutionTimeline;
  experiment_results: ExperimentResult[];

  // Configurations
  current_config: CampaignConfig;
  config_history: CampaignConfig[];

  // Performance
  patch_history: OptimizationPatch[];
  metrics_timeline: MetricsSnapshot[];
  best_performers: Record<string, any>;
  threshold_status: 'not_met' | 'met' | 'exceeded';
}
```

#### Session (Interaction Log)
```typescript
interface Session {
  session_id: string;
  project_id: string;
  session_num: number;

  // Files uploaded in this session
  uploaded_files: UploadedFile[];
  file_analysis: Record<string, any>;

  // Router decision
  decision: 'initialize' | 'reflect' | 'enrich' | 'continue';
  decision_reasoning: string;

  // Execution
  nodes_executed: string[];        // ['load_context', 'analyze_files', ...]
  execution_status: 'running' | 'completed' | 'failed';
  error_message?: string;

  started_at: string;
  completed_at?: string;
}
```

#### ReactCycle (Node Execution Audit)
```typescript
interface ReactCycle {
  id: number;
  session_id: string;
  project_id: string;
  cycle_num: number;
  node_name: string;

  // ReAct pattern
  thought?: string;
  action: Record<string, any>;
  observation: Record<string, any>;

  // Performance
  execution_time_ms: number;
  llm_tokens_used?: number;

  timestamp: string;
}
```

#### Strategy (LLM-Generated)
```typescript
interface Strategy {
  insights: {
    patterns: string[];            // Data-driven observations
    strengths: string[];
    weaknesses: string[];
    benchmark_comparison?: string;
  };

  target_audience: {
    primary_segments: string[];
    demographics: {
      age: string;
      gender: string;
      location: string;
    };
    interests: string[];
  };

  creative_strategy: {
    messaging_angles: string[];
    value_props: string[];
  };

  platform_strategy: {
    priorities: string[];          // ['TikTok', 'Meta']
    budget_split: Record<string, number>; // {'TikTok': 0.6, 'Meta': 0.4}
    rationale: string;
  };
}
```

#### ExecutionTimeline (Flexible Test Plan)
```typescript
interface ExecutionTimeline {
  timeline: {
    total_duration_days: number;   // 7-30 days
    reasoning: string;

    phases: Phase[];
    checkpoints: Checkpoint[];
  };

  statistical_requirements: {
    min_conversions_per_combo: number;
    confidence_level: number;
    expected_weekly_conversions?: number;
    power_analysis?: string;
  };

  risk_mitigation?: {
    early_warning_signals: string[];
    contingency_plans: string[];
  };
}

interface Phase {
  name: string;                    // "Short-term Discovery"
  duration_days: number;
  start_day: number;
  end_day: number;
  budget_allocation_percent: number;

  objectives: string[];
  test_combinations: TestCombination[];
  success_criteria: string[];

  decision_triggers: {
    proceed_if?: string;
    pause_if?: string;
    scale_if?: string;
  };
}

interface TestCombination {
  platform: string;                // 'TikTok' | 'Meta'
  audience: string;
  creative: string;
  budget_percent: number;
  rationale: string;
}

interface Checkpoint {
  day: number;
  purpose: string;
  review_focus: string[];
  action_required: boolean;
}
```

#### CampaignConfig (Platform Configs)
```typescript
interface CampaignConfig {
  summary: {
    total_daily_budget: number;
    experiment: string;
    version: number;
  };

  tiktok?: {
    daily_budget: number;
    objective: string;
    targeting: {
      age: string;
      gender: string;
      interests: string[];
    };
    creative: {
      format: string;
      angles: string[];
    };
  };

  meta?: {
    daily_budget: number;
    objective: string;
    targeting: {
      age: string;
      gender: string;
      interests: string[];
    };
    creative: {
      format: string;
      angles: string[];
    };
  };
}
```

---

## 4. Screen Architecture

### 4.1 Dashboard (Landing Page)

**Purpose:** Central hub for all projects with quick actions

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  🚀 Adronaut                    [+ New Project]  [@User]    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📊 Overview                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   5      │  │   12     │  │   3      │  │  $4.2K   │   │
│  │ Active   │  │ Total    │  │ Optimiz  │  │  Saved   │   │
│  │ Projects │  │ Projects │  │   ing    │  │   Cost   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
│  🔍 Filters: [All] [Active] [Completed]  Sort: [Recent ▼] │
│                                                              │
│  📁 Projects                                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Summer Campaign 2024            [📊 Strategy Ready] │   │
│  │ Created 2 days ago • Iteration 3 • TikTok + Meta    │   │
│  │ CPA: $23.45 (-15% vs v2) • ROAS: 3.2x              │   │
│  │ [View Details →]                                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Product Launch Q4               [⏳ Running]        │   │
│  │ Created 1 hour ago • Iteration 0 • Processing...    │   │
│  │ [View Progress →]                                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Key Components:**
- **Header**: Logo, New Project CTA, User menu
- **Stats Cards**: Active projects, total projects, optimizing, cost saved
- **Filters Bar**: Phase filters, status filters, sort dropdown
- **Project Cards**:
  - Project name + status badge
  - Metadata (created date, iteration, platforms)
  - Key metrics (CPA, ROAS with trend indicators)
  - Primary action button

**Interactions:**
- Click card → Navigate to Project Detail
- Click "New Project" → Open project creation modal
- Filter/sort → Update card list in real-time

---

### 4.2 New Project Modal

**Purpose:** Create new project and upload initial data

**Layout:**
```
┌─────────────────────────────────────────────┐
│  Create New Campaign Project          [✕]  │
├─────────────────────────────────────────────┤
│                                              │
│  Step 1 of 2: Project Details               │
│                                              │
│  Project Name *                              │
│  [_____________________________________]    │
│                                              │
│  Product Description                         │
│  [_____________________________________]    │
│  [_____________________________________]    │
│                                              │
│  Target Daily Budget *                       │
│  $ [___________]                            │
│                                              │
│              [Cancel]     [Next: Upload →]  │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  Create New Campaign Project          [✕]  │
├─────────────────────────────────────────────┤
│                                              │
│  Step 2 of 2: Upload Historical Data        │
│                                              │
│  ┌─────────────────────────────────────┐   │
│  │     📁                               │   │
│  │  Drag & drop CSV files here          │   │
│  │  or click to browse                   │   │
│  │                                       │   │
│  └─────────────────────────────────────┘   │
│                                              │
│  Uploaded Files:                             │
│  ✓ historical_q3.csv (245 KB, 1,234 rows)  │
│  ✓ benchmarks.csv (12 KB, 45 rows)         │
│                                              │
│  Expected columns: campaign_name, spend,     │
│  conversions, CPA, ROAS, platform, etc.      │
│                                              │
│          [← Back]     [Create Project →]    │
└─────────────────────────────────────────────┘
```

**Key Components:**
- **Step Indicator**: Show progress (1 of 2, 2 of 2)
- **Form Inputs**: Text inputs with validation
- **File Dropzone**: Drag-and-drop with file preview
- **File List**: Show uploaded files with size/row count
- **Navigation**: Back/Next/Cancel/Submit buttons

**Validation:**
- Project name required
- Budget must be positive number
- At least one CSV file required
- File format validation (CSV, expected columns)

---

### 4.3 Project Detail View

**Purpose:** Comprehensive view of project state, strategy, and history

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  ← Back to Projects                                          │
├─────────────────────────────────────────────────────────────┤
│  Summer Campaign 2024                    [Upload Results]   │
│  Phase: Optimizing • Iteration 3 • Updated 2 hours ago      │
├─────────────────────────────────────────────────────────────┤
│  [📊 Overview] [🎯 Strategy] [📅 Timeline] [📈 Performance] │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📊 Overview Tab                                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Current Metrics                                    │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐        │    │
│  │  │  $23.45  │  │   3.2x   │  │   847    │        │    │
│  │  │   CPA    │  │   ROAS   │  │  Conv.   │        │    │
│  │  │  -15% ↓  │  │  +22% ↑  │  │          │        │    │
│  │  └──────────┘  └──────────┘  └──────────┘        │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Metrics Timeline                                   │    │
│  │  📈 [Line chart showing CPA/ROAS across iterations] │    │
│  │     v0 ----  v1 ----  v2 ----  v3 (current)        │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Latest Configuration (v3)                          │    │
│  │  [TikTok] [Meta]                                    │    │
│  │  Daily Budget: $600 (60% of total)                 │    │
│  │  Objective: Conversions                             │    │
│  │  Targeting: 25-34, Female, Interests...            │    │
│  │  [📋 Copy JSON] [📥 Download]                       │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Session History (4 sessions)                                │
│  ┌────────────────────────────────────────────────────┐    │
│  │  ✓ Session 4 - 2 hours ago - Reflect               │    │
│  │    Uploaded: experiment_results_v2.csv              │    │
│  │    Decision: Generated optimization patch            │    │
│  │    Duration: 45s                                    │    │
│  │    [View Details →]                                 │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Tab Structure:**

**📊 Overview Tab:**
- Current metrics cards (CPA, ROAS, Conversions with trends)
- Metrics timeline chart (line chart across iterations)
- Latest configuration viewer (tabbed by platform)
- Session history accordion

**🎯 Strategy Tab:**
- Insights section (patterns, strengths, weaknesses)
- Target audience breakdown
- Creative strategy (messaging angles, value props)
- Platform strategy (priorities, budget split, rationale)

**📅 Timeline Tab:**
- Timeline visualization (Gantt-style)
- Phases breakdown (cards for each phase)
- Test combinations matrix
- Checkpoints calendar view

**📈 Performance Tab:**
- Iteration comparison table
- Patch history (all optimization decisions)
- Best performers ranking
- Config diff viewer (side-by-side v2 vs v3)

---

### 4.4 Agent Execution Progress View

**Purpose:** Real-time visibility into agent workflow execution

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  Summer Campaign 2024                                        │
│  Agent Running: Analyzing Results...                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Execution Progress                                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │  ✓ Load Context           (0.2s)                    │    │
│  │  ✓ Analyze Files          (1.3s)                    │    │
│  │  ✓ Router Decision        (2.1s)                    │    │
│  │  ⏳ Reflection Analysis    (running... 5s)          │    │
│  │     🤖 Comparing v2 vs thresholds...                │    │
│  │     📊 Analyzing 12 test combinations               │    │
│  │  ○ Generate Optimization Patch                      │    │
│  │  ○ Save State                                       │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Agent Activity Log                                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │  14:32:45  [Reflection] Starting performance...     │    │
│  │  14:32:46  [LLM] Prompt: Analyze the following...  │    │
│  │  14:32:51  [LLM] Response: Based on the data...    │    │
│  │  14:32:51  [Reflection] ✓ Found 3 winners, 2...    │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Key Components:**
- **Progress Steps**: Vertical timeline with checkmarks/spinner
- **Current Step Details**: Expanded view with sub-tasks
- **Activity Log**: Scrollable log with timestamps and categorized messages
- **Status Indicators**:
  - ✓ Completed (green)
  - ⏳ Running (blue, animated)
  - ○ Pending (gray)
  - ⚠ Warning (yellow)
  - ✕ Error (red)

**Real-time Updates:**
- WebSocket connection for live updates
- Auto-scroll log to bottom
- Estimated time remaining per step

---

### 4.5 Strategy Visualization

**Purpose:** Interactive visual representation of generated strategy

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  🎯 Strategy (v3)                                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📊 Key Insights                                             │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────┐   │
│  │  💪 Strengths  │  │  ⚠ Weaknesses  │  │  📈 Trends │   │
│  │                │  │                │  │            │   │
│  │  • TikTok had  │  │  • Meta CPA    │  │  • Female  │   │
│  │    23% lower   │  │    increased   │  │    audience│   │
│  │    CPA in Q3   │  │    15% in Aug  │  │    +40%    │   │
│  │  • UGC video   │  │  • Conversion  │  │  • Mobile  │   │
│  │    drove 3.2x  │  │    rate drop   │  │    traffic │   │
│  │    ROAS        │  │    on desktop  │  │    dominat │   │
│  └────────────────┘  └────────────────┘  └────────────┘   │
│                                                              │
│  🎯 Target Audience                                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Primary Segments: Young Professionals, Fitness...   │  │
│  │  Demographics: 25-34 • Female • Urban Areas          │  │
│  │  Interests: Wellness, Nutrition, Workout, Yoga...    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  🎨 Creative Strategy                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Messaging Angles:                                    │  │
│  │    1. "Transform your fitness journey in 30 days"    │  │
│  │    2. "Science-backed nutrition made simple"         │  │
│  │    3. "Join 50K+ users already seeing results"       │  │
│  │                                                        │  │
│  │  Value Props:                                         │  │
│  │    • Personalized meal plans                          │  │
│  │    • Expert coaching included                         │  │
│  │    • Money-back guarantee                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  📱 Platform Strategy                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Priority Platforms: TikTok (Primary), Meta (Second)  │  │
│  │                                                        │  │
│  │  Budget Allocation:                                   │  │
│  │  ████████████████████ TikTok 60%  $600/day          │  │
│  │  █████████████ Meta 40%  $400/day                    │  │
│  │                                                        │  │
│  │  Rationale: TikTok showed 23% lower CPA and higher   │  │
│  │  engagement with target demo in historical data...    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Key Components:**
- **Insight Cards**: Categorized (strengths, weaknesses, trends) with data citations
- **Audience Section**: Demographics, segments, interests in clean layout
- **Creative Strategy**: Numbered list of messaging angles and bullet points for value props
- **Platform Strategy**: Visual budget bars with percentages and rationale

**Visual Design:**
- Use color coding (green=strength, yellow=weakness, blue=trend)
- Show data citations inline (e.g., "23% lower CPA" not just "lower CPA")
- Progressive disclosure for long text (show more/less)

---

### 4.6 Execution Timeline Visualization

**Purpose:** Gantt-style view of test phases, combinations, and checkpoints

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  📅 Execution Timeline (14 Days)                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  💡 Timeline Reasoning:                                      │
│  "14-day timeline chosen to allow 2 optimization cycles     │
│   with sufficient statistical power. Budget supports 20+     │
│   conversions per combination for 90% confidence."           │
│                                                              │
│  Phases Overview:                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                      │   │
│  │  Day 1          Day 5      Day 7      Day 10   Day 14 │   │
│  │  │─── Phase 1 ───│─── Phase 2 ───│─── Phase 3 ──│   │   │
│  │     (35% budget)    (40% budget)    (25% budget)     │   │
│  │      ▼              ▼               ▼                │   │
│  │   Checkpoint    Checkpoint      Checkpoint           │   │
│  │    Day 3           Day 7          Day 12             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  Phase Details:                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  [1] SHORT-TERM DISCOVERY                            │   │
│  │  Days 1-5 (5 days) • Budget: 35%                    │   │
│  │                                                      │   │
│  │  Objectives:                                         │   │
│  │    • Identify winning platform                       │   │
│  │    • Test 3 audience segments                        │   │
│  │    • Validate UGC vs static creative                 │   │
│  │                                                      │   │
│  │  Test Combinations (3):                              │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │ [15%] TikTok + Interest + UGC Video          │  │   │
│  │  │   → Historical winner, testing scalability    │  │   │
│  │  ├──────────────────────────────────────────────┤  │   │
│  │  │ [12%] Meta + Lookalike + Static Image        │  │   │
│  │  │   → Hedge bet for audience discovery          │  │   │
│  │  ├──────────────────────────────────────────────┤  │   │
│  │  │ [8%] TikTok + Lookalike + UGC Video          │  │   │
│  │  │   → Testing interaction effect                │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  │                                                      │   │
│  │  Success Criteria:                                   │   │
│  │    ✓ CPA < $30 in at least 1 combination            │   │
│  │    ✓ ROAS > 2.5x overall                             │   │
│  │                                                      │   │
│  │  Decision Triggers:                                  │   │
│  │    → Proceed if: CPA < $30 in 2+ combos             │   │
│  │    ⚠ Pause if: CPA > $50 across all                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  [Expand Phase 2 →]  [Expand Phase 3 →]                     │
│                                                              │
│  📍 Checkpoint Schedule:                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🟡 Day 3: Early Signal Check                       │   │
│  │     Focus: Check for obvious losers, flag issues     │   │
│  │     Action Required: No (passive review)             │   │
│  │                                                      │   │
│  │  🔴 Day 7: Phase 1 Final Review                     │   │
│  │     Focus: Decide which combos to scale, which to    │   │
│  │            pause, allocate Phase 2 budget            │   │
│  │     Action Required: Yes (active decision)           │   │
│  │                                                      │   │
│  │  🟡 Day 12: Mid-Phase 3 Check                       │   │
│  │     Focus: Validate optimization patch effectiveness  │   │
│  │     Action Required: No (passive review)             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  📊 Statistical Requirements:                                │
│  Min conversions/combo: 15 • Confidence: 90%                │
│  Expected weekly conversions: 120                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Key Components:**
- **Timeline Gantt**: Horizontal bars showing phase durations with checkpoints
- **Phase Cards**: Expandable/collapsible cards for each phase
- **Combination Matrix**: Visual grid of test combinations with budget %
- **Checkpoint List**: Timeline of review points with action requirements
- **Stats Footer**: Statistical requirements summary

**Interactions:**
- Click phase bar → Expand phase details
- Hover combination → Show full rationale tooltip
- Click checkpoint → Highlight related phases

---

### 4.7 Performance Analysis & Comparison

**Purpose:** Compare iterations and visualize optimization trajectory

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  📈 Performance Analysis                                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Iteration Comparison                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Metric │  v0 (baseline) │  v1 │  v2 │  v3 (current) │  │
│  ├────────┼─────────────────┼─────┼─────┼────────────────┤  │
│  │ CPA    │ $32.10          │$28.5│$25.2│ $23.45 (-27%) │  │
│  │ ROAS   │  2.1x           │ 2.6x│ 2.9x│  3.2x (+52%)  │  │
│  │ Conv.  │  543            │ 621 │ 734 │  847 (+56%)   │  │
│  │ CTR    │  1.8%           │2.1% │2.4% │  2.7% (+50%)  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  Metrics Trend Chart                                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  $35 ┤                                                │  │
│  │      ┤  ●                                             │  │
│  │  $30 ┤     ●                                          │  │
│  │      ┤        ●                                       │  │
│  │  $25 ┤           ●  ← CPA decreasing (good)          │  │
│  │      ┤                                                │  │
│  │  $20 ┼────────────────────────────────────────────   │  │
│  │       v0      v1      v2      v3                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  Optimization Patch History                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ▼ v2 → v3: Scaling Winners + Creative Refresh       │  │
│  │     2 hours ago • Session 4                           │  │
│  │                                                        │  │
│  │     📊 Analysis:                                      │  │
│  │       • TikTok UGC combo hit $22 CPA (target: $25)   │  │
│  │       • Meta static underperformed at $38 CPA        │  │
│  │       • Female 25-34 segment 40% higher ROAS         │  │
│  │                                                        │  │
│  │     🔧 Changes Made:                                  │  │
│  │       • Increase TikTok budget 60% → 70%             │  │
│  │       • Decrease Meta budget 40% → 30%               │  │
│  │       • Narrow Meta targeting to female only         │  │
│  │       • Add 2 new UGC creative angles                │  │
│  │                                                        │  │
│  │     📋 Config Changes:                                │  │
│  │     [View Side-by-Side Diff →]                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ▼ v1 → v2: Audience Refinement                      │  │
│  │     2 days ago • Session 3                            │  │
│  │     [Click to expand]                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  Top Performers                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  🏆 #1: TikTok + Interest + UGC Video                │  │
│  │       CPA: $22.10 • ROAS: 4.1x • Conv: 412           │  │
│  │                                                        │  │
│  │  🥈 #2: TikTok + Lookalike + UGC Video               │  │
│  │       CPA: $24.80 • ROAS: 3.5x • Conv: 289           │  │
│  │                                                        │  │
│  │  🥉 #3: Meta + Lookalike + Carousel                  │  │
│  │       CPA: $29.30 • ROAS: 2.8x • Conv: 146           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Key Components:**
- **Comparison Table**: Side-by-side metrics across all iterations with trend indicators
- **Trend Charts**: Line charts showing metric trajectories
- **Patch History Accordion**: Expandable cards for each optimization with analysis/changes
- **Config Diff Viewer**: Side-by-side JSON diff (accessible from patch cards)
- **Top Performers Leaderboard**: Ranked list with medals

**Visual Design:**
- Use color coding: Green=improvement, Red=decline, Gray=neutral
- Show percentage changes prominently
- Highlight winning combinations with trophy icons

---

## 5. Component Library

### 5.1 Core UI Components

#### MetricCard
```typescript
interface MetricCardProps {
  label: string;              // "CPA"
  value: string | number;     // "$23.45"
  trend?: {
    value: number;            // -15
    direction: 'up' | 'down'; // 'down'
    isPositive: boolean;      // true (lower CPA is good)
  };
  icon?: ReactNode;
  size?: 'small' | 'medium' | 'large';
}
```

#### ProgressStepper
```typescript
interface ProgressStepperProps {
  steps: Step[];
  currentStep: number;
}

interface Step {
  id: string;
  name: string;
  status: 'completed' | 'running' | 'pending' | 'error';
  duration_ms?: number;
  substeps?: string[];
}
```

#### FileUploader
```typescript
interface FileUploaderProps {
  accept: string[];           // ['.csv', '.json']
  maxSize: number;            // 10MB
  multiple: boolean;
  onUpload: (files: File[]) => void;
  onValidate?: (file: File) => ValidationResult;
}
```

#### ConfigViewer
```typescript
interface ConfigViewerProps {
  config: CampaignConfig;
  format: 'json' | 'form';
  editable?: boolean;
  onCopy?: () => void;
  onDownload?: () => void;
}
```

#### TimelineChart
```typescript
interface TimelineChartProps {
  data: MetricsSnapshot[];
  metrics: string[];          // ['cpa', 'roas', 'conversions']
  xAxis: 'iteration' | 'date';
  height: number;
}
```

#### PhaseCard
```typescript
interface PhaseCardProps {
  phase: Phase;
  expanded: boolean;
  onToggle: () => void;
}
```

#### CheckpointBadge
```typescript
interface CheckpointBadgeProps {
  checkpoint: Checkpoint;
  onClick?: () => void;
}
```

---

### 5.2 Data Visualization Components

#### CombinationMatrix
Visual grid showing all test combinations across platforms/audiences/creatives

#### GanttTimeline
Horizontal timeline with phase bars and checkpoint markers

#### DiffViewer
Side-by-side JSON comparison with line-level highlighting

#### PerformanceTable
Sortable table with inline trend indicators and sparklines

---

## 6. State Management

### Global State Structure (Redux/Zustand)

```typescript
interface AppState {
  // Auth
  user: User | null;
  isAuthenticated: boolean;

  // Projects
  projects: {
    list: Project[];
    current: Project | null;
    loading: boolean;
    error: string | null;
  };

  // Sessions
  sessions: {
    list: Session[];
    current: Session | null;
    loading: boolean;
  };

  // Agent Execution
  execution: {
    isRunning: boolean;
    currentNode: string | null;
    progress: ExecutionProgress;
    logs: ActivityLog[];
  };

  // UI State
  ui: {
    sidebarOpen: boolean;
    activeTab: string;
    filters: FilterState;
  };
}

interface ExecutionProgress {
  steps: ProgressStep[];
  currentStepIndex: number;
  startTime: number;
  estimatedEndTime?: number;
}

interface ActivityLog {
  timestamp: string;
  level: 'info' | 'success' | 'warning' | 'error';
  category: 'node' | 'llm' | 'system';
  message: string;
}
```

### Key State Actions

```typescript
// Project Actions
dispatch(fetchProjects());
dispatch(createProject(projectData));
dispatch(selectProject(projectId));
dispatch(uploadResults(projectId, files));

// Session Actions
dispatch(startSession(projectId, files));
dispatch(fetchSessionHistory(projectId));

// Execution Actions
dispatch(subscribeToExecution(sessionId));
dispatch(updateProgress(progressData));
dispatch(addLog(logEntry));

// UI Actions
dispatch(setActiveTab(tabName));
dispatch(toggleSidebar());
dispatch(setFilters(filterState));
```

---

## 7. API Integration

### Backend API Endpoints

#### Authentication
```
POST   /api/auth/register          Register new user
POST   /api/auth/login             Login
POST   /api/auth/logout            Logout
GET    /api/auth/me                Get current user
```

#### Projects
```
GET    /api/projects               List all projects for user
POST   /api/projects               Create new project
GET    /api/projects/:id           Get project details
PATCH  /api/projects/:id           Update project
DELETE /api/projects/:id           Delete project
```

#### Sessions
```
POST   /api/projects/:id/sessions  Start new session
GET    /api/projects/:id/sessions  List sessions for project
GET    /api/sessions/:id           Get session details
GET    /api/sessions/:id/cycles    Get ReAct cycles for session
```

#### Files
```
POST   /api/files/upload           Upload file(s) to storage
GET    /api/files/:id              Download file
DELETE /api/files/:id              Delete file
POST   /api/files/analyze          Analyze file contents
```

#### Agent Execution
```
POST   /api/agent/run              Start agent execution
GET    /api/agent/status/:id       Get execution status
WS     /ws/execution/:session_id   WebSocket for live updates
```

---

### WebSocket Protocol

**Connection:**
```typescript
const ws = new WebSocket(`wss://api.adronaut.com/ws/execution/${sessionId}`);
```

**Message Types:**
```typescript
// Node started
{
  type: 'node_start',
  node_name: 'reflection',
  timestamp: '2025-10-13T14:32:45Z'
}

// Node progress
{
  type: 'node_progress',
  node_name: 'reflection',
  message: 'Analyzing 12 test combinations...',
  progress: 0.5
}

// Node completed
{
  type: 'node_complete',
  node_name: 'reflection',
  duration_ms: 5200,
  timestamp: '2025-10-13T14:32:50Z'
}

// LLM activity
{
  type: 'llm_call',
  task_name: 'Performance Analysis',
  prompt_preview: 'Analyze the following...',
  tokens_used: 1247
}

// Session complete
{
  type: 'session_complete',
  session_id: 'uuid',
  final_state: {...}
}

// Error
{
  type: 'error',
  message: 'Failed to analyze results',
  details: '...'
}
```

---

## 8. Visual Design System

### Color Palette

#### Primary Colors
```css
--primary-500: #6366F1;      /* Indigo - Main brand */
--primary-600: #4F46E5;
--primary-700: #4338CA;
```

#### Semantic Colors
```css
--success-500: #10B981;      /* Green - Improvements, completed */
--warning-500: #F59E0B;      /* Amber - Warnings, checkpoints */
--error-500: #EF4444;        /* Red - Errors, declines */
--info-500: #3B82F6;         /* Blue - Running, info */
```

#### Neutral Colors
```css
--gray-50: #F9FAFB;
--gray-100: #F3F4F6;
--gray-200: #E5E7EB;
--gray-700: #374151;
--gray-900: #111827;
```

### Typography

```css
/* Headings */
--font-heading: 'Inter', sans-serif;
--h1: 2.5rem / 600;          /* Page titles */
--h2: 2rem / 600;            /* Section titles */
--h3: 1.5rem / 600;          /* Card titles */

/* Body */
--font-body: 'Inter', sans-serif;
--body-lg: 1.125rem / 400;
--body-base: 1rem / 400;
--body-sm: 0.875rem / 400;

/* Mono */
--font-mono: 'JetBrains Mono', monospace;
--code: 0.875rem / 400;
```

### Spacing Scale

```css
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-12: 3rem;     /* 48px */
```

### Component Styling

#### Cards
```css
.card {
  background: white;
  border: 1px solid var(--gray-200);
  border-radius: 0.75rem;
  padding: var(--space-6);
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.card:hover {
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  border-color: var(--primary-500);
}
```

#### Buttons
```css
.btn-primary {
  background: var(--primary-500);
  color: white;
  padding: var(--space-3) var(--space-6);
  border-radius: 0.5rem;
  font-weight: 600;
}

.btn-secondary {
  background: white;
  color: var(--gray-700);
  border: 1px solid var(--gray-300);
}
```

#### Status Badges
```css
.badge-success { background: #D1FAE5; color: #065F46; }
.badge-warning { background: #FEF3C7; color: #92400E; }
.badge-error { background: #FEE2E2; color: #991B1B; }
.badge-info { background: #DBEAFE; color: #1E40AF; }
```

---

## 9. Real-time Updates

### WebSocket Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       React Frontend                         │
│  useWebSocket(sessionId) → connects to WS                   │
│  ↓ receives messages                                         │
│  dispatch(updateProgress(msg)) → updates Redux              │
│  ↓ components re-render                                      │
│  ProgressStepper, ActivityLog update UI                     │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI WebSocket Server                  │
│  /ws/execution/{session_id}                                 │
│  ↓ listens to agent events                                   │
│  track_node() → emits node_start/node_complete              │
│  LLM calls → emits llm_call                                 │
│  ↓ broadcasts to connected clients                           │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                   LangGraph Agent (Core)                     │
│  @track_node decorator → emits events                       │
│  Progress tracker → logs to WS server                        │
└─────────────────────────────────────────────────────────────┘
```

### React Hook Example

```typescript
function useAgentExecution(sessionId: string) {
  const [progress, setProgress] = useState<ExecutionProgress>({});
  const [logs, setLogs] = useState<ActivityLog[]>([]);
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(`wss://api.adronaut.com/ws/execution/${sessionId}`);

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      switch (msg.type) {
        case 'node_start':
          setProgress(prev => ({ ...prev, currentNode: msg.node_name }));
          break;
        case 'node_complete':
          // Update step status
          break;
        case 'llm_call':
          setLogs(prev => [...prev, {
            timestamp: new Date().toISOString(),
            level: 'info',
            category: 'llm',
            message: `[LLM] ${msg.task_name}: ${msg.prompt_preview.slice(0, 100)}...`
          }]);
          break;
        case 'session_complete':
          setIsComplete(true);
          break;
      }
    };

    return () => ws.close();
  }, [sessionId]);

  return { progress, logs, isComplete };
}
```

---

## 10. Technical Recommendations

### Frontend Stack

**Framework:** React 18+ with TypeScript
- Component-based architecture
- Strong typing for data models
- Large ecosystem

**State Management:** Redux Toolkit or Zustand
- Redux Toolkit: Battle-tested, great DevTools
- Zustand: Simpler, less boilerplate

**Routing:** React Router v6
- Declarative routing
- Nested routes for project tabs

**Styling:** Tailwind CSS + Headless UI
- Utility-first CSS
- Pre-built accessible components

**Data Fetching:** React Query (TanStack Query)
- Automatic caching
- Optimistic updates
- Retry logic

**Charts:** Recharts or Chart.js
- Recharts: React-native, composable
- Chart.js: More features, heavier

**Forms:** React Hook Form + Zod
- Performant form handling
- Schema validation

**WebSocket:** native WebSocket API + custom hook
- Simple, no library needed
- Reconnection logic in custom hook

---

### Backend Stack (FastAPI)

**Framework:** FastAPI
- Async support
- Auto-generated OpenAPI docs
- WebSocket support

**API Structure:**
```
backend/
├── api/
│   ├── routes/
│   │   ├── auth.py
│   │   ├── projects.py
│   │   ├── sessions.py
│   │   ├── files.py
│   │   └── agent.py
│   ├── dependencies.py
│   └── middleware.py
├── models/
│   ├── user.py
│   ├── project.py
│   └── session.py
├── services/
│   ├── agent_service.py
│   ├── file_service.py
│   └── websocket_manager.py
├── database/
│   └── supabase_client.py
└── main.py
```

**Key Endpoints Implementation:**
```python
from fastapi import FastAPI, WebSocket
from src.agent.graph import get_campaign_agent

app = FastAPI()

@app.post("/api/projects/{project_id}/sessions")
async def start_session(project_id: str, files: List[UploadFile]):
    # 1. Upload files to storage
    # 2. Create session record
    # 3. Start agent execution async
    # 4. Return session_id
    pass

@app.websocket("/ws/execution/{session_id}")
async def execution_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()
    # Connect to progress tracker
    # Stream events to client
    pass
```

---

### Database Access

**Supabase Client:**
```typescript
// Frontend
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.REACT_APP_SUPABASE_URL,
  process.env.REACT_APP_SUPABASE_ANON_KEY
)

// Fetch projects
const { data: projects } = await supabase
  .from('projects')
  .select('*')
  .eq('user_id', userId)
  .order('updated_at', { ascending: false })
```

**Backend (Python):**
```python
from src.database.persistence import ProjectPersistence

# Load project
project = ProjectPersistence.load_project(project_id)

# Save project
ProjectPersistence.save_project(project_data)
```

---

### Authentication

**Strategy:** Supabase Auth
- Email/password
- Social logins (Google, GitHub)
- JWTs for API auth

**Frontend Flow:**
```typescript
// Login
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password'
})

// Get session
const { data: { session } } = await supabase.auth.getSession()

// Protected API calls
fetch('/api/projects', {
  headers: {
    'Authorization': `Bearer ${session.access_token}`
  }
})
```

---

### File Upload Flow

1. **Frontend:** User selects files → client uploads directly to Supabase Storage
2. **Frontend:** Gets storage paths → sends to backend API
3. **Backend:** Creates uploaded_files records with storage paths
4. **Backend:** Starts agent with file references
5. **Agent:** Downloads files from storage → processes

**Why this flow?**
- Reduces backend bandwidth
- Leverages Supabase CDN
- Enables direct browser-to-storage upload

---

### Performance Optimizations

1. **Pagination:** Load projects in batches (20 per page)
2. **Virtual Scrolling:** For long activity logs (react-window)
3. **Debouncing:** Search/filter inputs (300ms delay)
4. **Lazy Loading:** Code-split routes with React.lazy()
5. **Memoization:** Expensive calculations with useMemo/useCallback
6. **Optimistic Updates:** Show UI changes before API confirms
7. **Caching:** React Query for 5-minute cache on projects list

---

### Deployment

**Frontend:** Vercel or Netlify
- Auto-deploy from git
- Edge CDN
- Preview deployments

**Backend:** Railway or Render
- Docker container
- Managed Postgres (if needed)
- WebSocket support

**Database:** Supabase (managed)
- Hosted Postgres
- Built-in storage
- Auth included

---

## Summary Checklist

### MVP Features (Phase 1)
- [ ] Dashboard with project list
- [ ] Create new project modal
- [ ] File upload with validation
- [ ] Agent execution progress view
- [ ] Strategy visualization
- [ ] Config viewer/download
- [ ] Session history

### Enhanced Features (Phase 2)
- [ ] Execution timeline visualization
- [ ] Performance comparison view
- [ ] Config diff viewer
- [ ] Real-time WebSocket updates
- [ ] Activity log with filtering
- [ ] Metrics charts

### Advanced Features (Phase 3)
- [ ] Knowledge graph visualization
- [ ] ReAct cycle audit trail
- [ ] Multi-user collaboration
- [ ] API rate limiting
- [ ] Usage analytics
- [ ] Export reports (PDF)

---

## Next Steps

1. **Design Mockups:** Create high-fidelity mockups in Figma based on layouts above
2. **Component Library:** Build storybook with reusable components
3. **API Spec:** Finalize OpenAPI spec for backend
4. **Database Migrations:** Set up Supabase schema
5. **MVP Development:** Start with Dashboard → New Project → Execution Progress
6. **Testing:** Unit tests (Jest), E2E tests (Playwright)
7. **Deployment:** Set up CI/CD pipeline

---

**Document Version:** 1.0
**Last Updated:** 2025-10-13
**Author:** Generated for Adronaut Agent UI Design
