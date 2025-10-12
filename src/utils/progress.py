"""
Progress tracking and visualization utilities
"""

import time
from typing import Optional, Dict, Any
from datetime import datetime


class Colors:
    """ANSI color codes for terminal output"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'


class ProgressTracker:
    """Track and display progress of agent execution"""

    def __init__(self, verbose: bool = True):
        """
        Initialize progress tracker

        Args:
            verbose: Whether to display detailed progress
        """
        self.verbose = verbose
        self.start_time = None
        self.node_start_time = None
        self.current_node = None
        self.node_count = 0

    def start(self):
        """Start tracking"""
        self.start_time = time.time()
        self._print_header()

    def _print_header(self):
        """Print session header"""
        if not self.verbose:
            return

        print()
        print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 80}{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}  🚀 Campaign Agent Execution Started{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 80}{Colors.RESET}")
        print()

    def node_start(self, node_name: str):
        """
        Mark start of node execution

        Args:
            node_name: Name of the node starting
        """
        if not self.verbose:
            return

        self.current_node = node_name
        self.node_start_time = time.time()
        self.node_count += 1

        # Format node name for display
        display_name = node_name.replace('_', ' ').title()

        print()
        print(f"{Colors.BLUE}{Colors.BOLD}[{self.node_count}] {display_name}{Colors.RESET}")
        print(f"{Colors.GRAY}{'─' * 80}{Colors.RESET}")

    def node_end(self, node_name: str, result: Optional[Dict[str, Any]] = None):
        """
        Mark end of node execution

        Args:
            node_name: Name of the node that ended
            result: Optional result data from node
        """
        if not self.verbose or not self.node_start_time:
            return

        duration = time.time() - self.node_start_time

        print(f"{Colors.GREEN}✓ Completed in {duration:.2f}s{Colors.RESET}")

        # Show key results if available
        if result:
            if "messages" in result and result["messages"]:
                last_msg = result["messages"][-1]
                print(f"{Colors.DIM}  → {last_msg}{Colors.RESET}")

    def llm_call_start(self, task_name: str, prompt_preview: str):
        """
        Mark start of LLM call

        Args:
            task_name: Name of the LLM task
            prompt_preview: Preview of the prompt (first 100 chars)
        """
        if not self.verbose:
            return

        print(f"{Colors.MAGENTA}  🤖 LLM Call: {task_name}{Colors.RESET}")
        print(f"{Colors.DIM}  Prompt: {prompt_preview[:100]}...{Colors.RESET}")

    def llm_call_end(self, task_name: str, duration: float, response_preview: str):
        """
        Mark end of LLM call

        Args:
            task_name: Name of the LLM task
            duration: Duration in seconds
            response_preview: Preview of response (first 100 chars)
        """
        if not self.verbose:
            return

        print(f"{Colors.MAGENTA}  ✓ LLM Response in {duration:.2f}s{Colors.RESET}")
        print(f"{Colors.DIM}  Response: {response_preview[:100]}...{Colors.RESET}")

    def log_message(self, message: str, level: str = "info"):
        """
        Log a message with appropriate color

        Args:
            message: Message to log
            level: Message level (info, success, warning, error)
        """
        if not self.verbose:
            return

        color_map = {
            "info": Colors.WHITE,
            "success": Colors.GREEN,
            "warning": Colors.YELLOW,
            "error": Colors.RED,
            "debug": Colors.GRAY,
        }

        color = color_map.get(level, Colors.WHITE)
        icon_map = {
            "info": "ℹ",
            "success": "✓",
            "warning": "⚠",
            "error": "✗",
            "debug": "•",
        }
        icon = icon_map.get(level, "•")

        print(f"{color}  {icon} {message}{Colors.RESET}")

    def finish(self):
        """Mark end of execution"""
        if not self.verbose or not self.start_time:
            return

        total_duration = time.time() - self.start_time

        print()
        print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 80}{Colors.RESET}")
        print(f"{Colors.GREEN}{Colors.BOLD}  ✓ Execution Complete{Colors.RESET}")
        print(f"{Colors.GRAY}  Total time: {total_duration:.2f}s{Colors.RESET}")
        print(f"{Colors.GRAY}  Nodes executed: {self.node_count}{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 80}{Colors.RESET}")
        print()


# Global progress tracker instance
_progress_tracker: Optional[ProgressTracker] = None


def get_progress_tracker() -> ProgressTracker:
    """
    Get or create global progress tracker

    Returns:
        ProgressTracker instance
    """
    global _progress_tracker
    if _progress_tracker is None:
        _progress_tracker = ProgressTracker(verbose=True)
    return _progress_tracker


def set_verbose(verbose: bool):
    """
    Set verbosity for progress tracking

    Args:
        verbose: Whether to show detailed progress
    """
    global _progress_tracker
    if _progress_tracker is not None:
        _progress_tracker.verbose = verbose
