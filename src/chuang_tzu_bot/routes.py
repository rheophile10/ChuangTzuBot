from aiogram import Router, F
from aiogram.types import Message
import json
from web_resources.worker_helper_funcs import check_master_health
from web_resources.worker_helper_funcs.queue import (
    enqueue_task,
    get_task_by_id,
    get_pending_tasks,
    get_running_tasks,
    get_failed_tasks,
    get_tasks_by_worker,
)
from chuang_tzu_bot.pretty_message_html import health_report
from chuang_tzu_bot.parse_user_args import ArgParseError, parse_telegram_flags


router = Router()


@router.message(F.text, F.text.startswith(("/help", "/start")))
async def cmd_help_or_start(message: Message):
    help_text = """
🛰️💥🔫<b>Command Center</b>🛰️💥🔫

🔥🤖💣🤖🔥💣🤖🔥

<b>🎯Available COMMANDS:🎯</b>

<b>🌐 System & Monitoring</b> 🔭
📊 /health     → Full battlefield health scan

<b>QUEUE STATUS</b>📋
📈 /queue      → Mission queue status
⏳ /pending    → Targets awaiting strike
🏃 /running    → Active fire missions
❌ /failed     → Failed ops (BOOM!)
🔍 /task --id 123 → Intel extraction on target ID

<b>🚀 Task Deployment</b> 💥
/enq &lt;name&gt; --data {...} → Enqueue a new task
    💣Examples:
    • /enq scrape --data {"url": "https://news.com"} --device gpu
    • /enq notify --data {"user_id": 123} --at 2025-12-25T09:00:00

<b>🛠️ Agent Interrogation</b> 🔫
👷 /wts --worker &lt;id&gt; → Extract status from field agent
    📌 Example: /wts --worker agent_47

<b>ℹ️ Control Panel</b> 🧨
🎛️ /start /help → Reload tactical HUD
    """.strip()

    await message.answer(help_text, parse_mode="HTML", disable_web_page_preview=True)


@router.message(F.text, F.text.startswith("/health"))
async def cmd_health(message: Message):
    health = await check_master_health(timeout=5.0)

    pretty_html = health_report(health)

    await message.answer(pretty_html, parse_mode="HTML")


@router.message(F.text, F.text.startswith("/enq"))
async def cmd_enq(message: Message):
    try:
        task_name, params = parse_telegram_flags(
            text=message.text,
            required_flags=["data"],
            optional_flags=["device", "at"],
            allow_positional=True,
        )

        if not task_name:
            raise ArgParseError("Missing task name")

        # Apply defaults
        device = params.get("device", "cpu")
        run_at = params.get("at")
        data = params["data"]

        task_id = await enqueue_task(
            func_name=task_name,
            data=data,
            device=device,
            run_at=run_at,
        )

        lines = [
            "<b>✅ Task Enqueued!</b>",
            f"<b>ID:</b> <code>{task_id}</code>",
            f"<b>Name:</b> <code>{task_name}</code>",
            f"<b>Device:</b> <code>{device.upper()}</code>",
        ]
        if run_at:
            lines.append(
                f"<b>Scheduled:</b> <code>{run_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</code>"
            )
        lines.append(
            f"<b>Data:</b> <code>{json.dumps(data, ensure_ascii=False)}</code>"
        )

        await message.answer("\n".join(lines), parse_mode="HTML")

    except ArgParseError as e:
        await message.answer(
            f"<b>❌ Invalid usage</b>\n\n"
            f"<code>{str(e)}</code>\n\n"
            "<b>Usage:</b>\n"
            "<code>/enq &lt;task_name&gt; --data {&quot;json&quot;} [--device cpu|gpu] [--at YYYY-MM-DDTHH:MM:SS]</code>\n\n"
            "<b>Examples:</b>\n"
            "/enq scrape --data {&quot;url&quot;: &quot;https://site.com&quot;} --device gpu\n"
            "/enq notify --data {&quot;user_id&quot;: 123} --at 2025-12-25T09:00:00",
            parse_mode="HTML",
        )
    except Exception as e:
        await message.answer(
            f"❌ Enqueue failed: <code>{str(e)}</code>", parse_mode="HTML"
        )


