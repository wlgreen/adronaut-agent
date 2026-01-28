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

    # Check for --inputs / --urls flags first; fall back to interactive prompt
    cli_inputs = getattr(args, 'inputs', None)
    cli_urls = getattr(args, 'urls', None)

    if cli_inputs or cli_urls:
        # Non-interactive mode
        local_paths = [p.strip() for p in (cli_inputs or "").split(",") if p.strip()]
        product_urls = [u.strip() for u in (cli_urls or "").split(",") if u.strip()]
    else:
        # Interactive mode
        print("Upload local files/folders or product URLs (comma-separated):")
        print("  Examples:")
        print("    ./data/historical.csv")
        print("    ./data/ (folder; recursive)")
        print("    https://mysite.com/product")
        print("  Or mix: https://mysite.com/product,./data/")
        print()
        input_str = input("Files/Folders/URLs: ").strip()

        if not input_str:
            print("Error: No files or URLs provided")
            return 1

        # Parse inputs - separate URLs from local paths (files or directories)
        inputs = [p.strip() for p in input_str.split(",") if p.strip()]
        local_paths = []
        product_urls = []

        for item in inputs:
            if item.startswith('http://') or item.startswith('https://'):
                product_urls.append(item)
            else:
                local_paths.append(item)

    # Expand directories into file lists (recursive), ignore hidden files/dirs
    def _is_hidden(p: Path) -> bool:
        return any(part.startswith('.') for part in p.parts)

    file_paths: list[str] = []
    for pth in local_paths:
        p = Path(pth).expanduser()
        if not p.exists():
            print(f"Error: Path not found: {pth}")
            return 1
        if p.is_dir():
            for f in p.rglob('*'):
                if f.is_file() and not _is_hidden(f):
                    file_paths.append(str(f))
        elif p.is_file():
            if not _is_hidden(p):
                file_paths.append(str(p))
        else:
            print(f"Error: Unsupported path type: {pth}")
            return 1

    # De-dupe while preserving order
    seen = set()
    file_paths = [x for x in file_paths if not (x in seen or seen.add(x))]

    if not file_paths and not product_urls:
        print("Error: No valid files/folders/URLs provided")
        return 1

    # Show what we found
    if product_urls:
        print(f"\nDetected {len(product_urls)} URL(s):")
        for url in product_urls:
            print(f"  • {url}")
    if file_paths:
        print(f"\nDetected {len(file_paths)} file(s) (from files/folders):")
        for fp in file_paths[:10]:
            print(f"  • {fp}")
        if len(file_paths) > 10:
            print(f"  ... +{len(file_paths) - 10} more")

    # Copy files into local storage (no Supabase)
    uploaded_files = []

    if file_paths:
        print(f"\nStoring {len(file_paths)} file(s) locally...")

        try:
            from src.storage.file_manager import upload_file

            for path in file_paths:
                filename = Path(path).name
                print(f"  Storing {filename}...", end=" ")

                storage_path = upload_file(path, project_id)

                uploaded_files.append({
                    "storage_path": storage_path,
                    "original_filename": filename
                })

                print("✓")

        except Exception as e:
            print(f"\nError storing files: {str(e)}")
            return 1

    print(f"\nStarting agent for project: {project_id}")
    if uploaded_files:
        print(f"Files: {len(uploaded_files)}")
    if product_urls:
        print(f"URLs: {len(product_urls)}")

    # Initialize progress tracker
    tracker = get_progress_tracker()
    tracker.start()

    try:
        # Create initial state
        state = create_initial_state(
            project_id=project_id,
            uploaded_files=uploaded_files
        )

        # Add product URLs to state if any
        if product_urls:
            state["product_urls"] = product_urls

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


