import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple


class ArgParseError(Exception):
    """Custom exception for clean error messages"""

    pass


def parse_telegram_flags(
    text: str,
    required_flags: Optional[list[str]] = None,
    optional_flags: Optional[list[str]] = None,
    allow_positional: bool = True,
) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Parse Telegram message text with keyword flags like --key value

    Returns:
        (positional_value, kwargs_dict)

    Example:
        "/cmd mytask --device gpu --dry_run --count 5"
        → ("mytask", {"device": "gpu", "dry_run": True, "count": 5})
    """
    if required_flags is None:
        required_flags = []
    if optional_flags is None:
        optional_flags = []

    all_flags = set(required_flags + optional_flags)
    bool_flags = {
        f for f in all_flags if f.endswith("_run") or f in {"dry_run", "force", "debug"}
    }  # common bools

    args = text.strip().split()[1:]  # Skip the command itself
    positional = None
    kwargs: Dict[str, Any] = {}
    i = 0

    while i < len(args):
        arg = args[i]

        if arg.startswith("--"):
            flag = arg[2:]  # Remove --
            if flag not in all_flags:
                raise ArgParseError(f"Unknown flag: --{flag}")

            if i + 1 >= len(args):
                # Boolean flag at end
                if flag in bool_flags:
                    kwargs[flag] = True
                else:
                    raise ArgParseError(f"Missing value for --{flag}")
            else:
                value = args[i + 1]
                # Auto-detect types
                if value.lower() in ("true", "false"):
                    kwargs[flag] = value.lower() == "true"
                elif value.isdigit():
                    kwargs[flag] = int(value)
                elif flag in {"device"} and value.lower() in ("cpu", "gpu"):
                    kwargs[flag] = value.lower()
                elif flag == "data":
                    try:
                        kwargs[flag] = json.loads(value)
                    except json.JSONDecodeError as e:
                        raise ArgParseError(f"Invalid JSON in --data: {e}")
                elif flag == "at":
                    try:
                        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                        kwargs[flag] = (
                            dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
                        )
                    except ValueError:
                        raise ArgParseError(
                            f"Invalid datetime: {value}. Use YYYY-MM-DDTHH:MM:SS"
                        )
                else:
                    # String fallback
                    kwargs[flag] = value

                i += 1  # Skip the value

        elif allow_positional and positional is None:
            positional = arg
        else:
            raise ArgParseError("Extra positional argument (only one allowed)")

        i += 1

    # Validate required
    missing = [f for f in required_flags if f not in kwargs]
    if missing:
        raise ArgParseError(
            f"Missing required flags: {', '.join('--' + m for m in missing)}"
        )

    return positional, kwargs
