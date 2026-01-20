#!/usr/bin/env python3
"""Generate visual diff viewer pages for GitHub Pages."""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, List


def copy_snapshots_to_docs():
    """Copy latest snapshots to docs directory for GitHub Pages."""
    snapshots_dir = Path("snapshots")
    docs_snapshots_dir = Path("docs/snapshots")

    docs_snapshots_dir.mkdir(parents=True, exist_ok=True)

    if not snapshots_dir.exists():
        print("⚠️  No snapshots directory found")
        return []

    snapshot_files = sorted(snapshots_dir.glob("*.html"))

    for snapshot in snapshot_files:
        dest = docs_snapshots_dir / snapshot.name
        shutil.copy2(snapshot, dest)
        print(f"📄 Copied {snapshot.name}")

    return [f.stem for f in snapshot_files]


def read_diff_stats() -> Dict:
    """Read diff statistics from files."""
    stats = {
        "additions": 0,
        "deletions": 0,
        "summary": ""
    }

    # Read diff summary
    summary_path = Path("diff_summary.txt")
    if summary_path.exists():
        with open(summary_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Parse additions and deletions
            for line in content.split('\n'):
                if '追加行:' in line:
                    stats["additions"] = int(''.join(filter(str.isdigit, line)))
                elif '削除行:' in line:
                    stats["deletions"] = int(''.join(filter(str.isdigit, line)))

    return stats


def update_changes_index(date: str, prev_date: str, stats: Dict):
    """Update the changes index in index.html."""
    index_path = Path("docs/index.html")

    if not index_path.exists():
        print("❌ docs/index.html not found")
        return

    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Create new change entry
    new_change = {
        "date": date,
        "prevDate": prev_date,
        "additions": stats["additions"],
        "deletions": stats["deletions"],
        "summary": "ドキュメント更新"
    }

    # Find the changesData array and prepend new entry
    marker = "const changesData = ["
    if marker in content:
        insert_pos = content.index(marker) + len(marker)

        # Format the new entry
        entry_json = json.dumps(new_change, ensure_ascii=False, indent=12)

        # Insert at the beginning of the array
        updated_content = (
            content[:insert_pos] +
            "\n" + entry_json + "," +
            content[insert_pos:]
        )

        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        print(f"✅ Updated index.html with change entry for {date}")
    else:
        print("⚠️  Could not find changesData marker in index.html")


def generate_viewer_page(date: str, prev_date: str, stats: Dict):
    """Generate a specific diff viewer page."""
    viewer_template = Path("docs/viewer.html")
    output_path = Path(f"docs/diffs/{date}.html")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not viewer_template.exists():
        print("❌ docs/viewer.html template not found")
        return

    with open(viewer_template, 'r', encoding='utf-8') as f:
        content = f.read()

    # Read diff details
    diff_details = ""
    diff_path = Path("diff_details.txt")
    if diff_path.exists():
        with open(diff_path, 'r', encoding='utf-8') as f:
            diff_details = f.read()

    # Escape for JavaScript string
    diff_details_escaped = json.dumps(diff_details)

    # Update configuration in the viewer
    config_update = f"""
        const config = {{
            date: '{date}',
            prevDate: '{prev_date}',
            additions: {stats['additions']},
            deletions: {stats['deletions']},
            diffContent: {diff_details_escaped}
        }};
    """

    # Replace the config section
    config_marker = "const config = {"
    if config_marker in content:
        start = content.index(config_marker)
        end = content.index("};", start) + 2
        updated_content = content[:start] + config_update + content[end:]

        # Fix relative paths for diffs subdirectory
        # Change href="index.html" to href="../index.html"
        updated_content = updated_content.replace('href="index.html"', 'href="../index.html"')
        # Fix snapshots path: snapshots/ -> ../snapshots/
        updated_content = updated_content.replace('`snapshots/${', '`../snapshots/${')

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        print(f"✅ Generated viewer page: {output_path}")
    else:
        # If marker not found, just copy the template
        shutil.copy2(viewer_template, output_path)
        print(f"⚠️  Generated basic viewer page (config not updated): {output_path}")


def main():
    """Main function to generate all viewer pages."""
    print("🚀 Generating visual diff viewer...")

    # Copy snapshots to docs
    dates = copy_snapshots_to_docs()

    if len(dates) < 2:
        print("ℹ️  Need at least 2 snapshots to generate diff viewer")
        sys.exit(0)

    # Get latest two dates
    latest_date = dates[-1]
    prev_date = dates[-2]

    print(f"📊 Creating diff viewer: {prev_date} → {latest_date}")

    # Read diff stats
    stats = read_diff_stats()

    # Generate viewer page
    generate_viewer_page(latest_date, prev_date, stats)

    # Update index
    update_changes_index(latest_date, prev_date, stats)

    print("✅ Diff viewer generation complete!")
    print(f"🌐 View at: https://YOUR_USERNAME.github.io/ntt-scp-doc-monitor/diffs/{latest_date}.html")


if __name__ == "__main__":
    main()