def deploy_to_meta_command(args):
    """Deploy campaign config to Meta Ads via API"""
    import os
    from src.integrations.meta_ads import MetaAdsAPI, MetaAdsError

    config_path = Path(args.config_path)

    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        return 1

    # Load config
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in config file: {config_path}")
        return 1

    meta_config = config.get("meta", {})
    if not meta_config:
        print("Error: No 'meta' section found in config")
        return 1

    # Print banner
    print("=" * 60)
    print("  Meta Ads Deployment")
    print("=" * 60)
    print()
    print(f"Config file: {config_path}")
    print(f"Campaign: {meta_config.get('campaign_name', 'Untitled')}")
    print(f"Daily budget: ${meta_config.get('daily_budget', 0)}")
    print()

    # Check for dry-run mode
    dry_run = args.dry_run or os.getenv('META_DRY_RUN', '').lower() == 'true'
    sandbox_mode = os.getenv('META_SANDBOX_MODE', '').lower() == 'true'

    if dry_run:
        print("🔧 DRY RUN MODE: No actual API calls will be made")
        print()
    else:
        print("⚠️  This will create objects in Meta Ads (campaign/ad set/creatives).")
        print("    Safety: everything is created in PAUSED state.")
        confirm = input("Type YES to deploy: ").strip()
        if confirm != "YES":
            print("Aborted. (Did not deploy)")
            return 1
        print()

    # Get credentials from environment
    access_token = os.getenv('META_ACCESS_TOKEN')
    ad_account_id = os.getenv('META_AD_ACCOUNT_ID')
    page_id = os.getenv('META_PAGE_ID')
    instagram_actor_id = os.getenv('META_INSTAGRAM_ACTOR_ID')

    # Use sandbox credentials if in sandbox mode
    if sandbox_mode:
        access_token = os.getenv('META_SANDBOX_TOKEN') or access_token
        ad_account_id = os.getenv('META_SANDBOX_ACCOUNT_ID') or ad_account_id
        print("🧪 SANDBOX MODE: Using Meta sandbox environment")
        print()

    # Validate credentials
    if not dry_run:
        if not access_token:
            print("Error: META_ACCESS_TOKEN not set in environment")
            print("Set it in .env or export META_ACCESS_TOKEN=your_token")
            return 1
        if not ad_account_id:
            print("Error: META_AD_ACCOUNT_ID not set in environment")
            print("Set it in .env or export META_AD_ACCOUNT_ID=act_your_id")
            return 1
        if not page_id:
            print("Warning: META_PAGE_ID not set - creative creation will be skipped")

    # Initialize API
    try:
        api = MetaAdsAPI(
            access_token=access_token or "test_token",
            ad_account_id=ad_account_id or "act_test",
            page_id=page_id,
            instagram_actor_id=instagram_actor_id,
            dry_run=dry_run,
            sandbox_mode=sandbox_mode
        )
    except Exception as e:
        print(f"Error initializing Meta Ads API: {e}")
        return 1

    # Deploy campaign
    print("Starting deployment...")
    print()

    try:
        result = api.create_campaign_from_config(config)

        # Print results
        print("\n" + "=" * 60)
        print("  Deployment Complete")
        print("=" * 60)
        print()
        print(f"✓ Campaign ID: {result['campaign_id']}")
        print(f"✓ Ad Set IDs: {', '.join(result['ad_set_ids'])}")

        if result['ad_ids']:
            print(f"✓ Ad IDs: {', '.join(result['ad_ids'])}")
        if result['creative_ids']:
            print(f"✓ Creative IDs: {', '.join(result['creative_ids'])}")

        print(f"\nStatus: {result['status']}")

        if result['status'] == 'PAUSED':
            print("\n⚠️  Campaign created in PAUSED state")
            print("   Review in Meta Ads Manager, then activate when ready")
            print("   https://business.facebook.com/adsmanager")

        print()

        # Save deployment result (include guardrail context for watch-meta)
        meta_section = config.get("meta", {})
        result_out = {
            **result,
            "config_path": str(config_path),
            "guardrails": {
                "daily_cap": meta_section.get("daily_budget"),
                "target_cpa": (meta_section.get("bidding", {}) or {}).get("target_cpa"),
            },
        }

        result_filename = config_path.stem + "_deployment_result.json"
        with open(result_filename, 'w') as f:
            json.dump(result_out, f, indent=2)
        print(f"✓ Deployment result saved to: {result_filename}")
        print()

        return 0

    except MetaAdsError as e:
        print(f"\n❌ Meta Ads API Error: {e}")
        print()
        print("Common issues:")
        print("  • Invalid access token or expired")
        print("  • Ad account ID incorrect")
        print("  • Missing permissions (needs ads_management)")
        print("  • Rate limiting (try again later)")
        print()
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def monitor_meta_command(args):
    """Fetch Meta campaign status + insights"""
    import os
    from src.integrations.meta_ads import MetaAdsAPI
    from src.integrations.meta_monitor import fetch_campaign_metrics

    dry_run = args.dry_run or os.getenv('META_DRY_RUN', '').lower() == 'true'
    sandbox_mode = os.getenv('META_SANDBOX_MODE', '').lower() == 'true'

    campaign_id = args.campaign_id
    if args.deployment_result:
        p = Path(args.deployment_result)
        if not p.exists():
            print(f"Error: deployment result not found: {p}")
            return 1
        with open(p, 'r') as f:
            dep = json.load(f)
        campaign_id = campaign_id or dep.get('campaign_id')

    if not campaign_id:
        print("Error: need --campaign-id or --deployment-result")
        return 1

    access_token = os.getenv('META_ACCESS_TOKEN')
    ad_account_id = os.getenv('META_AD_ACCOUNT_ID')
    page_id = os.getenv('META_PAGE_ID')
    instagram_actor_id = os.getenv('META_INSTAGRAM_ACTOR_ID')

    if sandbox_mode:
        access_token = os.getenv('META_SANDBOX_TOKEN') or access_token
        ad_account_id = os.getenv('META_SANDBOX_ACCOUNT_ID') or ad_account_id

    if not dry_run and not access_token:
        print("Error: META_ACCESS_TOKEN not set")
        return 1
    if not dry_run and not ad_account_id:
        print("Error: META_AD_ACCOUNT_ID not set")
        return 1

    api = MetaAdsAPI(
        access_token=access_token or "test_token",
        ad_account_id=ad_account_id or "act_test",
        page_id=page_id,
        instagram_actor_id=instagram_actor_id,
        dry_run=dry_run,
        sandbox_mode=sandbox_mode,
    )

    print("=" * 60)
    print("  Meta Ads Monitor")
    print("=" * 60)
    print(f"Campaign ID: {campaign_id}")
    print(f"Range: {args.since} → {args.until}")
    if dry_run:
        print("🔧 DRY RUN MODE")

    result = fetch_campaign_metrics(api, campaign_id, args.since, args.until)

    out = {
        "campaign_id": campaign_id,
        "since": args.since,
        "until": args.until,
        "insights": result.insights,
        "status": result.status,
    }

    out_path = f"campaign_{campaign_id}_{args.since}_to_{args.until}_insights.json".replace(':', '_')
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2)

    print(f"✓ Saved: {out_path}")
    return 0


