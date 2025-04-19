"""本模块实现了 OneBot 实现（OneBot Implementation）的类 `OneBotImpl`。"""
from __future__ import annotations

import asyncio
import inspect
from core.logger import Logger
import sys
import time
from typing import Any, Callable, NamedTuple, cast
from uuid import uuid4

from pylibob.connection import Connection, HTTPWebhook, ServerConnection
from pylibob.connection_ws import WebSocketConnection, WebSocketReverse
from pylibob.event import Event, MetaStatusUpdateEvent
from pylibob.exception import OneBotImplError
from pylibob.runner import ClientRunner, ServerRunner
from pylibob.status import (
    BAD_PARAM,
    INTERNAL_HANDLER_ERROR,
    OK,
    UNKNOWN_SELF,
    UNSUPPORTED_ACTION,
    UNSUPPORTED_PARAM,
    WHO_AM_I,
)
from pylibob.types import (
    ActionHandler,
    ActionResponse,
    Bot,
    BotSelf,
    FailedActionResponse,
    Status,
)
from pylibob.utils import (
    TaskManager,
    TypingType,
    analytic_typing,
    background_task,
)

import msgspec
from msgspec import Struct, ValidationError, defstruct

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

log = Logger()
logger = log.get_logger(filename="impl")


class ActionHandlerWithValidate(NamedTuple):
    handler: ActionHandler
    keys: set[str]
    typing_types: dict[str, tuple[type, TypingType]]
    model: type[Struct] | None


