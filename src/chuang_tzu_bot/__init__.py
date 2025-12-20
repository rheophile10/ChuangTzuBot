import os
from typing import Iterable, Literal
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from chuang_tzu_bot.routes import router

load_dotenv()

BotEnviro = Literal["TEST", "PROD"]


def _get_token(bot_enviro: BotEnviro = "TEST") -> str:
    if bot_enviro == "TEST":
        token = os.getenv("TEST_FRANK_TELEGRAM_API")
    elif bot_enviro == "PROD":
        token = os.getenv("PROD_FRANK_TELEGRAM_API")
    else:
        raise ValueError("bot_enviro must be 'TEST' or 'PROD'")

    if not token:
        raise ValueError(f"No token found for {bot_enviro} environment")
    return token


def _get_allowed_chat_ids(bot_enviro: BotEnviro = "TEST") -> Iterable[int | str]:
    allowed_ids = []

    user_chat_id = os.getenv("YOUR_TELEGRAM_USER_ID", "")
    if user_chat_id.isdigit():
        allowed_ids.append(int(user_chat_id))

    if bot_enviro == "TEST":
        allowed_chats_str = os.getenv("TEST_ALLOWED_CHAT_ID", "")
    elif bot_enviro == "PROD":
        allowed_chats_str = os.getenv("PROD_ALLOWED_CHAT_ID", "")
    else:
        raise ValueError("bot_enviro must be 'TEST' or 'PROD'")

    allowed_chats = [
        int(cid.strip()) for cid in allowed_chats_str.split(",") if cid.strip()
    ]
    allowed_ids.extend(allowed_chats)

    return allowed_ids


def create_bot_client(bot_enviro: BotEnviro = "TEST") -> Bot:
    token = _get_token(bot_enviro)
    return Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


@asynccontextmanager
async def get_temp_bot(bot_enviro: BotEnviro = "TEST") -> Bot:
    token = _get_token(bot_enviro)

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    try:
        yield bot
    finally:
        await bot.session.close()


async def send_html_message(
    text: str,
    user_or_group: str = "user",
    chat_id: int | None = None,
    disable_web_page_preview: bool = True,
    disable_notification: bool = False,
    bot_enviro: BotEnviro = "TEST",
) -> bool:
    allowed_chat_ids = _get_allowed_chat_ids()

    if not allowed_chat_ids:
        raise ValueError("No allowed chat IDs configured")

    if chat_id is None:
        sorted_ids = sorted(allowed_chat_ids)
        if user_or_group == "user":
            chat_id = next((cid for cid in sorted_ids if cid > 0), sorted_ids[0])
        elif user_or_group == "group":
            chat_id = next((cid for cid in sorted_ids if cid < 0), sorted_ids[0])
        else:
            raise ValueError("user_or_group must be 'user' or 'group'")

    if chat_id not in allowed_chat_ids:
        raise ValueError(f"Chat ID {chat_id} not allowed")

    async with get_temp_bot(bot_enviro) as bot:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=disable_web_page_preview,
            disable_notification=disable_notification,
        )
    return True


async def start_polling(
    bot_enviro: BotEnviro = "TEST",
    polling_timeout: int = 30,
) -> None:
    bot = create_bot_client(bot_enviro)
    allowed_chat_ids = _get_allowed_chat_ids()
    allowed_set = set(allowed_chat_ids)

    dp = Dispatcher()

    router.message.filter(F.chat.id.in_(allowed_set))

    dp.include_router(router)

    print(f"Bot starting polling (env: {bot_enviro})")
    print(f"Allowed chats: {allowed_set}")
    print(f"Polling timeout: {polling_timeout}s")

    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(
            bot,
            polling_timeout=polling_timeout,
            allowed_updates=["message"],
        )
    finally:
        await dp.stop_polling()
        await asyncio.sleep(1)
        await bot.session.close()


__all__ = [
    "send_html_message",
    "start_polling",
]