def watch_meta_command(args):
    """Cron-friendly Meta monitoring with guardrails + Telegram-ready alerts."""
    import os
    from datetime import date, timedelta, datetime

    from src.integrations.meta_ads import MetaAdsAPI
    from src.integrations.meta_monitor import fetch_campaign_metrics
    from src.integrations.meta_watch import summarize_insights, evaluate_guardrails

    dep_path = Path(args.deployment_result)
    if not dep_path.exists():
        print(f"Error: deployment result not found: {dep_path}")
        return 1

    try:
        dep = json.loads(dep_path.read_text())
    except json.JSONDecodeError:
        print(f"Error: invalid JSON in deployment result: {dep_path}")
        return 1

    campaign_id = dep.get("campaign_id")
    if not campaign_id:
        print("Error: deployment result missing 'campaign_id'")
        print("Tip: re-run deploy-to-meta to generate a valid *_deployment_result.json")
        return 1

    guardrails = dep.get("guardrails") or {}
    daily_cap = guardrails.get("daily_cap")
    target_cpa = guardrails.get("target_cpa")

    # Allow overrides for older deployment files.
    if args.daily_cap is not None:
        daily_cap = args.daily_cap
    if args.target_cpa is not None:
        target_cpa = args.target_cpa

    # Validate guardrails (optional but recommended)
    if daily_cap is not None:
        try:
            daily_cap = float(daily_cap)
        except (TypeError, ValueError):
            print(f"Error: daily_cap must be a number. Got: {daily_cap!r}")
            return 1

    if target_cpa is not None:
        try:
            target_cpa = float(target_cpa)
        except (TypeError, ValueError):
            print(f"Error: target_cpa must be a number. Got: {target_cpa!r}")
            return 1

    dry_run = args.dry_run or os.getenv('META_DRY_RUN', '').lower() == 'true'
    sandbox_mode = os.getenv('META_SANDBOX_MODE', '').lower() == 'true'

    access_token = os.getenv('META_ACCESS_TOKEN')
    ad_account_id = os.getenv('META_AD_ACCOUNT_ID')
    page_id = os.getenv('META_PAGE_ID')
    instagram_actor_id = os.getenv('META_INSTAGRAM_ACTOR_ID')

    if sandbox_mode:
        access_token = os.getenv('META_SANDBOX_TOKEN') or access_token
        ad_account_id = os.getenv('META_SANDBOX_ACCOUNT_ID') or ad_account_id

    if not dry_run and not access_token:
        print("Error: META_ACCESS_TOKEN not set")
        return 1
    if not dry_run and not ad_account_id:
        print("Error: META_AD_ACCOUNT_ID not set")
        return 1

    api = MetaAdsAPI(
        access_token=access_token or "test_token",
        ad_account_id=ad_account_id or "act_test",
        page_id=page_id,
        instagram_actor_id=instagram_actor_id,
        dry_run=dry_run,
        sandbox_mode=sandbox_mode,
    )

    today = date.today()
    today_s = today.isoformat()
    trailing_start = (today - timedelta(days=7)).isoformat()
    trailing_end = (today - timedelta(days=1)).isoformat()

    print("=" * 60)
    print("  Meta Guardrail Watch")
    print("=" * 60)
    print(f"Campaign ID: {campaign_id}")
    print(f"Today: {today_s}")
    print(f"Trailing 7d: {trailing_start} → {trailing_end}")
    if daily_cap is not None:
        print(f"Guardrail daily cap: ${daily_cap:.2f}")
    if target_cpa is not None:
        print(f"Guardrail target CPA: ${target_cpa:.2f}")
    if dry_run:
        print("🔧 DRY RUN MODE")
    print()

    today_res = fetch_campaign_metrics(api, campaign_id, today_s, today_s)
    trailing_res = fetch_campaign_metrics(api, campaign_id, trailing_start, trailing_end)

    today_metrics = summarize_insights(today_res.insights)
    trailing_metrics = summarize_insights(trailing_res.insights)

    alerts = evaluate_guardrails(
        campaign_id=campaign_id,
        today=today_metrics,
        trailing_7d=trailing_metrics,
        daily_cap=daily_cap,
        target_cpa=target_cpa,
    )

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    snapshots_dir = Path("snapshots")
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    snap_path = snapshots_dir / f"{ts}.json"

    snapshot = {
        "timestamp": ts,
        "campaign_id": campaign_id,
        "today": {"date": today_s, **today_metrics},
        "trailing_7d": {"since": trailing_start, "until": trailing_end, **trailing_metrics},
        "guardrails": {"daily_cap": daily_cap, "target_cpa": target_cpa},
        "alerts": [a.__dict__ for a in alerts],
    }

    snap_path.write_text(json.dumps(snapshot, indent=2))

    # Telegram-friendly output (single message style)
    critical = [a for a in alerts if a.severity == "critical"]
    warning = [a for a in alerts if a.severity == "warning"]

    header = f"META WATCH | {campaign_id} | {today_s}"
    print(header)
    print("-" * len(header))
    cpa_val = today_metrics.get("cpa")
    cpa_str = "N/A" if cpa_val is None else f"${float(cpa_val):.2f}"
    print(
        f"Spend: ${today_metrics['spend']:.2f} | "
        f"CTR: {((today_metrics['ctr'] or 0)*100):.2f}% | "
        f"CPA: {cpa_str}"
    )

    if critical or warning:
        print("\nALERTS:")
        for a in alerts:
            if a.code == "OK":
                continue
            tag = "CRITICAL" if a.severity == "critical" else "WARNING"
            print(f"[{tag}] {a.message}")
            print(f"→ Suggested: {a.suggested_action}")
    else:
        print("\nOK: No guardrail breaches.")

    print(f"\n✓ Snapshot saved: {snap_path}")
    return 0