class OneBotImpl:
    """OneBot 实现类。

    OneBot 实现的主体包装:
        动作: 使用 `action` 装饰器注册。

        事件: 使用 `emit` 方法推送。

    内部已实现元动作 `get_version` `get_status` `get_supported_actions`。

    状态更新事件使用 `update_status` 方法推送。

    Attributes:
        name (str): 实现名称
        version (str): 实现版本
        conns (list[Connection]): 实现启用的连接列表
        conn_types (set[str]): 实现启用的连接类型
        onebot_version (str): OneBot 标准版本号
        is_good (bool): OneBot 实现运行状态是否正常
    """

    def __init__(
        self,
        name: str,
        version: str,
        conns: list[Connection],
        *bots: Bot,
        onebot_version: str = "12",
    ) -> None:
        """初始化 OneBot 实现。

        Args:
            name (str): 实现名称
            version (str): 实现版本
            conns (list[Connection]): 实现启用的连接列表
            onebot_version (str, optional): OneBot 标准版本号 Defaults to "12".
            *bots (Bot): 一系列 Bot 实例

        Raises:
            ValueError: 未提供 Bot 实例。
            ValueError: 启用的连接为空。
        """
        self.conns = conns
        self.conn_types = set()
        self.name = name
        self.version = version
        self.onebot_version = onebot_version
        self.is_good = True
        self.actions: dict[str, ActionHandlerWithValidate] = {}
        if not bots:
            raise ValueError("OneBotImpl needs at least one bot")
        self.bots: dict[str, Bot] = {
            f"{bot.platform}.{bot.user_id}": bot for bot in bots
        }

        if not conns:
            raise ValueError(
                "Connections are empty, "
                "OneBotImpl needs at least one connection to start",
            )
        for conn in conns:
            if conn.__class__ in self.conn_types:
                continue
            conn._impl = self  # noqa: SLF001
            conn.init_connection()
            self.conn_types.add(conn.__class__)

        self.register_action_handler("get_status", self._action_get_status)
        self.register_action_handler("get_version", self._action_get_version)
        self.register_action_handler(
            "get_supported_actions",
            self._action_get_supported_actions,
        )

    @property
    def status(self) -> Status:
        """当前 OneBot 实现的状态。

        此属性会作为动作 `get_status` 的返回值，也会作为状态更新事件 `meta.status_update` 的 `status`。
        """  # noqa: E501
        return {
            "good": self.is_good,
            "bots": [bot.dict_for_status() for bot in self.bots.values()],
        }

    @property
    def impl_ver(self) -> dict[str, str]:
        """当前 OneBot 的版本信息。

        此属性会作为动作 `get_version` 的返回值，也会作为连接事件 `meta.connect` 的 `version`。
        """  # noqa: E501
        return {
            "impl": self.name,
            "version": self.version,
            "onebot_version": self.onebot_version,
        }

    def register_action_handler(
        self,
        action: str,
        func: ActionHandler,
    ) -> ActionHandler:
        """注册一个动作响应器。

        可以注册标准动作和扩展动作（建议包含前缀）。

        动作响应器的函数可以使用 Type Hints 声明动作参数及类型，不符合 Type Hints 的动作将由 pylibob 自动返回 `10003 Bad Param`；
        多余的参数会由 pylibob 自动返回 `10006 Unsupported Param`。

        对于扩展参数，可以使用 Annotated 标注类型，第一个 metadata 会被视为参数名。

        对于注解为 `Bot` 的，pylibob 会内部处理为请求动作的 Bot 实例。

        支持使用默认值。

        动作响应器的返回值会作为动作响应的 `data`。

        示例:
            ```python
            @impl.action("hello")
            async def _(
                a: str,
                b: Annotated[int, "extra.param"],
                c: Bot,
                d: int = 5,
            ):
                return a, b, c, d
            ```

            此动作 `hello` 需要必须参数:

                a (string)
                extra.param (int)

            可选参数:

                d (int) (default = 5)

        Args:
            action (str): 动作名
            func (ActionHandler): 响应器函数

        Returns:
            响应器函数
        """  # noqa: E501
        types = analytic_typing(func)
        keys = set()
        types_dict = {}
        struct_type = []
        for name, type_, default, typing_type in types:
            keys.add(name)
            types_dict[name] = type_, typing_type
            if default is inspect.Parameter.empty:
                struct_type.append((name, type_))
            else:
                struct_type.append((name, type_, default))
        self.actions[action] = ActionHandlerWithValidate(
            func,
            keys,
            types_dict,
            defstruct(f"{action}ValidateModel", struct_type),
        )
        logger.info(f"已注册动作: {action}")
        logger.debug(f"动作 {action} 类型: {types}")
        return func

    def action(
        self,
        action: str,
    ) -> Callable[[ActionHandler], ActionHandler]:
        """注册动作响应器的装饰器。

        Args:
            action (str): 动作名
        """

        def wrapper(
            func: ActionHandler,
        ) -> ActionHandler:
            self.register_action_handler(action, func)
            return func

        return wrapper

    async def handle_action(  # noqa: PLR0911
        self,
        action: str,
        params: dict[str, Any],
        bot_self: BotSelf | None = None,
        echo: str | None = None,
    ) -> ActionResponse:
        """处理动作请求。

        pylibob 自动处理的返回:
            - 不支持的动作，返回 `10002 Unsupported Action`。
            - 当前 OneBot 实现的 Bot 大于 1 时:
                - 未指定请求 Bot 的时候，返回 `10101 Who Am I`。
                - 提供的 Bot 实例不存在时，返回 `10102 Unknown Self`。
            - 参数类型校验失败时，返回 `10003 Bad Param`。
            - 含有多余参数时，返回 `10006 Unsupported Param`。
            - 运行响应器出错时，返回 `20002 Internal Handler Error`。

        Args:
            action (str): 动作名
            params (dict[str, Any]): 动作参数
            bot_self (BotSelf | None): 机器人自身标识
            echo (str | None): 动作请求标识

        Returns:
            动作响应
        """
        action_handler = self.actions.get(action)
        if not action_handler:
            return FailedActionResponse(
                retcode=UNSUPPORTED_ACTION,
                message="action is not supported",
                echo=echo,
            )
        handler, keys, types, model = action_handler
        if len(self.bots) > 1 and not bot_self:
            return FailedActionResponse(
                retcode=WHO_AM_I,
                message="bot is not detect",
                echo=echo,
            )

        bot_id = (
            f"{bot_self['platform']}.{bot_self['user_id']}" if bot_self else ""
        )
        if bot_id and bot_id not in self.bots:
            logger.warning(f"未找到 Bot: {bot_id}")
            return FailedActionResponse(
                retcode=UNKNOWN_SELF,
                message=f"bot {bot_id} is not exist",
                echo=echo,
            )
        bot = self.bots.get(bot_id) or next(iter(self.bots.values()))

        for name, type_detail in types.items():
            type_, typing_type = type_detail
            if typing_type is TypingType.BOT:
                params[name] = bot
            elif typing_type is TypingType.ANNOTATED:
                param_real_name = cast(Annotated, type_).__metadata__[0]
                params[name] = params.pop(param_real_name, None)

        try:
            msgspec.convert(params, model)
        except ValidationError as e:
            logger.warning(f"请求模型校验失败: {e}")
            return FailedActionResponse(retcode=BAD_PARAM, message=str(e))
        if extra_params := set(params) - set(keys):
            logger.warning(f"不支持的动作参数: {', '.join(extra_params)}")
            return FailedActionResponse(
                retcode=UNSUPPORTED_PARAM,
                message=f"Don't support params: {', '.join(extra_params)}",
            )
        try:
            logger.info(f"执行动作 {action}")
            data = await handler(**params)
        except OneBotImplError as e:
            return FailedActionResponse(
                retcode=e.retcode,
                message=e.message,
                data=e.data,
                echo=echo,
            )
        except Exception:
            logger.exception(f"执行 {action} 动作时出错:")
            return FailedActionResponse(
                retcode=INTERNAL_HANDLER_ERROR,
                echo=echo,
            )
        return ActionResponse(status="ok", retcode=OK, data=data, echo=echo)

    async def emit(
        self,
        event: Event,
        conns: list[Connection] | None = None,
    ) -> None:
        """推送事件到应用端。

        如果 `conns` 未指定，则将请求推送到所有连接。

        Args:
            event (Event): 事件
            conns (list[Connection] | None): 连接列表 Default to self.conns
        """
        if conns is None:
            conns = self.conns
        logger.debug(f"推送事件: {event}")
        for conn in conns:
            task = asyncio.create_task(conn.emit_event(event))
            background_task.add(task)
            task.add_done_callback(background_task.remove)

    async def _action_get_version(self):
        """[元动作]获取版本信息
        https://12.onebot.dev/interface/meta/actions/#get_version
        """
        return self.impl_ver

    async def _action_get_supported_actions(
        self,
    ):
        """[元动作]获取支持的动作列表

        https://12.onebot.dev/interface/meta/actions/#get_supported_actions
        """
        return list(self.actions.keys())

    async def _action_get_status(self):
        """[元动作]获取运行状态

        https://12.onebot.dev/interface/meta/actions/#get_status
        """
        return self.status

    def _get_host(self) -> tuple[str, int] | None:
        return next(
            (
                (conn.host, conn.port)
                for conn in self.conns
                if isinstance(conn, ServerConnection)
            ),
            None,
        )

    def _get_ws_reverse(self) -> WebSocketReverse | None:
        return next(
            (
                conn
                for conn in self.conns
                if isinstance(conn, WebSocketReverse)
            ),
            None,
        )

    def run(self) -> None:
        """运行 OneBot 实现。

        pylibob 会根据连接类型自动选择合适的
        Runner（ServerRunner 或 ClientRunner）。
        同时启动VoceChat webhook服务器。
        """
        from core.webhook import VoceChatWebhook
        from config import WEBHOOK_HOST, WEBHOOK_PORT # Import webhook config
        logger.debug(f"webhook host: {WEBHOOK_HOST} port: {WEBHOOK_PORT}")

        host = self._get_host()
        ws_reverse = self._get_ws_reverse()

        if host is not None:
            logger.debug("Runner 选中: ServerRunner")
            runner = ServerRunner(*host)
            if ws_reverse:
                logger.debug("向 ServerRunner 添加反向 WS 服务")

                async def _stop():
                    ws_reverse.task_manager.cancel_all()

                runner.on_startup(ws_reverse.run)
                runner.on_shutdown(_stop)
        elif ws_reverse:
            logger.debug("Runner 选中: ClientRunner (反向 WS)")
            runner = ClientRunner(ws_reverse.task_manager)
            runner.on_startup(ws_reverse.run)
        else:
            logger.debug("Runner 选中: ClientRunner")
            runner = ClientRunner(TaskManager())

        if ws_reverse and ws_reverse.enable_heartbeat:
            logger.debug("向 Runner 中添加反向 WS 心跳任务")
            runner.on_startup(ws_reverse._start_heartbeat)  # noqa: SLF001
            runner.on_shutdown(ws_reverse._stop_heartbeat)  # noqa: SLF001

        # 创建VoceChat webhook服务器
        webhook_server = VoceChatWebhook(self, WEBHOOK_HOST, WEBHOOK_PORT)
        runner.on_startup(webhook_server.start)
        runner.on_shutdown(webhook_server.stop)

        asyncio.run(runner.run())

    async def update_status(self) -> None:
        """更新状态。

        此方法仅在连接为 WebSocket 或 HTTP Webhook 时起作用。
        """
        await self.emit(
            MetaStatusUpdateEvent(
                id=str(uuid4()),
                time=time.time(),
                status=self.status,
            ),
            conns=[
                conn
                for conn in self.conns
                if isinstance(conn, (WebSocketConnection, HTTPWebhook))
            ],
        )
