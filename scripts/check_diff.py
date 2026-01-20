#!/usr/bin/env python3
"""Check for differences between the latest and previous snapshots."""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional


def get_snapshots() -> list[str]:
    """Get sorted list of snapshot files.

    Returns:
        List of snapshot filenames sorted by date (oldest first)
    """
    snapshots_dir = Path("snapshots")
    if not snapshots_dir.exists():
        return []

    snapshots = sorted([f.name for f in snapshots_dir.glob("*.html")])
    return snapshots


def calculate_diff(prev_file: str, latest_file: str) -> Optional[str]:
    """Calculate diff between two files.

    Args:
        prev_file: Path to previous snapshot
        latest_file: Path to latest snapshot

    Returns:
        Diff string if changes exist, None otherwise
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--no-index", "--unified=3", prev_file, latest_file],
            capture_output=True,
            text=True
        )

        # git diff returns exit code 1 when files differ
        if result.returncode == 1 and result.stdout:
            return result.stdout
        elif result.returncode > 1:
            print(f"❌ Error running git diff: {result.stderr}", file=sys.stderr)
            return None

        return None  # No changes

    except Exception as e:
        print(f"❌ Error calculating diff: {e}", file=sys.stderr)
        return None


def summarize_diff(diff_output: str) -> str:
    """Create a human-readable summary of changes.

    Args:
        diff_output: Raw diff output

    Returns:
        Summary string
    """
    lines = diff_output.split('\n')
    additions = sum(1 for line in lines if line.startswith('+') and not line.startswith('+++'))
    deletions = sum(1 for line in lines if line.startswith('-') and not line.startswith('---'))

    summary = f"📊 **変更サマリー**\n\n"
    summary += f"- 追加行: {additions}行\n"
    summary += f"- 削除行: {deletions}行\n"
    summary += f"- 合計変更: {additions + deletions}行\n"

    return summary


def main():
    """Main function to check for document changes."""
    snapshots = get_snapshots()

    if len(snapshots) < 2:
        print("ℹ️  Not enough snapshots to compare (need at least 2)")
        # Set output for GitHub Actions
        with open(os.environ.get('GITHUB_OUTPUT', '/dev/null'), 'a') as f:
            f.write("changed=false\n")
        sys.exit(0)

    # Compare latest with previous
    prev_snapshot = f"snapshots/{snapshots[-2]}"
    latest_snapshot = f"snapshots/{snapshots[-1]}"

    print(f"📝 Comparing:")
    print(f"  Previous: {snapshots[-2]}")
    print(f"  Latest:   {snapshots[-1]}")

    diff_output = calculate_diff(prev_snapshot, latest_snapshot)

    if diff_output:
        print("🚨 Changes detected!")

        # Create summary
        summary = summarize_diff(diff_output)
        with open("diff_summary.txt", "w", encoding="utf-8") as f:
            f.write(summary)

        # Save full diff (limit to 65KB for GitHub Issues)
        diff_truncated = diff_output[:65000]
        if len(diff_output) > 65000:
            diff_truncated += "\n\n... (差分が長すぎるため省略されました)"

        with open("diff_details.txt", "w", encoding="utf-8") as f:
            f.write(diff_truncated)

        # Set output for GitHub Actions
        with open(os.environ.get('GITHUB_OUTPUT', '/dev/null'), 'a') as f:
            f.write("changed=true\n")

        sys.exit(0)
    else:
        print("✅ No changes detected")

        # Set output for GitHub Actions
        with open(os.environ.get('GITHUB_OUTPUT', '/dev/null'), 'a') as f:
            f.write("changed=false\n")

        sys.exit(0)


if __name__ == "__main__":
    main()