def setup_cron_command(args):
    """Print a crontab entry for hourly monitoring 9am-9pm."""
    repo_path = Path(args.repo_path or Path(__file__).resolve().parent)
    python_bin = args.python or "python3"

    if not args.deployment_result:
        print("Error: --deployment-result is required")
        return 1

    dep = Path(args.deployment_result)
    if not dep.is_absolute():
        dep = (Path.cwd() / dep).resolve()

    # 0 minutes, hours 9-21 inclusive.
    cron = (
        f"0 9-21 * * * cd {repo_path} && {python_bin} cli.py watch-meta "
        f"--deployment-result {dep} >> {repo_path}/snapshots/watch-meta.log 2>&1"
    )

    print("=" * 60)
    print("  Cron Setup Helper")
    print("=" * 60)
    print("Add this to your crontab (run: crontab -e):\n")
    print(cron)
    print("\nNotes:")
    print("  • Runs hourly from 9:00 through 21:00")
    print("  • Writes snapshots/ for alert history")
    print("  • Ensure env vars are available to cron (META_ACCESS_TOKEN, etc.)")
    return 0


def export_manual_guide_command(args):
    """Export manual ad setup guide from config file"""
    config_path = Path(args.config_path)

    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        return 1

    # Load config
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in config file: {config_path}")
        return 1

    meta_config = config.get("meta", {})
    if not meta_config:
        print("Error: No 'meta' section found in config")
        return 1

    # Generate manual guide
    output_path = args.output or config_path.stem + "_manual_setup.md"

    print("=" * 60)
    print("  Manual Meta Ads Setup Guide Generator")
    print("=" * 60)
    print()
    print(f"Reading config: {config_path}")
    print(f"Output file: {output_path}")
    print()

    # Generate checklist content
    guide_content = generate_manual_checklist(config)

    # Write to file
    with open(output_path, 'w') as f:
        f.write(guide_content)

    print(f"✓ Manual setup guide generated: {output_path}")
    print()
    print("Next steps:")
    print("  1. Open the generated markdown file")
    print("  2. Follow the checklist to create ads in Meta Ads Manager")
    print("  3. Check off items as you complete them")
    print()

    return 0


