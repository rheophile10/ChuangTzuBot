from datetime import datetime
from newspaper_boy.types import Citation


SPICINESS_EMOJI_MAP = {
    1: "🔥",  # mild
    2: "🔥🔥",  # warm
    3: "🔥🔥🔥",  # hot
    4: "🔥🔥🔥🔥",  # very hot
    5: "🔥🔥🔥🔥🔥",  # nuclear
}


def citation_to_telegram_html(citation: Citation) -> str:
    title = citation.get("title") or "No title"
    url = citation["url"]
    publisher = citation.get("publisher") or "Unknown source"

    # Format date
    date_obj = citation.get("date")
    if isinstance(date_obj, datetime):
        published = date_obj.strftime("%B %d, %Y at %I:%M %p")
    elif date_obj:
        try:
            published = datetime.fromisoformat(
                str(date_obj).replace("Z", "+00:00")
            ).strftime("%B %d, %Y at %I:%M %p")
        except Exception:
            published = str(date_obj)
    else:
        published = "Date unknown"

    snippet = citation.get("metadata", {}).get("snippet")
    snippet_line = f"{snippet[:200]}...\n" if snippet else ""

    bot_comment = citation.get("reason_for_ccfr")
    bot_comment_line = (
        f"💬 <b>Why this matters:</b> {bot_comment}\n" if bot_comment else ""
    )

    spiciness = citation.get("spiciness")
    if isinstance(spiciness, int) and 1 <= spiciness <= 5:
        spice_emoji = SPICINESS_EMOJI_MAP.get(spiciness, "🔥")
        spiciness_line = f"🌶 <b>Spiciness:</b> {spice_emoji} ({spiciness}/5)\n"
    else:
        spiciness_line = ""

    html = f"""
<b>{title}</b>

{snippet_line}{bot_comment_line}{spiciness_line}<b>Source:</b> {publisher.upper()}
⏱ {published}

👉 <a href="{url}">link</a>
——————————————————
    """.strip()

    return html
