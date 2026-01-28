#!/usr/bin/env python3

"""Fail CI if code changes were made without updating key docs.

Heuristic:
- If changes include python source (src/**.py) or cli.py,
  require README.md and/or ARCHITECTURE.md to be updated too.
- If changes include storage/path/layout code, require FILE_STORAGE_ARCHITECTURE.md.

This is intentionally conservative; you can bypass by touching the relevant docs
(even with a small note).

Environment:
- Works in GitHub Actions on PRs and pushes.
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import List


def sh(cmd: List[str]) -> str:
    return subprocess.check_output(cmd, text=True).strip()


def changed_files(base: str, head: str) -> List[str]:
    out = sh(["git", "diff", "--name-only", f"{base}...{head}"])
    return [line for line in out.splitlines() if line.strip()]


def _ref_exists(ref: str) -> bool:
    try:
        sh(["git", "rev-parse", "--verify", ref])
        return True
    except Exception:
        return False


def _merge_base(a: str, b: str) -> str | None:
    try:
        return sh(["git", "merge-base", a, b])
    except Exception:
        return None


def main() -> int:
    base = os.environ.get("DOCS_CHECK_BASE")
    head = os.environ.get("DOCS_CHECK_HEAD") or "HEAD"

    # If base not provided (or invalid), pick a sane default.
    if not base or not _ref_exists(base):
        # Prefer comparing against the merge-base with origin/main when available.
        if _ref_exists("origin/main"):
            mb = _merge_base("origin/main", head)
            base = mb or "origin/main"
        else:
            # Fallback for shallow/fork setups: compare to previous commit.
            base = "HEAD~1" if _ref_exists("HEAD~1") else head

    files = changed_files(base, head)
    if not files:
        print("No changed files detected")
        return 0

    changed = set(files)

    touches_code = any(
        f == "cli.py" or (f.startswith("src/") and f.endswith(".py"))
        for f in changed
    )

    touches_storage_layout = any(
        f.startswith("src/storage/") or "paths.py" in f or "file_manager.py" in f
        for f in changed
    )

    docs_touched = {
        "README.md": "README.md" in changed,
        "ARCHITECTURE.md": "ARCHITECTURE.md" in changed,
        "FILE_STORAGE_ARCHITECTURE.md": "FILE_STORAGE_ARCHITECTURE.md" in changed,
    }

    missing = []

    if touches_code:
        # Require at least one of the main docs
        if not (docs_touched["README.md"] or docs_touched["ARCHITECTURE.md"]):
            missing.append("README.md or ARCHITECTURE.md")

    if touches_storage_layout:
        if not docs_touched["FILE_STORAGE_ARCHITECTURE.md"]:
            missing.append("FILE_STORAGE_ARCHITECTURE.md")

    if missing:
        print("\nDocs check failed.")
        print("Changed files:")
        for f in files:
            print(f"  - {f}")
        print("\nMissing required doc updates:")
        for m in missing:
            print(f"  - {m}")
        print("\nTip: add a short note in the doc(s) describing the change.")
        return 1

    print("Docs check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
