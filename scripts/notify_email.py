#!/usr/bin/env python3
"""Send notification via email using Gmail SMTP."""

import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path


def send_email_notification(
    gmail_address: str,
    gmail_app_password: str,
    to_addresses: str,
    date: str,
    repo_url: str
) -> None:
    """Send change notification via email.

    Args:
        gmail_address: Gmail address for sending
        gmail_app_password: Gmail app password
        to_addresses: Comma-separated recipient email addresses
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

    # Read diff details
    diff_path = Path("diff_details.txt")
    diff_content = ""
    if diff_path.exists():
        with open(diff_path, 'r', encoding='utf-8') as f:
            diff_content = f.read()
            # Limit to 5000 characters for email
            if len(diff_content) > 5000:
                diff_content = diff_content[:5000] + f"\n\n... (残り {len(diff_content) - 5000} 文字)"

    # Extract username from repo_url
    username = repo_url.split('/')[-2] if '/' in repo_url else 'unknown'
    repo_name = repo_url.split('/')[-1] if '/' in repo_url else 'unknown'
    viewer_url = f"https://{username}.github.io/{repo_name}/diffs/{date}.html"

    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🚨 NTT SCP仕様書が更新されました ({date})"
    msg['From'] = gmail_address
    msg['To'] = to_addresses

    # Plain text version
    text_body = f"""
NTT SCP仕様書が更新されました

日付: {date}

{summary}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

差分詳細:

{diff_content}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

リンク:
- ビジュアル差分ビューア: {viewer_url}
- スナップショット: {repo_url}/blob/main/snapshots/{date}.html
- Issues: {repo_url}/issues

---
NTT SCP Document Monitor
    """.strip()

    # HTML version
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .date {{
            opacity: 0.9;
            margin-top: 8px;
        }}
        .summary {{
            background: #f8f9fa;
            padding: 15px;
            border-left: 4px solid #667eea;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .diff {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            margin: 20px 0;
        }}
        .diff pre {{
            margin: 0;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        }}
        .links {{
            background: white;
            padding: 15px;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            margin: 20px 0;
        }}
        .links a {{
            display: inline-block;
            margin: 5px 10px 5px 0;
            padding: 8px 16px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 4px;
        }}
        .links a:hover {{
            background: #5568d3;
        }}
        .footer {{
            text-align: center;
            color: #999;
            font-size: 12px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚨 NTT SCP仕様書が更新されました</h1>
        <div class="date">日付: {date}</div>
    </div>

    <div class="summary">
        <strong>変更サマリー</strong><br>
        <pre style="white-space: pre-wrap; font-family: inherit;">{summary}</pre>
    </div>

    <div class="diff">
        <strong>📝 差分詳細</strong>
        <pre>{diff_content}</pre>
    </div>

    <div class="links">
        <strong>🔗 リンク</strong><br><br>
        <a href="{viewer_url}">👁️ ビジュアル差分ビューア</a>
        <a href="{repo_url}/blob/main/snapshots/{date}.html">📄 スナップショット</a>
        <a href="{repo_url}/issues">📊 Issues</a>
    </div>

    <div class="footer">
        NTT SCP Document Monitor
    </div>
</body>
</html>
    """.strip()

    # Attach parts
    part1 = MIMEText(text_body, 'plain', 'utf-8')
    part2 = MIMEText(html_body, 'html', 'utf-8')
    msg.attach(part1)
    msg.attach(part2)

    # Send email
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(gmail_address, gmail_app_password)
            server.sendmail(gmail_address, to_addresses.split(','), msg.as_string())

        print(f"✅ Email notification sent successfully to {to_addresses}")
    except smtplib.SMTPException as e:
        print(f"❌ Failed to send email notification: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: notify_email.py <gmail_address> <gmail_app_password> <to_addresses> <date> <repo_url>")
        sys.exit(1)

    send_email_notification(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
