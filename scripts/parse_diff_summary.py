#!/usr/bin/env python3
"""Parse diff and generate human-readable change summary."""

import re
from pathlib import Path
from typing import List, Dict


def extract_section_context(lines: List[str], start_idx: int, max_lines: int = 20) -> str:
    """Extract surrounding context to identify the section.

    Args:
        lines: All lines from the diff
        start_idx: Index of the change
        max_lines: Max lines to look back

    Returns:
        Section identifier (e.g., "1.2 サービスメニュー")
    """
    # Look backwards for section headers (h1-h6)
    for i in range(max(0, start_idx - max_lines), start_idx):
        line = lines[i]

        # Match HTML headings
        h_match = re.search(r'<h[1-6][^>]*>(.*?)</h[1-6]>', line)
        if h_match:
            heading_text = re.sub(r'<[^>]+>', '', h_match.group(1)).strip()
            return heading_text

        # Match markdown-style headings
        if re.match(r'^\+?\s*#{1,6}\s+(.+)', line):
            return re.match(r'^\+?\s*#{1,6}\s+(.+)', line).group(1).strip()

    return "不明なセクション"


def identify_change_type(added_lines: List[str], removed_lines: List[str]) -> str:
    """Identify what type of change occurred.

    Args:
        added_lines: Lines that were added
        removed_lines: Lines that were removed

    Returns:
        Description of change type
    """
    added_text = ' '.join(added_lines).lower()
    removed_text = ' '.join(removed_lines).lower()

    # Check for specific patterns
    if 'warning' in added_text or 'admonition warning' in added_text:
        return "Warning"
    elif 'note' in added_text or 'admonition note' in added_text:
        return "Note"
    elif 'table' in added_text or '<td>' in added_text:
        return "テーブル"
    elif 'nav' in added_text or 'menu' in added_text:
        return "ナビゲーション"
    elif '<h' in added_text:
        return "見出し"
    elif '<li>' in added_text:
        return "リスト項目"
    elif '<p>' in added_text:
        return "段落"
    else:
        return "コンテンツ"


def parse_diff_summary(diff_path: Path) -> List[Dict[str, str]]:
    """Parse diff file and extract change summary.

    Args:
        diff_path: Path to diff file

    Returns:
        List of change descriptions with line numbers
    """
    if not diff_path.exists():
        return []

    with open(diff_path, 'r', encoding='utf-8') as f:
        diff_content = f.read()

    lines = diff_content.split('\n')
    changes = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Find chunk headers (@@)
        chunk_match = re.match(r'^@@ -(\d+),?\d* \+(\d+),?\d* @@', line)
        if chunk_match:
            old_line = int(chunk_match.group(1))
            new_line = int(chunk_match.group(2))

            # Collect changes in this chunk
            added_lines = []
            removed_lines = []
            chunk_start = i

            i += 1
            while i < len(lines) and not lines[i].startswith('@@'):
                if lines[i].startswith('+') and not lines[i].startswith('+++'):
                    added_lines.append(lines[i][1:])
                elif lines[i].startswith('-') and not lines[i].startswith('---'):
                    removed_lines.append(lines[i][1:])
                i += 1

            # Only process if there are actual changes
            if added_lines or removed_lines:
                section = extract_section_context(lines, chunk_start)
                change_type = identify_change_type(added_lines, removed_lines)

                # Extract meaningful preview text
                preview_text = ""
                if added_lines:
                    # Get first meaningful line
                    for line in added_lines:
                        text = re.sub(r'<[^>]+>', '', line).strip()
                        if text and len(text) > 5:
                            preview_text = text[:100] + ("..." if len(text) > 100 else "")
                            break

                change_desc = {
                    'section': section,
                    'type': change_type,
                    'line': new_line,
                    'preview': preview_text,
                    'additions': len(added_lines),
                    'deletions': len(removed_lines)
                }

                changes.append(change_desc)

            continue

        i += 1

    return changes


def generate_summary_json(changes: List[Dict[str, str]], output_path: Path) -> None:
    """Generate JSON summary file.

    Args:
        changes: List of change descriptions
        output_path: Path to output JSON file
    """
    import json

    summary = {
        'total_changes': len(changes),
        'changes': changes
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"✅ Generated summary: {output_path}")


def main():
    """Main function."""
    diff_path = Path("diff_details.txt")
    output_path = Path("diff_summary.json")

    if not diff_path.exists():
        print("❌ diff_details.txt not found")
        return

    print("🔍 Parsing diff file...")
    changes = parse_diff_summary(diff_path)

    print(f"📊 Found {len(changes)} change(s):")
    for i, change in enumerate(changes, 1):
        print(f"\n{i}. {change['section']} > {change['type']}")
        print(f"   Line: {change['line']}")
        print(f"   Changes: +{change['additions']} -{change['deletions']}")
        if change['preview']:
            print(f"   Preview: {change['preview']}")

    generate_summary_json(changes, output_path)


if __name__ == "__main__":
    main()