def generate_manual_checklist(config):
    """Generate customized manual checklist from config"""
    meta = config.get("meta", {})
    campaign_name = meta.get("campaign_name", "Untitled Campaign")
    daily_budget = meta.get("daily_budget", 0)
    objective = meta.get("objective", "CONVERSIONS")

    targeting = meta.get("targeting", {})
    age_range = targeting.get("age_range", "18-65")
    locations = targeting.get("locations", ["US"])
    detailed = targeting.get("detailed_targeting", {})
    interests = detailed.get("interests", [])
    behaviors = detailed.get("behaviors", [])

    placements = meta.get("placements", [])
    optimization = meta.get("optimization", {})
    bidding = meta.get("bidding", {})
    creative_specs = meta.get("creative_specs", {})
    schedule = meta.get("schedule", {})

    # Build checklist markdown
    md = f"""# Manual Meta Ads Setup Checklist
**Generated from config**: {campaign_name}

This checklist guides you through creating ads manually in Meta Ads Manager using your agent-generated config.

📖 **Full Documentation**: See `/docs/MANUAL_META_ADS_SETUP.md` for detailed instructions.

---

## Campaign: {campaign_name}

### Campaign Setup
- [ ] Log in to [Meta Ads Manager](https://business.facebook.com/adsmanager)
- [ ] Click **Create** campaign
- [ ] Select objective: **{objective}** ({"Sales/Conversions" if objective == "CONVERSIONS" else "Traffic" if objective == "OUTCOME_TRAFFIC" else objective})
- [ ] Campaign name: `{campaign_name}`
- [ ] Special ad categories: None (unless applicable)
- [ ] Click **Continue**

---

## Ad Set: {campaign_name} - Ad Set 1

### Budget & Schedule
- [ ] Daily budget: **${daily_budget:.2f}/day**
- [ ] Start date: {schedule.get("start_date", "Set to today or desired date")}
- [ ] End date: {"No end date" if not schedule.get("end_date") else schedule.get("end_date")}

### Audience Targeting

#### Locations
"""

    # Add locations
    for loc in locations:
        md += f"- [ ] Add location: **{loc}**\n"

    md += f"\n#### Demographics\n"
    md += f"- [ ] Age: **{age_range}**\n"
    md += f"- [ ] Gender: **{targeting.get('gender', 'All')}**\n"

    # Language
    if targeting.get("language"):
        md += f"- [ ] Language: **{targeting.get('language')}**\n"

    # Detailed targeting
    md += "\n#### Detailed Targeting\n"
    if interests:
        md += "**Interests** (add each):\n"
        for interest in interests:
            md += f"- [ ] {interest}\n"

    if behaviors:
        md += "\n**Behaviors** (add each):\n"
        for behavior in behaviors:
            md += f"- [ ] {behavior}\n"

    # Custom audiences
    custom = targeting.get("custom_audiences", [])
    if custom:
        md += "\n**Custom Audiences**:\n"
        for aud in custom:
            md += f"- [ ] {aud}\n"

    # Placements
    md += f"\n### Placements\n"
    md += "- [ ] Select **Manual Placements**\n"
    md += "- [ ] Uncheck **Automatic Placements**\n"
    md += "Check only these placements:\n"
    for placement in placements:
        md += f"- [ ] {placement}\n"

    # Optimization
    md += f"\n### Optimization & Delivery\n"
    opt_goal = optimization.get("optimization_goal", "CONVERSIONS")
    md += f"- [ ] Performance goal: **{opt_goal}**\n"

    if opt_goal == "CONVERSIONS":
        md += f"- [ ] Conversion event: **{optimization.get('pixel_event', 'Purchase')}**\n"

    attribution = optimization.get("conversion_window", "7_DAY_CLICK")
    md += f"- [ ] Attribution: **{attribution}**\n"

    # Bidding
    md += f"\n### Bidding Strategy\n"
    bid_strategy = bidding.get("strategy", "LOWEST_COST_WITHOUT_CAP")

    if bid_strategy == "LOWEST_COST_WITH_BID_CAP":
        bid_amount = bidding.get("bid_amount", 0)
        md += f"- [ ] Bid strategy: **Cost per result goal**\n"
        md += f"- [ ] Bid cap: **${bid_amount:.2f}**\n"
    else:
        md += f"- [ ] Bid strategy: **Highest volume** (no bid cap)\n"

    md += f"- [ ] Billing: **Impressions** (default)\n"

    # Creative
    md += f"\n---\n\n## Creative\n\n"
    md += "### Upload Media\n"

    formats = creative_specs.get("formats", ["Video or Image"])
    if isinstance(formats, list):
        formats_str = ", ".join(formats)
    else:
        formats_str = formats

    md += f"- [ ] Format: {formats_str}\n"

    duration = creative_specs.get("duration")
    if duration:
        md += f"- [ ] Duration: {duration}\n"

    aspect_ratio = creative_specs.get("aspect_ratio")
    if aspect_ratio:
        md += f"- [ ] Aspect ratio: {aspect_ratio}\n"

    md += "\n### Ad Copy\n"

    # Messaging
    messaging = creative_specs.get("messaging", [])
    if messaging:
        md += "**Primary Text** (use these themes):\n"
        for msg in messaging[:3]:  # First 3
            md += f"- {msg}\n"
        md += "\n- [ ] Write primary text incorporating above themes\n"
    else:
        md += "- [ ] Write primary text\n"

    # Headline
    headline = creative_specs.get("name")
    if headline:
        md += f"\n**Headline**:\n"
        md += f"- [ ] Enter: \"{headline}\"\n"
    else:
        md += f"- [ ] Enter headline (40 characters max)\n"

    # Destination & CTA
    md += f"\n### Destination\n"

    link = creative_specs.get("link", "https://your-website.com")
    md += f"- [ ] Website URL: `{link}`\n"

    cta_type = creative_specs.get("call_to_action", {}).get("type", "SHOP_NOW")
    md += f"- [ ] Call to Action: **{cta_type}**\n"

    # Instagram
    md += f"\n### Instagram (if using Instagram placements)\n"
    md += f"- [ ] Connect Instagram account\n"
    md += f"- [ ] Verify Instagram actor ID is set\n"

    # Review
    md += f"\n---\n\n## Review & Publish\n\n"
    md += f"- [ ] Review all settings against this checklist\n"
    md += f"- [ ] Generate ad preview for each placement\n"
    md += f"- [ ] Check image/video displays correctly\n"
    md += f"- [ ] Verify text not cut off\n"
    md += f"- [ ] Set status to **PAUSED**\n"
    md += f"- [ ] Click **Publish**\n"
    md += f"- [ ] Wait for ad review (24-48 hours)\n"
    md += f"- [ ] Check review status in Ads Manager\n"
    md += f"- [ ] Activate when approved\n"

    # Summary
    summary = config.get("summary", {})
    if summary:
        md += f"\n---\n\n## Campaign Summary\n\n"
        md += f"**Total Daily Budget**: ${summary.get('total_daily_budget', 0)}\n\n"

        experiment = summary.get("experiment")
        if experiment:
            md += f"**Experiment**: {experiment}\n\n"

        expected = summary.get("expected_outcomes", {})
        if expected:
            md += f"**Expected Outcomes**:\n"
            for key, value in expected.items():
                md += f"- {key}: {value}\n"

    md += f"\n---\n\n"
    md += f"**Generated by Adronaut Agent**\n\n"
    md += f"For detailed instructions, see: `/docs/MANUAL_META_ADS_SETUP.md`\n"

    return md


