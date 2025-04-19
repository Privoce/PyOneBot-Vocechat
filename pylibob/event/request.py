"""请求事件。"""
from __future__ import annotations

from typing import Literal

from pylibob.event.base import Event


class RequestEvent(Event, kw_only=True):
    """请求事件基类。"""

    type: Literal["request"] = "request"  # noqa: A003
