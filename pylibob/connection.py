"""本模块实现了 OneBot Connect 的 HTTP 和 HTTP Webhook 部分
以及连接基类的定义。
"""
from __future__ import annotations

from asyncio import Queue
import json
from core.logger import Logger
from typing import TYPE_CHECKING, Any

from pylibob.asgi import asgi_app
from pylibob.event import Event
from pylibob.status import BAD_REQUEST
from pylibob.types import (
    ActionResponse,
    BotSelf,
    ContentType,
    FailedActionResponse,
)
from pylibob.utils import authorize, detect_content_type
from pylibob.version import __version__

from aiohttp import ClientSession, ClientTimeout
import msgpack
import msgspec
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_401_UNAUTHORIZED,
    HTTP_415_UNSUPPORTED_MEDIA_TYPE,
)

if TYPE_CHECKING:
    from pylibob.impl import OneBotImpl

log = Logger()
logger = log.get_logger(filename="connection")


class Connection:
    """连接基类。

    `init_connection` 方法为初始化连接的方法，用于在 `impl` 确定后继续初始化。
    顺序如下:
    ``` mermaid
    graph LR
        A[__init__] --> B[确定 impl] --> C[init_connection]
    ```

    `run_action` 用于以原始数据运行动作响应器。

    `emit_event` 用于向应用端推送事件，需各连接自行实现。

    Attributes:
        access_token (str | None): 访问令牌
        impl (OneBotImpl): OneBot 实现实例
    """

    def __init__(
        self,
        *,
        access_token: str | None = None,
    ) -> None:
        """初始化连接。

        Args:
            access_token (str | None): 访问令牌
        """
        self.access_token = access_token
        self._impl: "OneBotImpl" | None = None
        super().__init__()

    @property
    def impl(self) -> "OneBotImpl":
        """OneBot 实现实例。`"""
        if self._impl is None:
            raise ValueError("OneBotImpl is not initialed")
        return self._impl

    async def run_action(
        self,
        data: dict[str, Any],
    ) -> ActionResponse:
        """以原始数据运行动作响应器。

        - 未传入 `action` 或 `params` 时返回 10001 Bad Request。

        Args:
            data (dict[str, Any]): 原始数据
        """
        if not (action := data.get("action")):
            return FailedActionResponse(
                retcode=BAD_REQUEST,
                message="`action` is not exist.",
            )
        if (params := data.get("params")) is None:
            return FailedActionResponse(
                retcode=BAD_REQUEST,
                message="`params` is not exist.",
            )
        echo = data.get("echo")
        bot_self: BotSelf | None = data.get("self")
        return await self.impl.handle_action(action, params, bot_self, echo)

    def init_connection(self) -> None:
        """初始化连接。"""

    async def emit_event(self, event: Event) -> None:
        """向应用端推送事件。

        需要各连接自行实现。

        Args:
            event (Event): 事件
        """
        raise NotImplementedError


class ServerConnection(Connection):
    """服务器连接（HTTP/正向 WebSocket）基类。

    服务器连接会由 ServerRunner 运行（uvicorn）。

    Attributes:
        access_token (str | None): 访问令牌
        host (str): 服务器监听 IP
        port (int): 服务器监听端口
    """

    def __init__(
        self,
        *,
        access_token: str | None = None,
        host: str = "0.0.0.0",
        port: int = 8080,
    ) -> None:
        """初始化服务器连接。

        Args:
            access_token (str | None): 访问令牌
            host (str): 服务器监听 IP
            port (int): 服务器监听端口
        """
        super().__init__(access_token=access_token)
        self.host = host
        self.port = port


class HTTP(ServerConnection):
    """[HTTP 连接](https://12.onebot.dev/connect/communication/http/)。

    当启用 `get_latest_events` 元动作时，连接会创建一个大小为 `event_buffer_size` 的事件队列 `event_queue`。

    Attributes:
        access_token (str | None): 访问令牌
        host (str): HTTP 服务器监听 IP
        port (int): HTTP 服务器监听端口
        event_queue (Queue[Event] | None): 事件队列
    """  # noqa: E501

    def __init__(
        self,
        *,
        access_token: str | None = None,
        host: str = "0.0.0.0",
        port: int = 8080,
        event_enabled: bool = True,
        event_buffer_size: int = 20,
    ) -> None:
        """初始化 HTTP 连接。

        Args:
            access_token (str | None): 访问令牌
            host (str): HTTP 服务器监听 IP
            port (int): HTTP 服务器监听端口
            event_enabled (bool): 是否启用 `get_latest_events` 元动作
            event_buffer_size (int): 事件缓冲区大小
        """
        self.logger = log.get_logger(filename="connection.http")

        super().__init__(access_token=access_token, host=host, port=port)
        self.event_queue: Queue[Event] | None = (
            Queue(maxsize=event_buffer_size) if event_enabled else None
        )

    async def receive_http_request(self, request: Request) -> Response:
        # 鉴权
        if not authorize(self.access_token, request):
            # 如果鉴权失败，必须返回 HTTP 状态码 401 Unauthorized
            self.logger.warning(f"{request.url} 鉴权失败")
            return Response(status_code=HTTP_401_UNAUTHORIZED)
        # 检查 Content-Type
        if not (
            content_type := detect_content_type(
                request.headers.get("Content-Type") or "",
            )
        ):
            self.logger.warning(
                f"{request.url} Content-Type 不为 application/json "
                "或 application/msgpack",
            )
            return Response(status_code=HTTP_415_UNSUPPORTED_MEDIA_TYPE)

        body = await request.body()
        if content_type == ContentType.JSON:
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                return JSONResponse(
                    msgspec.to_builtins(
                        FailedActionResponse(
                            retcode=BAD_REQUEST,
                            message="Invalid JSON",
                        ),
                    ),
                )
        else:
            try:
                data = msgpack.unpackb(body)
            except msgpack.UnpackException:
                return Response(
                    msgspec.msgpack.encode(
                        FailedActionResponse(
                            retcode=BAD_REQUEST,
                            message="Invalid MessagePack",
                        ),
                    ),
                )
        self.logger.info(
            f"[RECEIVE({content_type.name}) <= {request.url}] {data}",
        )
        resp = await self.run_action(data)
        convert_func = (
            msgspec.json.encode
            if content_type == ContentType.JSON
            else msgspec.msgpack.encode
        )
        return Response(
            convert_func(resp),
            headers={"Content-Type": content_type.value},
        )

    async def action_get_latest_events(self, limit: int = 0, timeout: int = 0):
        """[获取最新事件列表](https://12.onebot.dev/interface/meta/actions/#get_latest_events)"""
        # TODO: long polling
        assert self.event_queue
        times = 1
        events = []
        while not self.event_queue.empty() and (limit == 0 or times <= limit):
            events.append((await self.event_queue.get()).dict())
            times += 1
        return events

    def init_connection(self) -> None:
        asgi_app.add_route(
            "/",
            self.receive_http_request,
            ["POST"],
            f"{self.impl.name}-{self.impl.version}-http",
            False,
        )
        if self.event_queue:
            self.logger.info("启用元动作 get_latest_events")
            self.impl.register_action_handler(
                "get_latest_events",
                self.action_get_latest_events,
            )

    async def emit_event(self, event: Event) -> None:
        if self.event_queue:
            if self.event_queue.full():
                self.event_queue.get_nowait()  # pop the oldest event
            self.event_queue.put_nowait(event)


