#!/usr/bin/env python3
"""
Campaign Setup Agent CLI

Usage:
    python cli.py run --project-id <project-id>
"""

import sys
import argparse
import json
import uuid
from pathlib import Path
from src.agent.graph import get_campaign_agent
from src.agent.state import create_initial_state
from src.database.persistence import SessionPersistence, ProjectPersistence
from src.utils.progress import get_progress_tracker


def is_valid_uuid(value):
    """Check if a string is a valid UUID"""
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


def get_or_create_project(project_identifier):
    """
    Get existing project or create new one

    Args:
        project_identifier: Either a UUID or a project name

    Returns:
        project_id: UUID of the project
    """
    # Check if it's already a valid UUID
    if is_valid_uuid(project_identifier):
        # Verify it exists
        project = ProjectPersistence.load_project(project_identifier)
        if project:
            print(f"✓ Using existing project: {project.get('project_name', 'Unnamed')}")
            return project_identifier
        else:
            print(f"Error: Project UUID {project_identifier} not found")
            sys.exit(1)

    # Treat as project name - create new project
    print(f"Creating new project: {project_identifier}")
    project_id = ProjectPersistence.create_project(
        user_id="cli-user",  # Default user for CLI
        project_name=project_identifier,
        product_description="Campaign setup via CLI",
        target_budget=1000.0  # Default budget
    )
    print(f"✓ Created project with ID: {project_id}")
    return project_id


def print_banner():
    """Print CLI banner"""
    print("=" * 60)
    print("  Campaign Setup Agent - Intelligent Optimization")
    print("=" * 60)
    print()


def print_strategy_details(strategy):
    """
    Print detailed strategy breakdown showing insights → strategy mapping

    Args:
        strategy: Strategy dictionary from current_strategy
    """
    if not strategy:
        return

    print("\n" + "=" * 60)
    print("  STRATEGY BREAKDOWN")
    print("=" * 60)

    # Insights
    insights = strategy.get("insights", {})
    if insights:
        print("\n📊 KEY INSIGHTS:")
        if insights.get("patterns"):
            print("\n  Patterns Identified:")
            for pattern in insights["patterns"]:
                print(f"    • {pattern}")

        if insights.get("strengths"):
            print("\n  Strengths:")
            for strength in insights["strengths"]:
                print(f"    ✓ {strength}")

        if insights.get("weaknesses"):
            print("\n  Weaknesses:")
            for weakness in insights["weaknesses"]:
                print(f"    ⚠ {weakness}")

        if insights.get("benchmark_comparison"):
            print(f"\n  Benchmark Comparison:")
            print(f"    {insights['benchmark_comparison']}")

    # Target Audience
    audience = strategy.get("target_audience", {})
    if audience:
        print("\n🎯 TARGET AUDIENCE:")
        if audience.get("primary_segments"):
            segments = audience['primary_segments']
            if isinstance(segments, list):
                print(f"  Segments: {', '.join(segments)}")
            else:
                print(f"  Segments: {segments}")
        if audience.get("demographics"):
            demo = audience["demographics"]
            if isinstance(demo, dict):
                print(f"  Demographics: {demo.get('age', 'N/A')} | {demo.get('gender', 'N/A')} | {demo.get('location', 'N/A')}")
            else:
                print(f"  Demographics: {demo}")
        if audience.get("interests"):
            interests = audience['interests']
            if isinstance(interests, list):
                interests = interests[:5]  # First 5
                print(f"  Key Interests: {', '.join(interests)}")
            else:
                print(f"  Key Interests: {interests}")

    # Creative Strategy
    creative = strategy.get("creative_strategy", {})
    if creative:
        print("\n🎨 CREATIVE STRATEGY:")
        if creative.get("messaging_angles"):
            angles = creative["messaging_angles"]
            if isinstance(angles, list):
                print("  Messaging Angles:")
                for angle in angles[:3]:
                    print(f"    • {angle}")
            else:
                print(f"  Messaging Angles: {angles}")
        if creative.get("value_props"):
            props = creative["value_props"]
            if isinstance(props, list):
                print("  Value Propositions:")
                for prop in props[:3]:
                    print(f"    • {prop}")
            else:
                print(f"  Value Propositions: {props}")

    # Platform Strategy
    platform = strategy.get("platform_strategy", {})
    if platform:
        print("\n📱 PLATFORM STRATEGY:")
        if platform.get("priorities"):
            priorities = platform['priorities']
            if isinstance(priorities, list):
                print(f"  Priority Platforms: {', '.join(priorities)}")
            else:
                print(f"  Priority Platforms: {priorities}")
        if platform.get("budget_split"):
            budget_split = platform["budget_split"]
            if isinstance(budget_split, dict):
                print("  Budget Allocation:")
                for plat, pct in budget_split.items():
                    # Handle both numeric and string percentages
                    try:
                        pct_num = float(pct) if isinstance(pct, str) else pct
                        print(f"    {plat}: {int(pct_num * 100)}%")
                    except (ValueError, TypeError):
                        print(f"    {plat}: {pct}")
            else:
                print(f"  Budget Allocation: {budget_split}")
        if platform.get("rationale"):
            print(f"  Rationale: {platform['rationale']}")

    print()


