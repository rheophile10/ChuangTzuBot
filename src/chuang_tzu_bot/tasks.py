import asyncio

from chuang_tzu_bot import bot, ALLOWED_CHAT, VERBOSE_MODE
from chuang_tzu_bot.message import citation_to_telegram_html

from newspaper_boy.serper import (
    _build_query,
    total_serper_search_results,
)
from newspaper_boy.llm import filter_firearms_policy_citations
from newspaper_boy.types import SerperScrapeTask


async def send_to_all(
    serper_task: SerperScrapeTask,
):
    query = _build_query(
        raw_string=serper_task.get("raw_string", ""),
        csv_or_list=serper_task.get("csv_or_list", ""),
    )
    search_header_message = f"🔎 <b>Serper Search:</b> {query}"
    print(search_header_message)
    if VERBOSE_MODE:
        await bot.send_message(
            ALLOWED_CHAT,
            search_header_message,
            parse_mode="HTML",
        )
    citations = total_serper_search_results(**serper_task)
    results_length_message = f"📰 <b>Found {len(citations)} results.</b>"
    print(results_length_message)
    if VERBOSE_MODE:
        await bot.send_message(
            ALLOWED_CHAT,
            results_length_message,
            parse_mode="HTML",
        )
    filtered_citations = filter_firearms_policy_citations(citations)
    filtered_length_message = (
        f"✅ <b>{len(filtered_citations)} articles passed the filter.</b>"
    )
    print(filtered_length_message)
    if VERBOSE_MODE:
        await bot.send_message(
            ALLOWED_CHAT,
            filtered_length_message,
            parse_mode="HTML",
        )
    if len(filtered_citations) == 0:
        return
    for citation in filtered_citations:
        message = citation_to_telegram_html(citation)
        await bot.send_message(
            ALLOWED_CHAT,
            message,
            disable_web_page_preview=False,
            parse_mode="HTML",
        )
        await asyncio.sleep(5)
