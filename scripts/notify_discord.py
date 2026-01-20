#!/usr/bin/env python3
"""Send notification to Discord webhook."""

import sys
import json
import requests
from pathlib import Path


def send_discord_notification(webhook_url: str, date: str, repo_url: str) -> None:
    """Send change notification to Discord.

    Args:
        webhook_url: Discord webhook URL
        date: Date of the snapshot (YYYYMMDD)
        repo_url: GitHub repository URL
    """
    # Read summary
    summary_path = Path("diff_summary.txt")
    if not summary_path.exists():
        print("❌ diff_summary.txt not found", file=sys.stderr)
        sys.exit(1)

    with open(summary_path, 'r', encoding='utf-8') as f:
        summary = f.read()

    # Read diff and split into chunks for Discord embed
    diff_path = Path("diff_details.txt")
    diff_chunks = []
    if diff_path.exists():
        with open(diff_path, 'r', encoding='utf-8') as f:
            diff_content = f.read()

            # Discord embed field limit: 1024 chars
            # Split into multiple fields if needed (max 3 chunks)
            chunk_size = 950  # Leave room for code block markers
            for i in range(0, min(len(diff_content), chunk_size * 3), chunk_size):
                chunk = diff_content[i:i + chunk_size]
                diff_chunks.append(chunk)

            # Add truncation notice if content is very long
            if len(diff_content) > chunk_size * 3:
                diff_chunks.append(f"\n... (残り {len(diff_content) - chunk_size * 3} 文字)")

    # Create Discord embed
    embed = {
        "title": f"🚨 NTT SCP仕様書が更新されました",
        "description": f"**日付**: {date}\n\n{summary}",
        "color": 15158332,  # Red color
        "fields": [],
        "timestamp": None,
        "footer": {
            "text": "NTT SCP Document Monitor"
        }
    }

    # Add diff chunks as separate fields
    if diff_chunks:
        for idx, chunk in enumerate(diff_chunks[:3]):  # Max 3 chunks
            field_name = f"🔍 差分プレビュー" if idx == 0 else f"🔍 差分プレビュー (続き {idx + 1})"
            embed["fields"].append({
                "name": field_name,
                "value": f"```diff\n{chunk}\n```",
                "inline": False
            })

    # Add links
    embed["fields"].extend([
        {
            "name": "📄 完全な差分",
            "value": f"[GitHub で確認]({repo_url}/blob/main/snapshots/{date}.html)",
            "inline": False
        },
        {
            "name": "📊 Issues",
            "value": f"[詳細を確認]({repo_url}/issues)",
            "inline": False
        }
    ])

    payload = {
        "username": "Document Monitor",
        "avatar_url": "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png",
        "embeds": [embed]
    }

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        print("✅ Discord notification sent successfully")
    except requests.RequestException as e:
        print(f"❌ Failed to send Discord notification: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: notify_discord.py <webhook_url> <date> <repo_url>")
        sys.exit(1)

    send_discord_notification(sys.argv[1], sys.argv[2], sys.argv[3])