def print_experiment_plan(experiment_plan):
    """
    Print experiment plan - handles both sequential (3-week) and parallel (7-day) formats

    Args:
        experiment_plan: Experiment plan dictionary
    """
    if not experiment_plan:
        return

    # Detect format: accelerated parallel or traditional sequential
    mode = experiment_plan.get("mode", "sequential")

    if mode == "accelerated":
        print_accelerated_experiment_plan(experiment_plan)
    else:
        print_sequential_experiment_plan(experiment_plan)


def print_sequential_experiment_plan(experiment_plan):
    """Print traditional 3-week sequential experiment plan"""
    print("\n" + "=" * 60)
    print("  EXPERIMENT PLAN (3 WEEKS - SEQUENTIAL)")
    print("=" * 60)

    for week_key in ["week_1", "week_2", "week_3"]:
        week = experiment_plan.get(week_key, {})
        if not week:
            continue

        week_num = week_key.split("_")[1]
        print(f"\n🔬 WEEK {week_num}: {week.get('name', 'Unnamed Test')}")
        print("─" * 60)

        if week.get("hypothesis"):
            print(f"  Hypothesis:")
            print(f"    {week['hypothesis']}")

        if week.get("variations"):
            variations = week["variations"]
            if isinstance(variations, list):
                print(f"\n  Variations:")
                for var in variations:
                    print(f"    • {var}")
            else:
                print(f"\n  Variations: {variations}")

        if week.get("control"):
            print(f"\n  Control Setup:")
            control = week["control"]
            if isinstance(control, dict):
                for key, val in control.items():
                    print(f"    {key}: {val}")
            else:
                print(f"    {control}")

        if week.get("metrics"):
            metrics = week["metrics"]
            if isinstance(metrics, list):
                print(f"\n  Success Metrics: {', '.join(metrics)}")
            else:
                print(f"\n  Success Metrics: {metrics}")

        if week.get("expected_improvement"):
            print(f"  Expected Improvement: {week['expected_improvement']}")

    print("\n" + "─" * 60)
    print("  → After each week, upload results for optimization")
    print()