def test_creative_command(args):
    """Run test creative workflow"""
    from src.workflows.test_creative_workflow import (
        run_test_creative_workflow,
        save_test_creative_results
    )

    print_banner()
    print("🎨 TEST CREATIVE WORKFLOW")
    print("=" * 60)
    print()

    # Parse keywords if provided
    required_keywords = None
    if args.keywords:
        required_keywords = [k.strip() for k in args.keywords.split(",")]

    # Print input summary
    print("INPUT SUMMARY:")
    print(f"  Product: {args.product_description[:100]}{'...' if len(args.product_description) > 100 else ''}")
    if args.product_image:
        print(f"  Image: {args.product_image}")
    print(f"  Platform: {args.platform}")
    if args.audience:
        print(f"  Audience: {args.audience}")
    if args.creative_style:
        print(f"  Style: {args.creative_style}")
    if required_keywords:
        print(f"  Required keywords: {', '.join(required_keywords)}")
    if args.brand_name:
        print(f"  Brand name: {args.brand_name}")
    print()

    # Run workflow
    try:
        results = run_test_creative_workflow(
            product_description=args.product_description,
            product_image_path=args.product_image,
            platform=args.platform,
            audience=args.audience,
            creative_style=args.creative_style,
            required_keywords=required_keywords,
            brand_name=args.brand_name
        )

        # Display results
        print()
        display_test_creative_results(results)

        # Save results
        output_path = save_test_creative_results(
            results=results,
            output_path=args.output
        )

        print()
        print("=" * 60)
        print("  RESULTS SAVED")
        print("=" * 60)
        print(f"📄 JSON file: {output_path}")
        print()

        return 0

    except Exception as e:
        print()
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


