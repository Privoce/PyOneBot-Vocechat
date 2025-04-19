"""pylibob 异常类，用于返回特定 `failed` 状态的响应。"""
from __future__ import annotations

from typing import Any

from pylibob.status import (
    BAD_HANDLER,
    BAD_PARAM,
    BAD_REQUEST,
    BAD_SEGMENT_DATA,
    INTERNAL_HANDLER_ERROR,
    UNKNOWN_SELF,
    UNSUPPORTED_ACTION,
    UNSUPPORTED_PARAM,
    UNSUPPORTED_SEGMENT,
    UNSUPPORTED_SEGMENT_DATA,
    WHO_AM_I,
)


class OneBotImplError(Exception):
    """OneBot 实现引发的错误。

    在响应器函数中引发此错误会由 pylibob 截获
    并转为 `failed` 的响应。
    """

    def __init__(
        self,
        retcode: int,
        data: Any = None,
        message: str = "",
    ) -> None:
        self.retcode = retcode
        self.data = data
        self.message = message


class BadRequest(OneBotImplError):
    """`10001` 无效的动作请求。

    格式错误（包括实现不支持 MessagePack 的情况）、
    必要字段缺失或字段类型错误。"""

    def __init__(self, data: Any = None, message: str = "") -> None:
        super().__init__(BAD_REQUEST, data, message)


class UnsupportedAction(OneBotImplError):
    """`10002` 不支持的动作请求。

    OneBot 实现没有实现该动作。"""

    def __init__(self, data: Any = None, message: str = "") -> None:
        super().__init__(UNSUPPORTED_ACTION, data, message)


class BadParam(OneBotImplError):
    """`10003` 无效的动作请求参数。

    参数缺失或参数类型错误。"""

    def __init__(self, data: Any = None, message: str = "") -> None:
        super().__init__(BAD_PARAM, data, message)


class UnsupportedParam(OneBotImplError):
    """`10004` 不支持的动作请求参数。

    OneBot 实现没有实现该参数的语义。"""

    def __init__(self, data: Any = None, message: str = "") -> None:
        super().__init__(UNSUPPORTED_PARAM, data, message)


class UnsupportedSegment(OneBotImplError):
    """`10005` 不支持的消息段类型。

    OneBot 实现没有实现该消息段类型。
    """

    def __init__(self, data: Any = None, message: str = "") -> None:
        super().__init__(UNSUPPORTED_SEGMENT, data, message)


class BadSegmentData(OneBotImplError):
    """`10006` 无效的消息段参数。

    参数缺失或参数类型错误。
    """

    def __init__(self, data: Any = None, message: str = "") -> None:
        super().__init__(BAD_SEGMENT_DATA, data, message)


class UnsupportedSegmentData(OneBotImplError):
    """`10007` 不支持的消息段参数。

    OneBot 实现没有实现该参数的语义。
    """

    def __init__(self, data: Any = None, message: str = "") -> None:
        super().__init__(UNSUPPORTED_SEGMENT_DATA, data, message)


class WhoAmI(OneBotImplError):
    """`10101` 未指定机器人账号。

    OneBot 实现在单个 OneBot Connect 连接上支持多个机器人账号，
    但动作请求未指定要使用的账号。"""

    def __init__(self, data: Any = None, message: str = "") -> None:
        super().__init__(WHO_AM_I, data, message)


class UnknownSelf(OneBotImplError):
    """`10102` 未知的机器人账号。

    动作请求指定的机器人账号不存在。
    """

    def __init__(self, data: Any = None, message: str = "") -> None:
        super().__init__(UNKNOWN_SELF, data, message)


class BadHandler(OneBotImplError):
    """`20001` 无动作处理器实现错误。

    没有正确设置响应状态等。
    """

    def __init__(self, data: Any = None, message: str = "") -> None:
        super().__init__(BAD_HANDLER, data, message)


class InternalHandlerError(OneBotImplError):
    """`20002` 动作处理器运行时抛出异常。

    OneBot 实现内部发生了未捕获的意料之外的异常。"""

    def __init__(self, data: Any = None, message: str = "") -> None:
        super().__init__(INTERNAL_HANDLER_ERROR, data, message)
