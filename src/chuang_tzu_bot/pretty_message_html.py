from datetime import datetime
from typing import Dict, Any, Optional


def health_report(health: Optional[Dict[str, Any]]) -> str:
    """
    Takes the health check dict and returns a beautifully formatted
    HTML string optimized for Telegram.
    """
    if not health:
        return (
            "<b>🚨 Master service is currently unavailable.</b>\n\n"
            "The bot cannot reach the backend server. "
            "Please check if the master service is running."
        )

    status = health.get("status", "unknown").upper()
    message_text = health.get("message", "No message provided")
    timestamp_str = health.get("timestamp", "Unknown time")

    # Parse and format timestamp nicely
    try:
        # Remove microseconds and convert T to space
        clean_ts = timestamp_str.split(".")[0].replace("T", " ")
        # Optional: convert to local time if you want
        last_checked = clean_ts + " UTC"
    except Exception:
        last_checked = timestamp_str

    # Databases
    databases = health.get("databases", {})
    research = databases.get("research", {})
    queue = databases.get("queue", {})

    research_connected = (
        "✅ Connected" if research.get("connected") else "❌ Disconnected"
    )
    research_tables = ", ".join(research.get("tables", [])) or "None listed"

    queue_connected = "✅ Connected" if queue.get("connected") else "❌ Disconnected"
    queue_tables = ", ".join(queue.get("tables", [])) or "None listed"

    # Overall system badge
    if status == "HEALTHY":
        badge = "<code style='background:#d4edda;color:#155724;padding:6px 10px;border-radius:8px;'>All Systems Operational</code>"
    else:
        badge = "<code style='background:#f8d7da;color:#721c24;padding:6px 10px;border-radius:8px;'>Issues Detected</code>"

    html = f"""
<b>🟢 Service Health Report</b>

<i>{message_text}</i>

────────────────────────────
<b>Status:</b> <b>{status}</b>
{badge}
<b>Last checked:</b> <code>{last_checked}</code>
────────────────────────────

<b>📊 Database Status</b>

🔸 <b>Research Database</b>
   • {research_connected}
   • Tables: <code>{research_tables}</code>

🔸 <b>Queue Database</b>
   • {queue_connected}
   • Tables: <code>{queue_tables}</code>

────────────────────────────
<i>All clear — your system is running perfectly! 🚀</i>

Use /health anytime to refresh
    """.strip()

    return html
