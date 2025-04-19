"""元事件。"""
from __future__ import annotations

from typing import Literal

from pylibob.event.base import Event
from pylibob.types import Status


class MetaEvent(
    Event,
    kw_only=True,
):
    """元事件基类。"""

    type: Literal["meta"] = "meta"  # noqa: A003


class MetaConnectEvent(
    MetaEvent,
    kw_only=True,
):
    """`meta.connect` [连接](https://12.onebot.dev/interface/meta/events/#metaconnect)。"""

    detail_type: Literal["connect"] = "connect"
    version: dict[str, str]


class MetaHeartbeatEvent(
    MetaEvent,
    kw_only=True,
):
    """`meta.heartbeat` [心跳](https://12.onebot.dev/interface/meta/events/#metaheartbeat)。"""

    detail_type: Literal["heartbeat"] = "heartbeat"
    interval: int


class MetaStatusUpdateEvent(
    MetaEvent,
    kw_only=True,
):
    """`meta.status_update` [状态更新](https://12.onebot.dev/interface/meta/events/#metastatusupdate)。"""

    detail_type: Literal["status_update"] = "status_update"
    status: Status
