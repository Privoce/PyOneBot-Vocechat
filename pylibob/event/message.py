"""消息事件。"""
from __future__ import annotations

from typing import Literal

from pylibob.event.base import Event
from pylibob.segment import Segment


class MessageEvent(Event, kw_only=True):
    """消息事件基类。"""

    type: Literal["message"] = "message"  # noqa: A003
    


class PrivateMessageEvent(MessageEvent, kw_only=True):
    """`message.private` [私聊消息](https://12.onebot.dev/interface/user/message-events/#messageprivate)。"""

    detail_type: Literal["private"] = "private"
    message_id: str
    message: list[Segment]
    alt_message: str = ""
    user_id: str


class GroupMessageEvent(MessageEvent, kw_only=True):
    """`message.group` [群消息](https://12.onebot.dev/interface/user/message-events/#messagegroup)。"""

    detail_type: Literal["group"] = "group"
    message_id: str
    message: list[Segment]
    alt_message: str = ""
    group_id: str
    user_id: str


class ChannelMessageEvent(MessageEvent, kw_only=True):
    """`message.channel` [频道消息](https://12.onebot.dev/interface/user/message-events/#messagechannel)。"""

    detail_type: Literal["channel"] = "channel"
    message_id: str
    message: list[Segment]
    alt_message: str = ""
    guild_id: str
    user_id: str
    channel_id: str
