import asyncio
from chuang_tzu_bot import bot, YOUR_TELEGRAM_USER_ID
from chuang_tzu_bot.routes import dp
from chuang_tzu_bot.tasks import send_to_all
from chuang_tzu_bot.worker import worker, schedule_task
from newspaper_boy.io import load_serper_scrape_tasks
import time


async def main():

    tasks = load_serper_scrape_tasks()

    asyncio.create_task(worker())
    task_spacing_seconds = 300
    delay = 10
    for task in tasks:
        schedule_task(
            func=send_to_all,
            delay_seconds=delay,
            data=task,
            recurring_interval_seconds=3500,
            name=f"serper_task_{task.get('search_type','news')}_{task.get('raw_string','')}",
        )
        delay += task_spacing_seconds
    await bot.send_message(YOUR_TELEGRAM_USER_ID, "Bot started!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
