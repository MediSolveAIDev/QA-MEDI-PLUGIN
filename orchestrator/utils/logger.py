"""구조화 로깅."""

import sys
from datetime import datetime


def log(level: str, message: str, extra: dict = None):
    """타임스탬프 + 레벨로 메시지 출력."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = {
        "INFO": "  [INFO]",
        "WARN": "  [WARN]",
        "ERROR": "  [ERROR]",
        "DEBUG": "  [DEBUG]",
    }.get(level, f"  [{level}]")

    line = f"{timestamp} {prefix} {message}"
    if extra:
        extra_str = " ".join(f"{k}={v}" for k, v in extra.items())
        line += f" ({extra_str})"

    print(line, file=sys.stderr if level in ("ERROR", "WARN") else sys.stdout)
