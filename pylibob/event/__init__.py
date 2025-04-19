"""[事件（Event）](https://12.onebot.dev/glossary/#event)。"""
from __future__ import annotations

from .base import Event as Event
from .message import (
    ChannelMessageEvent as ChannelMessageEvent,
    GroupMessageEvent as GroupMessageEvent,
    MessageEvent as MessageEvent,
    PrivateMessageEvent as PrivateMessageEvent,
)
from .meta import (
    MetaConnectEvent as MetaConnectEvent,
    MetaEvent as MetaEvent,
    MetaHeartbeatEvent as MetaHeartbeatEvent,
    MetaStatusUpdateEvent as MetaStatusUpdateEvent,
)
from .notice import (
    ChannelCreateEvent as ChannelCreateEvent,
    ChannelDeleteEvent as ChannelDeleteEvent,
    ChannelMemberDecreaseEvent as ChannelMemberDecreaseEvent,
    ChannelMemberIncreaseEvent as ChannelMemberIncreaseEvent,
    ChannelMessageDeleteEvent as ChannelMessageDeleteEvent,
    FriendDecreaseEvent as FriendDecreaseEvent,
    FriendIncreaseEvent as FriendIncreaseEvent,
    GroupMemberDecreaseEvent as GroupMemberDecreaseEvent,
    GroupMemberIncreaseEvent as GroupMemberIncreaseEvent,
    GroupMessageDeleteEvent as GroupMessageDeleteEvent,
    GuildMemberDecreaseEvent as GuildMemberDecreaseEvent,
    GuildMemberIncreaseEvent as GuildMemberIncreaseEvent,
    NoticeEvent as NoticeEvent,
)
from .request import RequestEvent as RequestEvent