def print_accelerated_experiment_plan(experiment_plan):
    """Print accelerated 7-day parallel experiment plan"""
    print("\n" + "=" * 60)
    print("  EXPERIMENT PLAN (7 DAYS - PARALLEL TESTING)")
    print("=" * 60)
    print("  ⚡ ACCELERATED MODE: Test everything simultaneously")
    print("=" * 60)

    day_plan = experiment_plan.get("day_1_to_7", {})

    if day_plan.get("description"):
        print(f"\n📋 {day_plan['description']}")

    # Print hypotheses
    hypotheses = day_plan.get("hypotheses", {})
    if hypotheses:
        print("\n🔬 HYPOTHESES:")
        if hypotheses.get("platform"):
            print(f"  Platform: {hypotheses['platform']}")
        if hypotheses.get("audience"):
            print(f"  Audience: {hypotheses['audience']}")
        if hypotheses.get("creative"):
            print(f"  Creative: {hypotheses['creative']}")
        if hypotheses.get("interaction"):
            print(f"  Interaction: {hypotheses['interaction']}")

    # Print test matrix
    test_matrix = day_plan.get("test_matrix", {})
    combinations = test_matrix.get("combinations", [])

    if combinations:
        print(f"\n📊 TEST MATRIX ({len(combinations)} combinations running in parallel):")
        print("─" * 60)

        for i, combo in enumerate(combinations, 1):
            budget = combo.get("budget_allocation", "?")
            print(f"\n  [{i}] {combo.get('label', 'Unnamed Combo')} ({budget})")
            print(f"      Platform:  {combo.get('platform', 'N/A')}")
            print(f"      Audience:  {combo.get('audience', 'N/A')}")
            print(f"      Creative:  {combo.get('creative', 'N/A')}")
            if combo.get("rationale"):
                rationale = combo["rationale"]
                # Wrap long rationale
                if len(rationale) > 70:
                    rationale = rationale[:67] + "..."
                print(f"      Why:       {rationale}")

    # Print decision criteria
    criteria = day_plan.get("decision_criteria", {})
    if criteria:
        print("\n📏 DECISION CRITERIA:")
        print(f"  Min conversions per combo: {criteria.get('min_conversions_per_combo', 'N/A')}")
        print(f"  Confidence level: {criteria.get('confidence_level', 'N/A')}")
        print(f"  Primary metric: {criteria.get('primary_metric', 'N/A')}")
        if criteria.get("secondary_metrics"):
            metrics = criteria["secondary_metrics"]
            if isinstance(metrics, list):
                print(f"  Secondary metrics: {', '.join(metrics)}")

    # Print evaluation schedule
    schedule = day_plan.get("evaluation_schedule", {})
    if schedule:
        print("\n📅 EVALUATION SCHEDULE:")
        if schedule.get("day_3"):
            print(f"  Day 3: {schedule['day_3']}")
        if schedule.get("day_7"):
            print(f"  Day 7: {schedule['day_7']}")

    # Print memory-based optimizations
    optimizations = experiment_plan.get("memory_based_optimizations", {})
    if optimizations:
        print("\n🧠 MEMORY-BASED OPTIMIZATIONS:")

        skipped = optimizations.get("skipped_tests", [])
        if skipped:
            print("  Skipped (based on historical data):")
            for item in skipped:
                print(f"    ✗ {item}")

        confident = optimizations.get("confident_decisions", [])
        if confident:
            print("  Confident decisions:")
            for item in confident:
                print(f"    ✓ {item}")

        hedges = optimizations.get("hedge_tests", [])
        if hedges:
            print("  Hedge tests:")
            for item in hedges:
                print(f"    ⚠ {item}")

    # Print expected outcome
    if day_plan.get("expected_outcome"):
        print(f"\n🎯 EXPECTED OUTCOME:")
        print(f"  {day_plan['expected_outcome']}")

    # Print statistical power
    if day_plan.get("statistical_power"):
        print(f"\n📊 STATISTICAL POWER:")
        print(f"  {day_plan['statistical_power']}")

    print("\n" + "─" * 60)
    print("  → Upload results on Day 3 for checkpoint, Day 7 for final decision")
    print("  ⚡ TIME SAVED: 14 days vs traditional sequential testing")
    print()


