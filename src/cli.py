"""윈도우 콘솔이 한글을 안 깨뜨리게."""

from __future__ import annotations

import sys


def utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
