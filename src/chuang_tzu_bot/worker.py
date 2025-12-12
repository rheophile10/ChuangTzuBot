# scheduler.py (or bottom of routes.py)

import asyncio
import heapq
import time
import uuid
from typing import Awaitable, Callable, Any, Optional
from datetime import datetime, timezone
from chuang_tzu_bot import QUEUE, WAKEUP
from chuang_tzu_bot.types import Task


def schedule_task(
    func: Callable[..., Awaitable[None]],
    *,
    delay_seconds: float = 0,
    run_at: Optional[float] = None,
    data: Any = None,
    recurring_interval_seconds: Optional[float] = None,
    name: str = "",
) -> uuid.UUID:
    """Schedule an async function to run at a specific time."""
    if run_at is None:
        run_at = time.time() + delay_seconds

    task_id = uuid.uuid4()

    task = {
        "run_at": run_at,
        "task_id": task_id,
        "name": name or func.__name__,
        "func": func,
        "data": data,
        "recurring_interval_seconds": recurring_interval_seconds,
    }
    task = Task(**task)

    heapq.heappush(QUEUE, task)
    WAKEUP.set()  # wake worker if sleeping
    return task_id


def _reschedule_if_recurring(task: Task):
    """Helper: re-add task if it has recurring_interval_seconds"""
    if task.recurring_interval_seconds is not None:
        schedule_task(
            func=task.func,
            run_at=time.time() + task.recurring_interval_seconds,
            data=task.data,
            recurring_interval_seconds=task.recurring_interval_seconds,
            name=task.name + " (recurring)",
        )


async def _execute_task(task: Task):
    """Separate execution function — clean and testable"""
    try:
        if task.data is None:
            await task.func()
        else:
            await task.func(task.data)
    except Exception as e:
        print(f"[Scheduler] Task '{task.name}' failed: {e}")


async def worker():
    """Single eternal worker — the beating heart"""
    while True:
        if not QUEUE:
            WAKEUP.clear()
            await WAKEUP.wait()
            continue

        now = time.time()
        next_task = QUEUE[0]

        # Sleep until next task (or until new earlier task arrives)
        if next_task.run_at > now:
            WAKEUP.clear()
            try:
                timeout = next_task.run_at - now
                await asyncio.wait_for(WAKEUP.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                pass
            continue

        # Time to run!
        task = heapq.heappop(QUEUE)
        asyncio.create_task(_execute_task(task))  # fire and forget (non-blocking)
        _reschedule_if_recurring(task)


def clear_queue() -> int:
    """Remove all tasks. Returns how many were removed."""
    count = len(QUEUE)
    QUEUE.clear()
    WAKEUP.set()  # wake worker in case it was sleeping
    return count


def format_queue() -> str:
    """Pretty-print current queue"""
    if not QUEUE:
        return "Queue is empty."

    lines = ["<b>Scheduled Tasks:</b>"]
    for i, task in enumerate(sorted(QUEUE, key=lambda t: t.run_at), 1):
        dt = datetime.fromtimestamp(task.run_at, tz=timezone.utc).astimezone()
        when = dt.strftime("%Y-%m-%d %H:%M:%S %Z")
        recur = (
            f" ↻ every {task.recurring_interval_seconds/3600:.1f}h"
            if task.recurring_interval_seconds
            else ""
        )
        lines.append(f"{i}. <code>{when}</code> — {task.name} {recur}\n")
    return "\n".join(lines)
