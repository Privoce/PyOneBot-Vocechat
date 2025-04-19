"""通知事件。"""
from __future__ import annotations

from typing import Literal

from pylibob.event.base import Event


class NoticeEvent(Event, kw_only=True):
    """通知事件基类。"""

    type: Literal["notice"] = "notice"  # noqa: A003


class FriendIncreaseEvent(NoticeEvent, kw_only=True):
    """`notice.friend_increase` [好友增加](https://12.onebot.dev/interface/user/notice-events/#noticefriend_increase)"""

    detail_type: Literal["friend_increase"] = "friend_increase"
    user_id: str


class FriendDecreaseEvent(NoticeEvent, kw_only=True):
    """`notice.friend_decrease` [好友减少](https://12.onebot.dev/interface/user/notice-events/#noticefriend_decrease)"""

    detail_type: Literal["friend_decrease"] = "friend_decrease"
    user_id: str


class PrivateMessageDeleteEvent(NoticeEvent, kw_only=True):
    """`notice.private_message_delete` [私聊消息删除](https://12.onebot.dev/interface/user/notice-events/#noticeprivate_message_delete)"""

    detail_type: Literal["private_message_delete"] = "private_message_delete"
    message_id: str
    user_id: str


class GroupMemberIncreaseEvent(NoticeEvent, kw_only=True):
    """`notice.group_member_increase` [群成员增加](https://12.onebot.dev/interface/user/notice-events/#noticegroup_member_increase)"""

    detail_type: Literal["group_member_increase"] = "group_member_increase"
    sub_type: str
    group_id: str
    user_id: str
    operator_id: str


class GroupMemberDecreaseEvent(NoticeEvent, kw_only=True):
    """`notice.group_member_decrease` [群成员减少](https://12.onebot.dev/interface/user/notice-events/#noticegroup_member_decrease)"""

    detail_type: Literal["group_member_decrease"] = "group_member_decrease"
    sub_type: str
    group_id: str
    user_id: str
    operator_id: str


class GroupMessageDeleteEvent(NoticeEvent, kw_only=True):
    """`notice.group_message_delete` [群消息删除](https://12.onebot.dev/interface/user/notice-events/#noticegroup_message_delete)"""

    detail_type: Literal["group_message_delete"] = "group_message_delete"
    sub_type: str
    group_id: str
    message_id: str
    user_id: str
    operator_id: str


class GuildMemberIncreaseEvent(NoticeEvent, kw_only=True):
    """`notice.guild_member_increase` [群组成员增加](https://12.onebot.dev/interface/user/notice-events/#noticeguild_member_increase)"""

    detail_type: Literal["guild_member_increase"] = "guild_member_increase"
    sub_type: str
    guild_id: str
    user_id: str
    operator_id: str


class GuildMemberDecreaseEvent(NoticeEvent, kw_only=True):
    """`notice.guild_member_decrease` [群组成员减少](https://12.onebot.dev/interface/user/notice-events/#noticeguild_member_decrease)"""

    detail_type: Literal["guild_member_decrease"] = "guild_member_decrease"
    sub_type: str
    guild_id: str
    user_id: str
    operator_id: str


class ChannelMemberIncreaseEvent(NoticeEvent, kw_only=True):
    """`notice.channel_member_increase` [频道成员增加](https://12.onebot.dev/interface/user/notice-events/#noticechannel_member_increase)"""

    detail_type: Literal["channel_member_increase"] = "channel_member_increase"
    sub_type: str
    guild_id: str
    channel_id: str
    user_id: str
    operator_id: str


class ChannelMemberDecreaseEvent(NoticeEvent, kw_only=True):
    """`notice.channel_member_decrease` [频道成员减少](https://12.onebot.dev/interface/user/notice-events/#noticechannel_member_decrease)"""

    detail_type: Literal["channel_member_decrease"] = "channel_member_decrease"
    sub_type: str
    guild_id: str
    channel_id: str
    user_id: str
    operator_id: str


class ChannelMessageDeleteEvent(NoticeEvent, kw_only=True):
    """`notice.channel_message_delete` [频道消息删除](https://12.onebot.dev/interface/user/notice-events/#noticechannel_message_delete)"""

    detail_type: Literal["channel_message_delete"] = "channel_message_delete"
    sub_type: str
    guild_id: str
    channel_id: str
    message_id: str
    user_id: str
    operator_id: str


class ChannelCreateEvent(NoticeEvent, kw_only=True):
    """`notice.channel_create` [频道新建](https://12.onebot.dev/interface/user/notice-events/#noticechannel_create)"""

    detail_type: Literal["channel_create"] = "channel_create"
    guild_id: str
    channel_id: str
    operator_id: str


class ChannelDeleteEvent(NoticeEvent, kw_only=True):
    """`notice.channel_delete` [频道删除](https://12.onebot.dev/interface/user/notice-events/#noticechannel_delete)"""

    detail_type: Literal["channel_delete"] = "channel_delete"
    guild_id: str
    channel_id: str
    operator_id: str