def print_results(final_state):
    """Print session results"""
    print("\n" + "=" * 60)
    print("  Session Results")
    print("=" * 60)

    # Basic info
    print(f"\nProject ID: {final_state['project_id']}")
    print(f"Session: {final_state['session_num']}")
    print(f"Decision: {final_state.get('decision', 'N/A')}")
    print(f"Phase: {final_state['current_phase']}")
    print(f"Iteration: {final_state['iteration']}")

    # Messages
    if final_state.get("messages"):
        print("\n--- Messages ---")
        for msg in final_state["messages"][-5:]:  # Last 5 messages
            print(f"  • {msg}")

    # Knowledge Graph Visualization
    if final_state.get("knowledge_facts"):
        print("\n--- Knowledge Graph ---")
        kg = final_state["knowledge_facts"]
        if kg:
            print(f"Total facts: {len(kg)}")
            print()
            for key, fact in kg.items():
                # Create confidence bar (0-10 blocks)
                conf = fact.get("confidence", 0)
                conf_bar = "█" * int(conf * 10)
                conf_bar = f"{conf_bar:10}"  # Pad to 10 chars

                # Format value
                value = str(fact.get("value", "N/A"))
                if len(value) > 35:
                    value = value[:32] + "..."

                # Format source
                source = fact.get("source", "unknown")

                print(f"  {key[:28]:28} {value:35} [{conf_bar}] {conf:.2f} ({source})")
        else:
            print("  (No facts discovered)")

    # Errors
    if final_state.get("errors"):
        print("\n--- Errors ---")
        for err in final_state["errors"]:
            print(f"  ⚠ {err}")

    # Config summary
    if final_state.get("current_config"):
        config = final_state["current_config"]
        print("\n--- Campaign Configuration ---")

        if "summary" in config:
            summary = config["summary"]
            print(f"  Total Daily Budget: ${summary.get('total_daily_budget', 0)}")
            print(f"  Experiment: {summary.get('experiment', 'N/A')}")

        if "tiktok" in config:
            print(f"\n  TikTok:")
            print(f"    Budget: ${config['tiktok'].get('daily_budget', 0)}")
            print(f"    Objective: {config['tiktok'].get('objective', 'N/A')}")

        if "meta" in config:
            print(f"\n  Meta:")
            print(f"    Budget: ${config['meta'].get('daily_budget', 0)}")
            print(f"    Objective: {config['meta'].get('objective', 'N/A')}")

    # Save config to file
    if final_state.get("current_config"):
        filename = f"campaign_{final_state['project_id']}_v{final_state['iteration']}.json"
        with open(filename, "w") as f:
            json.dump(final_state["current_config"], f, indent=2)
        print(f"\n✓ Configuration saved to: {filename}")

    # Print detailed strategy breakdown
    if final_state.get("current_strategy"):
        print_strategy_details(final_state["current_strategy"])

    # Print experiment plan
    if final_state.get("experiment_plan"):
        print_experiment_plan(final_state["experiment_plan"])

    print("\n" + "=" * 60)
    print()


def run_command(args):
    """Run the agent"""
    print_banner()

    # Get or create project (handles both UUID and name)
    project_id = get_or_create_project(args.project_id)

    # Prompt for files
    print("Upload files (comma-separated paths):")
    print("  Example: data/historical.csv,data/experiments.csv")
    print()
    file_input = input("Files: ").strip()

    if not file_input:
        print("Error: No files provided")
        return 1

    # Parse file paths
    file_paths = [p.strip() for p in file_input.split(",")]

    # Validate files exist
    for path in file_paths:
        if not Path(path).exists():
            print(f"Error: File not found: {path}")
            return 1

    # Upload files to Supabase Storage first
    print(f"\nUploading {len(file_paths)} file(s) to storage...")
    uploaded_files = []

    try:
        from src.storage.file_manager import upload_file

        for path in file_paths:
            filename = Path(path).name
            print(f"  Uploading {filename}...", end=" ")

            storage_path = upload_file(path, project_id)

            uploaded_files.append({
                "storage_path": storage_path,
                "original_filename": filename
            })

            print("✓")

    except Exception as e:
        print(f"\nError uploading files: {str(e)}")
        return 1

    print(f"\nStarting agent for project: {project_id}")
    print(f"Files: {len(uploaded_files)}")

    # Initialize progress tracker
    tracker = get_progress_tracker()
    tracker.start()

    try:
        # Create initial state
        state = create_initial_state(
            project_id=project_id,
            uploaded_files=uploaded_files
        )

        # Create session
        session_id = SessionPersistence.create_session(
            project_id=project_id,
            session_num=state["session_num"],
            uploaded_files=uploaded_files
        )
        state["session_id"] = session_id

        print(f"Session ID: {session_id}")
        print("Running agent...")
        print()

        # Get and run agent
        agent = get_campaign_agent()
        final_state = agent.invoke(state)

        # Print results
        print_results(final_state)

        # Finish tracking
        tracker.finish()

        return 0

    except Exception as e:
        tracker.log_message(f"Error: {str(e)}", "error")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Campaign Setup Agent - Intelligent Campaign Optimizer"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run the agent")
    run_parser.add_argument(
        "--project-id",
        required=True,
        help="Project identifier: existing UUID or new project name (e.g., 'my-campaign-001')"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "run":
        return run_command(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