class ClientConnection(Connection):
    """客户端连接（HTTP Webhook/反向 WebSocket）基类。

    Attributes:
        access_token (str | None): 访问令牌
        url (str): OneBot 应用的连接目标地址
        ua (str): 连接时使用的 User-Agent
    """

    def __init__(
        self,
        url: str,
        *,
        access_token: str | None = None,
    ) -> None:
        """初始化客户端连接。

        Args:
            access_token (str | None): 访问令牌
            url (str): OneBot 应用的连接目标地址
        """
        super().__init__(access_token=access_token)
        self.url = url

    @property
    def ua(self) -> str:
        """连接时使用的 User-Agent。"""
        return (
            f"OneBot/{self.impl.onebot_version} "
            f"pylibob/{__version__} "
            f"{self.impl.name}/{self.impl.version}"
        )


class HTTPWebhook(ClientConnection):
    """[HTTP Webhook 连接](https://12.onebot.dev/connect/communication/http-webhook/)。

    Attributes:
        access_token (str | None): 访问令牌
        url (str): Webhook 上报地址
        timeout (int): 上报请求超时时间，单位: 毫秒，0 表示不超时
    """

    def __init__(
        self,
        url: str,
        *,
        access_token: str | None = None,
        timeout: int = 5000,
    ) -> None:
        """初始化 HTTP Webhook 连接。

        Args:
            access_token (str | None): 访问令牌
            url (str): Webhook 上报地址
            timeout (int): 上报请求超时时间，单位: 毫秒，0 表示不超时
        """
        super().__init__(url, access_token=access_token)
        self.timeout = timeout
        self.logger = log.get_logger(filename="connection.http_webhook")

    def _make_header(self) -> dict[str, str]:
        header = {
            "Content-Type": "application/json",
            "User-Agent": self.ua,
            "X-OneBot-Version": self.impl.onebot_version,
            "X-Impl": self.impl.name,
        }
        if self.access_token:
            header["Authorization"] = f"Bearer {self.access_token}"
        return header

    async def emit_event(self, event: Event) -> None:
        async with ClientSession(
            headers=self._make_header(),
        ) as session:
            event_json = event.dict()
            self.logger.debug(f"[SEND => {self.url}] {event_json}")
            async with session.post(
                self.url,
                timeout=ClientTimeout(total=self.timeout / 1000),
                json=event_json,
            ) as resp:
                if resp.status == HTTP_204_NO_CONTENT:
                    # 如果响应状态码为 204 No Content，
                    # 应认为事件推送成功，并不做更多处理。
                    return
                if resp.status != HTTP_200_OK:
                    # 如果响应状态码不是 204 或 200 中的任一个，
                    # 应认为事件推送失败。
                    self.logger.warning(
                        f"事件推送失败: {resp.status} {resp.reason}",
                    )
                    return

                # 如果响应状态码为 200 OK，也应认为事件推送成功，
                # 此时应该根据响应头中的 Content-Type
                # 将响应体解析为动作请求列表，依次处理动作请求，丢弃动作响应。
                if not (
                    content_type := detect_content_type(
                        resp.headers.get("Content-Type") or "",
                    )
                ):
                    self.logger.warning(
                        "Content-Type 不为 application/json "
                        "或 application/msgpack",
                    )

                body = await resp.read()
                if content_type == ContentType.JSON:
                    try:
                        data = json.loads(body)
                    except json.JSONDecodeError:
                        return
                else:
                    try:
                        data = msgpack.unpackb(body)
                    except msgpack.UnpackException:
                        return
                self.logger.debug(f"[RECEIVE <= {self.url}] {data}")
                for action in data:
                    await self.run_action(action)
