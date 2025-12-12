from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram import Dispatcher, F
from chuang_tzu_bot import (
    HELP_TEXT,
    VERBOSE_MODE,
)
from chuang_tzu_bot.worker import schedule_task, clear_queue, format_queue
from chuang_tzu_bot.tasks import send_to_all


dp = Dispatcher()
# dp.message.filter(F.chat.id.in_(allowed_chat_ids))


@dp.message(CommandStart())
async def start(message: Message):
    # await message.answer(HELP_TEXT)
    chat_id = message.chat.id
    welcome = f"""Hello, <b>{chat_id}</b>! 👋"""

    await message.answer(welcome, parse_mode="HTML")


@dp.message(Command("verbose"))
async def verbose(message: Message):
    global VERBOSE_MODE
    VERBOSE_MODE = not VERBOSE_MODE
    text = "Verbose mode is now " + ("ON" if VERBOSE_MODE else "OFF")
    await message.answer(
        text,
    )


@dp.message(Command("queue"))
async def cmd_queue(message: Message):
    text = format_queue()
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)


@dp.message(Command("clear_queue"))
async def cmd_clear_queue(message: Message):
    count = clear_queue()
    await message.answer(f"Cleared {count} task(s). Queue is now empty.")


@dp.message(Command("schedule"))
async def cmd_schedule(message: Message):
    try:
        parts = message.text.split(maxsplit=2)
        delay = float(parts[1])
        text = parts[2] if len(parts) > 2 else "Scheduled message"

        schedule_task(
            func=send_to_all,
            delay_seconds=delay,
            data=text,
            name=f"one-shot ({delay}s)",
        )
        await message.answer(f"Scheduled in {delay} seconds: {text}")
    except:
        await message.answer("Usage: /schedule 30 Hello after half minute")


@dp.message(Command("repeat"))
async def cmd_repeat(message: Message):
    try:
        parts = message.text.split(maxsplit=2)
        hours = float(parts[1])
        text = parts[2] if len(parts) > 2 else "Recurring message"

        interval = hours * 3600
        schedule_task(
            func=send_to_all,
            delay_seconds=5,  # first run soon
            data=text,
            recurring_interval_seconds=interval,
            name=f"repeat every {hours}h",
        )
        await message.answer(f"Recurring message set: every {hours} hours")
    except:
        await message.answer("Usage: /repeat 4.5 Be excellent to each other")


@dp.message(Command("hello_now"))
async def cmd_hello_now(message: Message):
    schedule_task(send_to_all, delay_seconds=3, data="hello world from command")
    await message.answer("hello sent in 3s")


# @dp.message()
# async def chat_handler(message: Message):
#     user_text = (message.text or message.caption or "").strip()
#     if not user_text:
#         return  # ignore stickers, photos without caption, etc.

#     try:

#         response = await asyncio.to_thread(
#             llm_client.chat.completions.create,
#             model="gpt-3.5-turbo",
#             temperature=0.7,
#             max_tokens=1200,
#             messages=[
#                 {"role": "system", "content": SYSTEM_PROMPT},
#                 {"role": "user", "content": user_text},
#             ],
#         )
#         reply = response.choices[0].message.content
#         if reply is None:
#             reply = "I have nothing to say at this moment."
#         else:
#             reply = reply.strip()

#         if len(reply) > 4000:
#             parts = [reply[i : i + 4000] for i in range(0, len(reply), 4000)]
#             for i, part in enumerate(parts):
#                 if i == 0:
#                     await message.reply(part, disable_web_page_preview=True)
#                 else:
#                     await asyncio.sleep(1)
#                     await message.reply(part, disable_web_page_preview=True)
#         else:
#             await message.reply(reply, disable_web_page_preview=True)

#     except Exception as e:
#         await message.reply(
#             "I encountered an error while thinking. Please try again in a moment."
#         )
