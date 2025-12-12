from dataclasses import dataclass
from typing import Callable, Awaitable, Any, Optional
import uuid
import time


@dataclass(order=True)
class Task:
    run_at: float
    task_id: uuid.UUID
    name: str
    func: Callable[..., Awaitable[None]]
    data: Any = None
    recurring_interval_seconds: Optional[float] = None
