import os
from dotenv import load_dotenv
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from openai import OpenAI
import asyncio
from typing import List
from pathlib import Path
from chuang_tzu_bot.types import Task
import newspaper_boy

load_dotenv()

newspaper_boy.set_package_root(Path(__file__).parent.parent / "newspaper_boy")

TOKEN = os.getenv("TELEGRAM_API")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ALLOWED_CHAT = int(os.getenv("ALLOWED_CHAT_ID"))
YOUR_TELEGRAM_USER_ID = int(os.getenv("YOUR_TELEGRAM_USER_ID", "0"))
VERBOSE_MODE = False

with open("prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read().strip()

keywords = ["chuangtzu", "@chuangtzubot", "bot"]

HELP_TEXT = """
    Available commands:
    /help - Show this help message
    /change_keywords <comma-separated keywords> - Change the keywords to monitor
        ex: /change_keywords keyword1, keyword2, keyword3
    /change_prompt <new prompt> - Change the system prompt
        ex: /change_prompt You are a helpful assistant.
    /change_news_review_frequencies <hours> - Change the news review frequency (in hours)
        ex: /change_news_review_frequencies 3.5
    /get_todays_msm - Get a summary of today's mainstream media news
"""


llm_client = OpenAI(api_key=OPENAI_API_KEY)
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


# dp.message.filter(F.chat.id.in_(allowed_chat_ids))


QUEUE: List[Task] = []
WAKEUP = asyncio.Event()