def display_test_creative_results(results: dict):
    """Display test creative workflow results in terminal"""

    print("=" * 60)
    print("  WORKFLOW RESULTS")
    print("=" * 60)
    print()

    summary = results.get("summary", {})
    steps = results.get("workflow_steps", {})

    # Summary
    print("SUMMARY:")
    print(f"  Platform: {summary.get('platform', 'N/A')}")
    print(f"  Audience: {summary.get('audience', 'N/A')}")
    print(f"  Creative Style: {summary.get('creative_style', 'N/A')}")
    print(f"  Prompt Changed in Review: {'Yes' if summary.get('prompt_changed_in_review') else 'No'}")
    print(f"  Validation Passed: {'Yes ✓' if summary.get('validation_passed') else 'No ✗'}")
    print(f"  Final Score: {summary.get('final_score', 0)}/100")
    print()

    # Step 1: Generation
    step1 = steps.get("step1_generation", {})
    if step1:
        print("─" * 60)
        print("STEP 1: INITIAL GENERATION")
        print("─" * 60)
        print(f"Original Prompt Length: {len(step1.get('original_prompt', ''))} chars")
        print(f"Headline: {step1.get('copy_headline', 'N/A')}")
        print(f"Primary Text: {step1.get('copy_primary_text', 'N/A')[:100]}...")
        print(f"CTA: {step1.get('copy_cta', 'N/A')}")
        print(f"Hooks: {len(step1.get('hooks', []))} hooks generated")
        print()

    # Step 2: Review
    step2 = steps.get("step2_review", {})
    if step2:
        print("─" * 60)
        print("STEP 2: PROMPT REVIEW")
        print("─" * 60)
        print(f"Reviewed Prompt Length: {len(step2.get('reviewed_prompt', ''))} chars")
        print(f"Changed: {'Yes' if step2.get('changed') else 'No'}")
        if step2.get('review_notes'):
            print(f"Review Notes: {step2.get('review_notes')[:200]}{'...' if len(step2.get('review_notes', '')) > 200 else ''}")
        print()

    # Step 3: Creative
    step3 = steps.get("step3_creative", {})
    if step3:
        print("─" * 60)
        print("STEP 3: FINAL CREATIVE OUTPUT")
        print("─" * 60)
        print(f"Ready for Image Generation: {'Yes ✓' if step3.get('ready_for_image_generation') else 'No ✗'}")

        validation = step3.get("validation", {})
        if validation:
            print(f"Validation Status: {'Passed ✓' if validation.get('is_valid') else 'Failed ✗'}")
            if validation.get('errors'):
                print(f"Validation Warnings: {', '.join(validation.get('errors', []))}")

        print()
        print("FINAL VISUAL PROMPT:")
        print("─" * 60)
        prompt_text = step3.get('final_visual_prompt', '')
        # Display first 500 chars
        if len(prompt_text) > 500:
            print(prompt_text[:500] + "...")
            print(f"[Total length: {len(prompt_text)} chars]")
        else:
            print(prompt_text)
        print()

    # Step 4: Rating
    step4 = steps.get("step4_rating", {})
    if step4 and step4.get("success"):
        print("─" * 60)
        print("STEP 4: QUALITY RATING")
        print("─" * 60)
        print(f"Overall Score: {step4.get('overall_score', 0)}/100")
        print()

        # Category scores
        category_scores = step4.get("category_scores", {})
        if category_scores:
            print("Category Scores (0-10):")
            for category, score in category_scores.items():
                bar = "█" * score + "░" * (10 - score)
                print(f"  {category.replace('_', ' ').title():25s} {bar} {score}/10")
            print()

        # Keyword analysis
        keyword_analysis = step4.get("keyword_analysis", {})
        if keyword_analysis and not keyword_analysis.get("error"):
            print("Keyword Analysis:")
            found = keyword_analysis.get("required_keywords_found", [])
            missing = keyword_analysis.get("required_keywords_missing", [])
            if found:
                print(f"  ✓ Found: {', '.join(found)}")
            if missing:
                print(f"  ✗ Missing: {', '.join(missing)}")
            print()

        # Brand presence
        brand_presence = step4.get("brand_presence", {})
        if brand_presence and not brand_presence.get("error"):
            print("Brand Presence:")
            print(f"  Brand Mentioned: {'Yes ✓' if brand_presence.get('brand_mentioned') else 'No ✗'}")
            print(f"  Logo Described: {'Yes ✓' if brand_presence.get('logo_described') else 'No ✗'}")
            print(f"  Prominence: {brand_presence.get('prominence_level', 'N/A')}")
            print()

        # Strengths
        strengths = step4.get("strengths", [])
        if strengths:
            print("Strengths:")
            for strength in strengths:
                print(f"  ✓ {strength}")
            print()

        # Weaknesses
        weaknesses = step4.get("weaknesses", [])
        if weaknesses:
            print("Weaknesses:")
            for weakness in weaknesses:
                print(f"  ⚠ {weakness}")
            print()

        # Suggestions
        suggestions = step4.get("suggestions", [])
        if suggestions:
            print("Suggestions for Improvement:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"  {i}. {suggestion}")
            print()

    # Step 5: Image Generation
    step5 = steps.get("step5_image_generation", {})
    if step5:
        print("─" * 60)
        print("STEP 5: IMAGE GENERATION")
        print("─" * 60)
        if step5.get("success"):
            print(f"✓ Image Generated Successfully")
            print(f"Path: {step5.get('image_path')}")
            print(f"Model: {step5.get('model')}")
            print(f"Aspect Ratio: {step5.get('aspect_ratio')}")
        else:
            print(f"✗ Image Generation Failed")
            print(f"Error: {step5.get('error', 'Unknown error')}")
        print()

    # Step 6: Image Rating
    step6 = steps.get("step6_image_rating", {})
    if step6:
        print("─" * 60)
        print("STEP 6: IMAGE QUALITY RATING")
        print("─" * 60)

        if step6.get("success"):
            print(f"Overall Score: {step6.get('overall_score', 0)}/100")
            print()

            # Category scores
            category_scores = step6.get("category_scores", {})
            if category_scores:
                print("Category Scores (0-10):")
                for category, score in category_scores.items():
                    bar = "█" * score + "░" * (10 - score)
                    print(f"  {category.replace('_', ' ').title():25s} {bar} {score}/10")
                print()

            # Prompt match details
            prompt_match = step6.get("prompt_match_details", {})
            if prompt_match:
                print("Prompt Match Analysis:")
                matched = prompt_match.get("matched_elements", [])
                missing = prompt_match.get("missing_elements", [])
                if matched:
                    print(f"  ✓ Matched: {', '.join(matched[:3])}")
                if missing:
                    print(f"  ✗ Missing: {', '.join(missing[:3])}")
                print()

            # Strengths
            strengths = step6.get("strengths", [])
            if strengths:
                print("Image Strengths:")
                for strength in strengths:
                    print(f"  ✓ {strength}")
                print()

            # Weaknesses
            weaknesses = step6.get("weaknesses", [])
            if weaknesses:
                print("Image Weaknesses:")
                for weakness in weaknesses:
                    print(f"  ⚠ {weakness}")
                print()

            # Suggestions
            suggestions = step6.get("suggestions", [])
            if suggestions:
                print("Suggestions for Improvement:")
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"  {i}. {suggestion}")
                print()
        elif step6.get("skipped"):
            print(f"⚠ Image Review Skipped")
            print(f"Reason: {step6.get('reason', 'Unknown')}")
            print()
        else:
            # Failed
            print(f"✗ Image Review Failed")
            print(f"Error: {step6.get('error', 'Unknown error')}")
            print()


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
    run_parser.add_argument(
        "--inputs",
        help="Comma-separated local files/folders to process (recursive, ignores hidden)"
    )
    run_parser.add_argument(
        "--urls",
        help="Comma-separated product URLs to scrape"
    )

    # Test creative command
    test_creative_parser = subparsers.add_parser(
        "test-creative",
        help="Test creative generation workflow (generate → review → rate)"
    )
    test_creative_parser.add_argument(
        "--product-description",
        required=True,
        help="Description of the product/service to advertise"
    )
    test_creative_parser.add_argument(
        "--product-image",
        help="Path to product image (optional, for visual context)"
    )
    test_creative_parser.add_argument(
        "--platform",
        default="Meta",
        choices=["Meta", "TikTok", "Google"],
        help="Target advertising platform (default: Meta)"
    )
    test_creative_parser.add_argument(
        "--audience",
        help="Target audience description (optional)"
    )
    test_creative_parser.add_argument(
        "--creative-style",
        help="Creative style preference (optional)"
    )
    test_creative_parser.add_argument(
        "--keywords",
        help="Comma-separated list of required keywords to check for"
    )
    test_creative_parser.add_argument(
        "--brand-name",
        help="Brand name to check for presence in prompt"
    )
    test_creative_parser.add_argument(
        "--output",
        help="Custom output file path (default: output/test_creatives/test_creative_<timestamp>.json)"
    )

    # Deploy to Meta command
    deploy_parser = subparsers.add_parser(
        "deploy-to-meta",
        help="Deploy campaign config to Meta Ads via API"
    )
    deploy_parser.add_argument(
        "--config-path",
        required=True,
        help="Path to campaign config JSON file (e.g., campaign_xxx_v0.json)"
    )
    deploy_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test mode - log API calls without executing (no Meta API calls made)"
    )

    # Monitor Meta command
    monitor_parser = subparsers.add_parser(
        "monitor-meta",
        help="Fetch Meta campaign status + insights for a deployed campaign"
    )
    monitor_parser.add_argument(
        "--deployment-result",
        help="Path to *_deployment_result.json produced by deploy-to-meta"
    )
    monitor_parser.add_argument(
        "--campaign-id",
        help="Campaign ID (if you don't have a deployment result file)"
    )
    monitor_parser.add_argument(
        "--since",
        required=True,
        help="Start date (YYYY-MM-DD)"
    )
    monitor_parser.add_argument(
        "--until",
        required=True,
        help="End date (YYYY-MM-DD)"
    )
    monitor_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log what would be queried (no API calls)"
    )

    # Watch Meta command (cron-friendly guardrail monitoring)
    watch_parser = subparsers.add_parser(
        "watch-meta",
        help="Cron-friendly Meta monitoring with guardrails + Telegram-ready alerts"
    )
    watch_parser.add_argument(
        "--deployment-result",
        required=True,
        help="Path to *_deployment_result.json produced by deploy-to-meta"
    )
    watch_parser.add_argument(
        "--daily-cap",
        type=float,
        help="Override daily spend cap (defaults to deployment_result.guardrails.daily_cap)"
    )
    watch_parser.add_argument(
        "--target-cpa",
        type=float,
        help="Override target CPA (defaults to deployment_result.guardrails.target_cpa)"
    )
    watch_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log what would be queried (no API calls)"
    )

    # Cron setup helper
    cron_parser = subparsers.add_parser(
        "setup-cron",
        help="Print a crontab entry for hourly monitoring 9am-9pm"
    )
    cron_parser.add_argument(
        "--deployment-result",
        required=True,
        help="Path to *_deployment_result.json to monitor"
    )
    cron_parser.add_argument(
        "--repo-path",
        help="Repo path to cd into (default: this repo)"
    )
    cron_parser.add_argument(
        "--python",
        help="Python executable to use in cron (default: python3)"
    )

    # Export manual guide command
    export_parser = subparsers.add_parser(
        "export-manual-guide",
        help="Generate manual setup guide from campaign config"
    )
    export_parser.add_argument(
        "--config-path",
        required=True,
        help="Path to campaign config JSON file (e.g., campaign_xxx_v0.json)"
    )
    export_parser.add_argument(
        "--output",
        help="Output markdown file path (default: <config>_manual_setup.md)"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "run":
        return run_command(args)
    elif args.command == "test-creative":
        return test_creative_command(args)
    elif args.command == "deploy-to-meta":
        return deploy_to_meta_command(args)
    elif args.command == "monitor-meta":
        return monitor_meta_command(args)
    elif args.command == "watch-meta":
        return watch_meta_command(args)
    elif args.command == "setup-cron":
        return setup_cron_command(args)
    elif args.command == "export-manual-guide":
        return export_manual_guide_command(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
