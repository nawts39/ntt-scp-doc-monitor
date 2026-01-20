#!/usr/bin/env python3
"""Parse diff and generate human-readable change summary."""

import re
from pathlib import Path
from typing import List, Dict, Tuple


def extract_section_context(lines: List[str], start_idx: int, max_lines: int = 200) -> str:
    """Extract surrounding context to identify the section.

    Args:
        lines: All lines from the diff
        start_idx: Index of the change
        max_lines: Max lines to look back

    Returns:
        Section identifier (e.g., "1.2 サービスメニュー")
    """
    # Look backwards for section headers (h1-h6)
    # Prioritize h3-h4 (subsections), then h2, then h1
    found_headings = []

    for i in range(max(0, start_idx - max_lines), start_idx):
        line = lines[i]

        # Skip deleted lines
        if line.startswith('-') and not line.startswith('---'):
            continue

        # Match HTML headings with id attributes
        h_match = re.search(r'<h([1-6])[^>]*id=["\']([^"\']+)["\'][^>]*>', line)
        if h_match:
            level = int(h_match.group(1))
            # Look for the next line with actual heading text
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                # Remove leading + if present, and strip HTML tags
                heading_text = re.sub(r'<[^>]+>', '', next_line.lstrip('+ ')).strip()
                if heading_text and len(heading_text) > 0:
                    found_headings.append((level, heading_text, i))
                    continue

        # Match complete heading tags on single line
        h_match_single = re.search(r'<h[1-6][^>]*>(.*?)</h[1-6]>', line)
        if h_match_single:
            heading_text = re.sub(r'<[^>]+>', '', h_match_single.group(1)).strip()
            if heading_text and len(heading_text) > 0:
                level = int(re.search(r'<h([1-6])', line).group(1))
                found_headings.append((level, heading_text, i))
                continue

        # Match markdown-style headings
        md_match = re.match(r'^\+?\s*(#{1,6})\s+(.+)', line)
        if md_match:
            level = len(md_match.group(1))
            heading_text = md_match.group(2).strip()
            found_headings.append((level, heading_text, i))

    # Return the most recent h2-h4 heading (closest to the change)
    if found_headings:
        # Prefer h2-h4 (section/subsection level)
        section_headings = [(lvl, txt, idx) for lvl, txt, idx in found_headings if 2 <= lvl <= 4]
        if section_headings:
            return section_headings[-1][1]  # Return text of the closest one
        # Fallback to any heading
        return found_headings[-1][1]

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


def get_section_from_snapshot(snapshot_path: Path, line_number: int) -> Tuple[str, str]:
    """Get section name and anchor ID from snapshot HTML file.

    Args:
        snapshot_path: Path to the snapshot HTML file
        line_number: Line number in the snapshot

    Returns:
        Tuple of (section_name, anchor_id)
    """
    if not snapshot_path.exists():
        return ("不明なセクション", "")

    with open(snapshot_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Look backwards from the line to find the nearest heading with id
    for i in range(min(line_number - 1, len(lines) - 1), max(0, line_number - 500), -1):
        line = lines[i]

        # Match heading tags with id attribute
        h_match = re.search(r'<h([2-4])[^>]*id=["\']([^"\']+)["\'][^>]*>', line)
        if h_match:
            level = int(h_match.group(1))
            anchor_id = h_match.group(2)

            # Get heading text from next line
            if i + 1 < len(lines):
                heading_text = re.sub(r'<[^>]+>', '', lines[i + 1]).strip()
                if heading_text:
                    return (heading_text, anchor_id)

    return ("不明なセクション", "")


def extract_anchor_id(lines: List[str], chunk_start: int, max_lines: int = 100) -> str:
    """Extract the closest HTML id or anchor for navigation.

    Args:
        lines: All lines from the diff
        chunk_start: Index of the chunk
        max_lines: Max lines to look back

    Returns:
        HTML id attribute (e.g., "12" for section 1.2)
    """
    for i in range(max(0, chunk_start - max_lines), chunk_start):
        line = lines[i]

        # Skip deleted lines
        if line.startswith('-') and not line.startswith('---'):
            continue

        # Match id attributes in any tag
        id_match = re.search(r'id=["\']([^"\']+)["\']', line)
        if id_match:
            return id_match.group(1)

    return ""


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
                anchor_id = extract_anchor_id(lines, chunk_start)

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
                    'deletions': len(removed_lines),
                    'anchor': anchor_id
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

    # Enhance with snapshot data
    snapshot_files = sorted(Path("snapshots").glob("*.html"))
    if len(snapshot_files) >= 1:
        latest_snapshot = snapshot_files[-1]
        print(f"📄 Reading section info from {latest_snapshot.name}")

        for change in changes:
            section_name, anchor_id = get_section_from_snapshot(latest_snapshot, change['line'])
            if section_name != "不明なセクション":
                change['section'] = section_name
            if anchor_id:
                change['anchor'] = anchor_id

    print(f"📊 Found {len(changes)} change(s):")
    for i, change in enumerate(changes, 1):
        print(f"\n{i}. {change['section']} > {change['type']}")
        print(f"   Line: {change['line']}")
        print(f"   Changes: +{change['additions']} -{change['deletions']}")
        if change.get('anchor'):
            print(f"   Anchor: #{change['anchor']}")
        if change['preview']:
            print(f"   Preview: {change['preview']}")

    generate_summary_json(changes, output_path)


if __name__ == "__main__":
    main()
