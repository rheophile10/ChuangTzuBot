import asyncio
from chuang_tzu_bot import (
    send_html_message,
    start_polling,
    _get_allowed_chat_ids,
)
import time


async def demo_sending():
    """Demonstrate various ways to send HTML messages."""
    print("\n=== Sending Messages Demo ===\n")

    # 1. Default: send to primary "user" chat
    await send_html_message(
        text="<b>Hello!</b> This is a <i>bold and italic</i> test message from example.py",
        bot_enviro="TEST",
    )

    # 2. Send to group
    await send_html_message(
        text="📢 <u>Announcement</u> going to the group chat!",
        user_or_group="group",
        disable_web_page_preview=False,
        bot_enviro="TEST",
    )

    # 3. Send to specific chat_id (override)
    allowed = _get_allowed_chat_ids()
    user_id = next((cid for cid in allowed if cid > 0), None)
    if user_id:
        await send_html_message(
            text=f"👋 Direct message to chat ID: <code>{user_id}</code>",
            chat_id=user_id,
            disable_notification=True,
            bot_enviro="TEST",
        )

    # 4. Use PROD bot (if configured)
    # await send_html_message("This goes via PROD bot", bot_enviro="PROD")


async def demo_polling():
    """Start the bot in polling mode (blocks until Ctrl+C)."""
    print("\n=== Starting Polling ===\n")
    print("The bot is now listening for messages from allowed chats.")
    print("Send a message to one of your allowed chats to see handlers in action.")
    print("Press Ctrl+C to stop.\n")

    try:
        await start_polling(
            bot_enviro="TEST",  # Change to "PROD" if needed
            polling_timeout=3000,
            # allowed_chat_ids=...  # Optional: override env list
        )
    except KeyboardInterrupt:
        print("\nPolling stopped by user.")


async def main():
    print("Chuang Tzu Bot – Function Demo")
    print(f"Allowed chat IDs from env: {_get_allowed_chat_ids()}")

    # Run sending demo
    await demo_sending()
    time.sleep(2)
    # Uncomment the line below to also start interactive polling
    await demo_polling()

    print("\nDemo complete!")


if __name__ == "__main__":
    asyncio.run(main())
