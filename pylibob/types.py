"""OneBot 实现的类型定义。"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Coroutine, Literal, TypedDict

from msgspec import Struct


class BotSelf(TypedDict):
    """机器人自身标识类型 `self`"""

    platform: str
    user_id: str


@dataclass
class Bot:
    """OneBot 机器人。

    `extra` 中定义的字段将与 `platform` 结合成扩展字段。
    """

    platform: str
    user_id: str
    online: bool
    extra: dict[str, Any] | None = None

    def __hash__(self) -> int:
        return hash((self.platform, self.user_id))

    def dict_for_status(self) -> dict[str, Any]:
        """转换为机器人状态字典。

        Returns:
            机器人状态字典
        """
        # sourcery skip: dict-assign-update-to-union
        dic = {
            "self": {
                "platform": self.platform,
                "user_id": self.user_id,
            },
            "online": self.online,
        }
        if self.extra is not None:
            dic.update(
                {f"{self.platform}.{k}": v for k, v in self.extra.items()},
            )
        return dic

    def dict_for_self(self) -> BotSelf:
        """转换为机器人自身标识字典。

        Returns:
            机器人自身标识字典
        """
        return {
            "platform": self.platform,
            "user_id": self.user_id,
        }


class ContentType(str, Enum):
    """消息内容类型。"""

    JSON = "application/json"
    MSGPACK = "application/msgpack"


class ActionResponse(Struct, kw_only=True):
    """动作响应。"""

    status: Literal["ok", "failed"]
    retcode: int
    data: Any = None
    message: str | None = None
    echo: str | None = None


class FailedActionResponse(ActionResponse, kw_only=True):
    """失败的动作响应。"""

    status: Literal["failed"] = "failed"


ActionHandler = Callable[
    ...,
    Coroutine[Any, Any, Any],
]


class Status(TypedDict):
    """OneBot 实现的状态。"""

    good: bool
    bots: list[dict[str, Any]]
