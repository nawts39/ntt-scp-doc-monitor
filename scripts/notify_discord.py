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

    # Read diff (first 1000 chars for Discord embed)
    diff_path = Path("diff_details.txt")
    diff_preview = ""
    if diff_path.exists():
        with open(diff_path, 'r', encoding='utf-8') as f:
            diff_content = f.read()
            # Discord embed field limit: 1024 chars
            diff_preview = diff_content[:900]
            if len(diff_content) > 900:
                diff_preview += "\n\n... (差分が長いためGitHubで確認してください)"

    # Create Discord embed
    embed = {
        "title": f"🚨 NTT SCP仕様書が更新されました",
        "description": f"**日付**: {date}\n\n{summary}",
        "color": 15158332,  # Red color
        "fields": [
            {
                "name": "📄 スナップショット",
                "value": f"[GitHub で確認]({repo_url}/blob/main/snapshots/{date}.html)",
                "inline": False
            },
            {
                "name": "📊 Issues",
                "value": f"[詳細を確認]({repo_url}/issues)",
                "inline": False
            }
        ],
        "timestamp": None,
        "footer": {
            "text": "NTT SCP Document Monitor"
        }
    }

    # Add diff preview if available
    if diff_preview:
        embed["fields"].insert(0, {
            "name": "🔍 差分プレビュー",
            "value": f"```diff\n{diff_preview}\n```",
            "inline": False
        })

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