@router.message(F.text, F.text.startswith("/task"))
async def cmd_task(message: Message):
    try:
        _, params = parse_telegram_flags(
            message.text, required_flags=["id"], allow_positional=False
        )
        task_id = int(params["id"])
    except ArgParseError:
        await message.answer(
            "<b>/task — View task by ID</b>\n\n"
            "<b>Usage:</b>\n"
            "<code>/task --id 12345</code>",
            parse_mode="HTML",
        )
        return
    except ValueError:
        await message.answer("❌ Invalid task ID (must be a number)")
        return

    task = await get_task_by_id(task_id)
    if not task:
        await message.answer(
            f"❌ Task <code>{task_id}</code> not found or inaccessible."
        )
        return

    data_str = json.dumps(task.get("data", {}), ensure_ascii=False, indent=2)
    if len(data_str) > 800:
        data_str = data_str[:800] + "..."

    status_emoji = {
        "pending": "⏳",
        "running": "🏃",
        "completed": "✅",
        "failed": "❌",
    }.get(task["status"], "❓")

    await message.answer(
        f"<b>{status_emoji} Task {task['id']}</b>\n\n"
        f"<b>Name:</b> <code>{task['name']}</code>\n"
        f"<b>Status:</b> <code>{task['status'].upper()}</code>\n"
        f"<b>Device:</b> <code>{task.get('device', 'cpu').upper()}</code>\n"
        f"<b>Created:</b> <code>{task['created_at'][:19].replace('T', ' ')}</code>\n"
        + (
            f"<b>Assigned to:</b> <code>{task.get('assigned_to', 'none')}</code>\n"
            if task.get("assigned_to")
            else ""
        )
        + (
            f"<b>Error:</b> <code>{task.get('error_message', 'none')}</code>\n"
            if task.get("error_message")
            else ""
        )
        + f"\n<b>Data:</b>\n<pre>{data_str}</pre>",
        parse_mode="HTML",
    )


@router.message(F.text == "/pending")
async def cmd_pending(message: Message):
    tasks = await get_pending_tasks()
    if not tasks:
        await message.answer("✅ <b>No pending tasks</b> — queue is clear!")
        return

    lines = [f"<b>⏳ Pending Tasks ({len(tasks)})</b>\n"]
    for t in tasks[:20]:  # Limit to avoid spam
        lines.append(
            f"• <code>{t['id']}</code> | <code>{t['name']}</code> | "
            f"{t['created_at'][11:19]} | {t.get('device', 'cpu').upper()}"
        )
    if len(tasks) > 20:
        lines.append(f"\n... and {len(tasks)-20} more")

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(F.text == "/running")
async def cmd_running(message: Message):
    tasks = await get_running_tasks()
    if not tasks:
        await message.answer("🏃 <b>No tasks currently running</b>")
        return

    lines = [f"<b>🏃 Running Tasks ({len(tasks)})</b>\n"]
    for t in tasks:
        worker = t.get("assigned_to", "unknown")
        lines.append(
            f"• <code>{t['id']}</code> | <code>{t['name']}</code> | "
            f"Worker: <code>{worker}</code> | {t.get('device', 'cpu').upper()}"
        )

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(F.text == "/failed")
async def cmd_failed(message: Message):
    tasks = await get_failed_tasks()
    if not tasks:
        await message.answer("✅ <b>No failed tasks recently</b> — all good!")
        return

    lines = [f"<b>❌ Recent Failed Tasks ({len(tasks)})</b>\n"]
    for t in tasks[:15]:
        error = (t.get("error_message") or "Unknown error")[:60]
        lines.append(
            f"• <code>{t['id']}</code> | <code>{t['name']}</code>\n"
            f"  ↳ <code>{error}</code>"
        )

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(F.text, F.text.startswith("/wts"))
async def cmd_mytasks(message: Message):
    try:
        _, params = parse_telegram_flags(
            message.text, required_flags=["worker"], allow_positional=False
        )
        worker_id = params["worker"]
    except ArgParseError:
        await message.answer(
            "<b>/mytasks — Tasks for a worker</b>\n\n"
            "<code>/mytasks --worker test_worker_abc123</code>",
            parse_mode="HTML",
        )
        return

    tasks = await get_tasks_by_worker(worker_id)
    if not tasks:
        await message.answer(f"ℹ️ No tasks found for worker <code>{worker_id}</code>")
        return

    lines = [f"<b>📋 Tasks for {worker_id} ({len(tasks)})</b>\n"]
    for t in tasks[:20]:
        lines.append(
            f"• <code>{t['id']}</code> | <code>{t['status']}</code> | "
            f"<code>{t['name']}</code>"
        )

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(F.text == "/queue")
async def cmd_queue(message: Message):
    pending = len(await get_pending_tasks())
    running = len(await get_running_tasks())
    failed = len(await get_failed_tasks())

    await message.answer(
        f"<b>📊 Queue Overview</b>\n\n"
        f"⏳ Pending: <b>{pending}</b>\n"
        f"🏃 Running: <b>{running}</b>\n"
        f"❌ Failed: <b>{failed}</b>\n\n"
        f"Use /pending /running /failed for details",
        parse_mode="HTML",
    )
