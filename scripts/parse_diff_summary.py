#!/usr/bin/env python3
"""Advanced diff parser with HTML structure-aware change detection.

This version detects changes at a semantic level, splitting chunks into
individual logical units (table rows, list items, paragraphs, etc.)
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict


@dataclass
class Change:
    """Represents a single semantic change."""
    section: str
    type: str
    line: int
    preview: str
    additions: int
    deletions: int
    anchor: str
    detail: str = ""  # Additional context
    html_element: str = ""  # e.g., "table_row", "list_item", "paragraph"


class HTMLStructureDetector:
    """Detects HTML structural elements in diff lines."""

    @staticmethod
    def detect_element_type(lines: List[str]) -> str:
        """Detect the type of HTML element in the given lines."""
        combined = ' '.join(lines).lower()

        # Priority order matters
        if '<tr>' in combined or '<td>' in combined:
            return "table_row"
        elif '<li>' in combined:
            return "list_item"
        elif '<h1' in combined or '<h2' in combined or '<h3' in combined:
            return "heading"
        elif '<p>' in combined or '<p ' in combined:
            return "paragraph"
        elif '<div class="admonition' in combined:
            return "admonition"
        elif 'class="md-nav' in combined:
            return "navigation"
        elif '<a' in combined and 'href=' in combined:
            return "link"
        else:
            return "content"

    @staticmethod
    def find_element_boundaries(lines: List[str]) -> List[Tuple[int, int]]:
        """Find boundaries of logical HTML elements in diff lines.

        Returns:
            List of (start_idx, end_idx) tuples for each element
        """
        boundaries = []
        current_start = None
        current_element = None
        stack = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Opening tags that define element boundaries
            if re.search(r'<(tr|li|p|div|h[1-6])[\s>]', stripped):
                tag_match = re.search(r'<(tr|li|p|div|h[1-6])[\s>]', stripped)
                tag = tag_match.group(1)

                if not current_start:
                    current_start = i
                    current_element = tag
                stack.append(tag)

            # Closing tags
            if re.search(r'</(tr|li|p|div|h[1-6])>', stripped):
                tag_match = re.search(r'</(tr|li|p|div|h[1-6])>', stripped)
                tag = tag_match.group(1)

                if stack and stack[-1] == tag:
                    stack.pop()

                    # If stack is empty, we've closed the element
                    if not stack and current_start is not None:
                        boundaries.append((current_start, i + 1))
                        current_start = None
                        current_element = None

        # If we have an unclosed element, add it
        if current_start is not None:
            boundaries.append((current_start, len(lines)))

        # If no boundaries found, treat entire block as one element
        if not boundaries and lines:
            boundaries.append((0, len(lines)))

        return boundaries


class SemanticChangeDetector:
    """Detects semantic changes by analyzing HTML structure."""

    def __init__(self, snapshot_path: Path):
        self.snapshot_path = snapshot_path
        self.snapshot_lines = []
        if snapshot_path.exists():
            with open(snapshot_path, 'r', encoding='utf-8') as f:
                self.snapshot_lines = f.readlines()

    def get_section_info(self, line_number: int) -> Tuple[str, str]:
        """Get section name and anchor ID from snapshot."""
        if not self.snapshot_lines:
            return ("不明なセクション", "")

        # Look backwards for nearest heading
        for i in range(min(line_number - 1, len(self.snapshot_lines) - 1),
                      max(0, line_number - 500), -1):
            line = self.snapshot_lines[i]

            # Match h2-h4 with id
            h_match = re.search(r'<h([2-4])[^>]*id=["\']([^"\']+)["\'][^>]*>', line)
            if h_match:
                level = int(h_match.group(1))
                anchor_id = h_match.group(2)

                # Get heading text
                if i + 1 < len(self.snapshot_lines):
                    heading_text = re.sub(r'<[^>]+>', '', self.snapshot_lines[i + 1]).strip()
                    if heading_text:
                        return (heading_text, anchor_id)

        return ("不明なセクション", "")

    def split_chunk_into_changes(self,
                                 chunk_start_line: int,
                                 added_lines: List[str],
                                 removed_lines: List[str],
                                 context_lines: List[str] = None) -> List[Change]:
        """Split a single diff chunk into multiple semantic changes."""
        changes = []

        # Use context lines to determine element type
        all_context = context_lines if context_lines else []

        # Check if we're inside a table row by looking at immediate context
        # Need to see <tr> or <td> in close proximity
        recent_context = all_context[-5:] if len(all_context) > 5 else all_context
        in_table_row = any('<tr>' in line or '<td>' in line for line in recent_context)

        # Analyze added lines
        if added_lines:
            added_boundaries = HTMLStructureDetector.find_element_boundaries(added_lines)

            for start, end in added_boundaries:
                element_lines = added_lines[start:end]

                # First, get natural element type
                element_type = HTMLStructureDetector.detect_element_type(element_lines)

                # Override only if we're in a table row AND element doesn't have clear type
                if (in_table_row and
                    element_type == "content" and
                    '<tr>' not in ' '.join(element_lines) and
                    '<p>' not in ' '.join(element_lines) and
                    '<div' not in ' '.join(element_lines)):
                    element_type = "table_row"

                # Get preview text
                preview = self._extract_preview_text(element_lines)

                # Get section info
                section, anchor = self.get_section_info(chunk_start_line)

                # Determine change type
                change_type = self._classify_change_type(element_type, element_lines)

                change = Change(
                    section=section,
                    type=change_type,
                    line=chunk_start_line,
                    preview=preview,
                    additions=len(element_lines),
                    deletions=0,
                    anchor=anchor,
                    html_element=element_type
                )
                changes.append(change)

        # Analyze removed lines
        if removed_lines:
            removed_boundaries = HTMLStructureDetector.find_element_boundaries(removed_lines)

            for start, end in removed_boundaries:
                element_lines = removed_lines[start:end]

                # First, get natural element type
                element_type = HTMLStructureDetector.detect_element_type(element_lines)

                # Override only if we're in a table row AND element doesn't have clear type
                if (in_table_row and
                    element_type == "content" and
                    '<tr>' not in ' '.join(element_lines) and
                    '<p>' not in ' '.join(element_lines) and
                    '<div' not in ' '.join(element_lines)):
                    element_type = "table_row"

                # Get preview text
                preview = self._extract_preview_text(element_lines)

                # Get section info
                section, anchor = self.get_section_info(chunk_start_line)

                # Determine change type
                change_type = self._classify_change_type(element_type, element_lines, is_deletion=True)

                change = Change(
                    section=section,
                    type=change_type,
                    line=chunk_start_line,
                    preview=preview,
                    additions=0,
                    deletions=len(element_lines),
                    anchor=anchor,
                    html_element=element_type
                )
                changes.append(change)

        # Merge small changes if they're part of the same logical unit
        changes = self._merge_related_changes(changes)

        return changes

    def _extract_preview_text(self, lines: List[str], max_length: int = 150) -> str:
        """Extract meaningful preview text from HTML lines."""
        # Remove HTML tags and extract text
        text_parts = []
        for line in lines:
            # Skip pure structural tags
            if re.match(r'^\s*</?[^>]+>\s*$', line):
                continue

            # Extract text content
            text = re.sub(r'<[^>]+>', '', line).strip()
            if text and len(text) > 3:
                text_parts.append(text)

        preview = ' '.join(text_parts)
        preview = re.sub(r'\s+', ' ', preview).strip()

        if len(preview) > max_length:
            preview = preview[:max_length] + "..."

        return preview

    def _classify_change_type(self, element_type: str, lines: List[str],
                              is_deletion: bool = False) -> str:
        """Classify the type of change with human-readable labels."""
        combined = ' '.join(lines).lower()

        prefix = "削除: " if is_deletion else "追加: "

        # Specific patterns
        if 'admonition warning' in combined or 'class="admonition warning' in combined:
            return f"{prefix}Warning"
        elif 'admonition note' in combined:
            return f"{prefix}Note"
        elif element_type == "table_row":
            return f"{prefix}テーブル行"
        elif element_type == "list_item":
            return f"{prefix}リスト項目"
        elif element_type == "heading":
            if is_deletion:
                return "見出し変更（旧）"
            else:
                return "見出し変更（新）"
        elif element_type == "navigation":
            return f"{prefix}ナビゲーション"
        elif element_type == "paragraph":
            return f"{prefix}段落"
        elif element_type == "admonition":
            return f"{prefix}注意書き"
        else:
            return f"{prefix}コンテンツ"

    def _merge_related_changes(self, changes: List[Change]) -> List[Change]:
        """Merge changes that are part of the same logical modification."""
        if len(changes) <= 1:
            return changes

        merged = []
        i = 0

        while i < len(changes):
            current = changes[i]

            # Check if next change is a paired modification (add + delete of same type)
            if (i + 1 < len(changes) and
                changes[i + 1].html_element == current.html_element and
                changes[i + 1].section == current.section and
                current.additions > 0 and changes[i + 1].deletions > 0):

                # This is a modification (not pure add/delete)
                next_change = changes[i + 1]

                merged_change = Change(
                    section=current.section,
                    type=f"変更: {current.html_element}",
                    line=current.line,
                    preview=f"[旧] {next_change.preview} → [新] {current.preview}",
                    additions=current.additions,
                    deletions=next_change.deletions,
                    anchor=current.anchor,
                    html_element=current.html_element
                )
                merged.append(merged_change)
                i += 2
            else:
                merged.append(current)
                i += 1

        return merged


def parse_diff_advanced(diff_path: Path, snapshot_path: Path) -> List[Dict]:
    """Parse diff with advanced semantic change detection."""
    if not diff_path.exists():
        return []

    with open(diff_path, 'r', encoding='utf-8') as f:
        diff_content = f.read()

    lines = diff_content.split('\n')
    detector = SemanticChangeDetector(snapshot_path)
    all_changes = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Find chunk headers (@@)
        chunk_match = re.match(r'^@@ -(\d+),?\d* \+(\d+),?\d* @@', line)
        if chunk_match:
            old_line = int(chunk_match.group(1))
            new_line = int(chunk_match.group(2))

            # Collect all added, removed, and context lines in this chunk
            added_lines = []
            removed_lines = []
            context_lines = []

            i += 1
            while i < len(lines) and not lines[i].startswith('@@'):
                if lines[i].startswith('+') and not lines[i].startswith('+++'):
                    added_lines.append(lines[i][1:])
                elif lines[i].startswith('-') and not lines[i].startswith('---'):
                    removed_lines.append(lines[i][1:])
                elif not lines[i].startswith('\\'):  # Not a "No newline" marker
                    # This is a context line (no prefix or space prefix)
                    context_lines.append(lines[i].lstrip(' '))
                i += 1

            # Split chunk into semantic changes
            if added_lines or removed_lines:
                chunk_changes = detector.split_chunk_into_changes(
                    new_line, added_lines, removed_lines, context_lines
                )
                all_changes.extend(chunk_changes)

            continue

        i += 1

    # Convert to dict format
    return [asdict(change) for change in all_changes]


def main():
    """Main function."""
    diff_path = Path("diff_details.txt")
    output_path = Path("diff_summary.json")

    if not diff_path.exists():
        print("❌ diff_details.txt not found")
        return

    # Find latest snapshot
    snapshot_files = sorted(Path("snapshots").glob("*.html"))
    if not snapshot_files:
        print("❌ No snapshot files found")
        return

    latest_snapshot = snapshot_files[-1]
    print(f"🔍 Parsing diff with advanced semantic detection...")
    print(f"📄 Using snapshot: {latest_snapshot.name}")

    changes = parse_diff_advanced(diff_path, latest_snapshot)

    print(f"\n📊 Found {len(changes)} semantic change(s):\n")

    for i, change in enumerate(changes, 1):
        print(f"{i}. {change['section']} > {change['type']}")
        print(f"   Line: {change['line']}")
        print(f"   Element: {change['html_element']}")
        print(f"   Changes: +{change['additions']} -{change['deletions']}")
        if change.get('anchor'):
            print(f"   Anchor: #{change['anchor']}")
        if change['preview']:
            print(f"   Preview: {change['preview']}")
        print()

    # Generate JSON
    import json
    summary = {
        'total_changes': len(changes),
        'changes': changes
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"✅ Generated advanced summary: {output_path}")


if __name__ == "__main__":
    main()
