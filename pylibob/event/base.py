"""事件基类模块。"""
from __future__ import annotations

from typing import Any, Literal

from pylibob.types import Bot

import msgspec


class Event(msgspec.Struct, kw_only=True):
    """事件基类。"""

    id: str  # noqa: A003
    time: float
    type: Literal["meta", "message", "notice", "request"]  # noqa: A003
    detail_type: str
    sub_type: str = ""
    self: Bot | None = None
    _extra: dict[str, Any] | None = None
    _platform: str = ""

    def dict(self) -> dict[str, Any]:  # noqa: A003
        """将事件转为字典。

        Returns:
            转换成字典的事件。
        """
        # sourcery skip: dict-assign-update-to-union
        raw = {
            k: v for k, v in msgspec.to_builtins(self).items() if v is not None
        }
        platform = raw.pop('_platform')
        if extra := raw.pop("_extra", None):
            raw.update(
                {f"{platform}.{k}": v for k, v in extra.items()},
            )
        if bot_self := raw.get("self"):
            raw["self"] = {
                "platform": bot_self["platform"],
                "user_id": bot_self["user_id"],
            }
        return raw
