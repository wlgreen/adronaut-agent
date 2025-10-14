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
    Print execution timeline plan

    Args:
        experiment_plan: Execution timeline dictionary
    """
    if not experiment_plan:
        return

    # Check if this is the new execution timeline format
    if "timeline" in experiment_plan:
        print_execution_timeline(experiment_plan)
    else:
        # Fallback for old format (shouldn't happen but safe)
        print("\n⚠ Legacy experiment plan format detected")
        print(json.dumps(experiment_plan, indent=2))


def print_execution_timeline(execution_plan):
    """Print flexible execution timeline plan"""
    timeline = execution_plan.get("timeline", {})

    if not timeline:
        print("\n⚠ No timeline data available")
        return

    total_days = timeline.get("total_duration_days", 0)
    phases = timeline.get("phases", [])
    checkpoints = timeline.get("checkpoints", [])

    print("\n" + "=" * 60)
    print(f"  EXECUTION TIMELINE ({total_days} DAYS)")
    print("=" * 60)

    # Print reasoning
    if timeline.get("reasoning"):
        print(f"\n💡 Timeline Design:")
        print(f"  {timeline['reasoning']}")

    # Print phases
    print(f"\n📅 TESTING PHASES ({len(phases)} phases):")
    print("─" * 60)

    for i, phase in enumerate(phases, 1):
        phase_name = phase.get("name", f"Phase {i}")
        duration = phase.get("duration_days", 0)
        start = phase.get("start_day", 0)
        end = phase.get("end_day", 0)
        budget_pct = phase.get("budget_allocation_percent", 0)

        print(f"\n[{i}] {phase_name.upper()}")
        print(f"    Days {start}-{end} ({duration} days) | Budget: {budget_pct}%")

        # Objectives
        objectives = phase.get("objectives", [])
        if objectives:
            print(f"    Objectives:")
            for obj in objectives:
                print(f"      • {obj}")

        # Test combinations
        combos = phase.get("test_combinations", [])
        if combos:
            print(f"    Test Combinations ({len(combos)}):")
            for combo in combos:
                combo_budget = combo.get("budget_percent", 0)
                print(f"      [{combo_budget}%] {combo.get('platform', '?')} + "
                      f"{combo.get('audience', '?')[:25]} + "
                      f"{combo.get('creative', '?')[:20]}")
                if combo.get("rationale"):
                    rationale = combo["rationale"]
                    if len(rationale) > 60:
                        rationale = rationale[:57] + "..."
                    print(f"           → {rationale}")

                # Display creative generation prompts
                creative = combo.get("creative_generation")
                if creative:
                    if creative.get("error"):
                        print(f"           ⚠ Creative: {creative.get('note', 'Manual development required')}")
                    else:
                        print(f"           📸 Creative Brief:")

                        # Visual prompt (truncated)
                        visual_prompt = creative.get("visual_prompt", "")
                        if visual_prompt:
                            visual_preview = visual_prompt[:80] + "..." if len(visual_prompt) > 80 else visual_prompt
                            print(f"              Visual: {visual_preview}")

                        # Ad copy
                        copy_text = creative.get("copy_primary_text", "")
                        if copy_text:
                            copy_preview = copy_text[:60] + "..." if len(copy_text) > 60 else copy_text
                            print(f"              Copy: \"{copy_preview}\"")

                        # Headline
                        headline = creative.get("copy_headline", "")
                        if headline:
                            print(f"              Headline: \"{headline}\"")

                        # CTA
                        cta = creative.get("copy_cta", "")
                        if cta:
                            print(f"              CTA: {cta}")

                        # Hooks (show first hook + count)
                        hooks = creative.get("hooks", [])
                        if hooks:
                            first_hook = hooks[0][:50] + "..." if len(hooks[0]) > 50 else hooks[0]
                            additional = f" (+{len(hooks)-1} more)" if len(hooks) > 1 else ""
                            print(f"              Hooks: \"{first_hook}\"{additional}")

                        # Technical specs
                        specs = creative.get("technical_specs", {})
                        if specs:
                            aspect_ratio = specs.get("aspect_ratio", "?")
                            dimensions = specs.get("dimensions", "?")
                            print(f"              Specs: {aspect_ratio} | {dimensions}")

        # Success criteria
        criteria = phase.get("success_criteria", [])
        if criteria:
            print(f"    Success Criteria:")
            for criterion in criteria:
                print(f"      ✓ {criterion}")

        # Decision triggers
        triggers = phase.get("decision_triggers", {})
        if triggers:
            print(f"    Decision Triggers:")
            if triggers.get("proceed_if"):
                print(f"      → Proceed if: {triggers['proceed_if']}")
            if triggers.get("pause_if"):
                print(f"      ⚠ Pause if: {triggers['pause_if']}")
            if triggers.get("scale_if"):
                print(f"      ⚡ Scale if: {triggers['scale_if']}")

    # Print checkpoints
    if checkpoints:
        print(f"\n📍 CHECKPOINT SCHEDULE ({len(checkpoints)} checkpoints):")
        print("─" * 60)

        for checkpoint in checkpoints:
            day = checkpoint.get("day", 0)
            purpose = checkpoint.get("purpose", "Review")
            required = checkpoint.get("action_required", False)
            action_mark = "🔴" if required else "🟡"

            print(f"\n  {action_mark} Day {day}: {purpose}")

            review_focus = checkpoint.get("review_focus", [])
            if review_focus:
                print(f"     Focus:")
                for focus_item in review_focus:
                    print(f"       • {focus_item}")

    # Print statistical requirements
    stats = execution_plan.get("statistical_requirements", {})
    if stats:
        print(f"\n📊 STATISTICAL REQUIREMENTS:")
        print(f"  Min conversions/combo: {stats.get('min_conversions_per_combo', 'N/A')}")
        print(f"  Confidence level: {stats.get('confidence_level', 'N/A')}")
        print(f"  Expected weekly conversions: {stats.get('expected_weekly_conversions', 'N/A')}")
        if stats.get("power_analysis"):
            print(f"  Power analysis: {stats['power_analysis']}")

    # Print risk mitigation
    risks = execution_plan.get("risk_mitigation", {})
    if risks:
        print(f"\n⚠️  RISK MITIGATION:")

        early_signals = risks.get("early_warning_signals", [])
        if early_signals:
            print(f"  Early warning signals:")
            for signal in early_signals:
                print(f"    • {signal}")

        contingencies = risks.get("contingency_plans", [])
        if contingencies:
            print(f"  Contingency plans:")
            for plan in contingencies:
                print(f"    → {plan}")

    # Print creative assets summary
    total_creatives = 0
    platforms_with_creatives = set()
    for phase in phases:
        for combo in phase.get("test_combinations", []):
            if combo.get("creative_generation") and not combo.get("creative_generation", {}).get("error"):
                total_creatives += 1
                platforms_with_creatives.add(combo.get("platform", "Unknown"))

    if total_creatives > 0:
        print(f"\n📸 CREATIVE ASSETS SUMMARY:")
        print(f"  Total creative briefs generated: {total_creatives}")
        print(f"  Platforms covered: {', '.join(sorted(platforms_with_creatives))}")
        print(f"  Ready for AI image generation (DALL-E, Midjourney, etc.)")

    print("\n" + "─" * 60)
    print(f"  ⏱️  Total Duration: {total_days} days (max 30 days)")
    print(f"  📈 Adaptive approach based on historical performance")
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

    # Flow tracking info
    flow_status = final_state.get('flow_status', 'unknown')
    print(f"\n--- Flow Status ---")
    print(f"Status: {flow_status}")
    if flow_status == "completed":
        print("✓ Flow completed successfully")
    elif flow_status == "in_progress":
        print(f"⚠ Flow incomplete - last completed: {final_state.get('last_completed_node', 'N/A')}")
    elif flow_status == "failed":
        print(f"✗ Flow failed at: {final_state.get('current_executing_node', 'N/A')}")

    completed_nodes = final_state.get('completed_nodes', [])
    if completed_nodes:
        print(f"Completed nodes ({len(completed_nodes)}): {' → '.join(completed_nodes)}")

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

    # Check if project has incomplete flow
    if is_valid_uuid(args.project_id):
        project = ProjectPersistence.load_project(args.project_id)
        if project:
            flow_status = project.get("flow_status", "not_started")
            last_completed = project.get("last_completed_node")
            completed_nodes = project.get("completed_nodes", [])

            if flow_status == "in_progress" and last_completed:
                print("\n" + "=" * 60)
                print("  ⚠️  INCOMPLETE FLOW DETECTED")
                print("=" * 60)
                print(f"Flow status: {flow_status}")
                print(f"Last completed node: {last_completed}")
                print(f"Completed nodes: {completed_nodes}")
                print("=" * 60)

                if not args.restart:
                    print("✓ Will resume from last checkpoint")
                    print("  (Use --restart to force a fresh start)\n")
                else:
                    print("✓ Forcing fresh start (--restart flag used)\n")

            elif flow_status == "failed" and last_completed:
                print("\n" + "=" * 60)
                print("  ⚠️  PREVIOUS FLOW FAILED")
                print("=" * 60)
                print(f"Last completed node before failure: {last_completed}")
                print(f"Completed nodes: {completed_nodes}")
                print("=" * 60)

                if not args.restart:
                    print("✓ Will retry from failed point")
                    print("  (Use --restart to force a fresh start)\n")
                else:
                    print("✓ Forcing fresh start (--restart flag used)\n")

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

        # Set force_restart flag if requested
        if args.restart:
            state["force_restart"] = True

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
    run_parser.add_argument(
        "--restart",
        action="store_true",
        help="Force restart flow even if resumption is possible (clears flow state)"
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
