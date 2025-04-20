"""本模块实现了 OneBot Connect 的 正反向 WebSocket 的部分以及 WebSocket 连接的基类。
"""  # noqa: E501
from __future__ import annotations

import abc
import asyncio
import json
from core.logger import Logger
import time
from typing import Any, NoReturn
from uuid import uuid4

from pylibob.asgi import asgi_app, asgi_lifespan_manager
from pylibob.connection import ClientConnection, Connection, ServerConnection
from pylibob.event import Event, MetaConnectEvent, MetaHeartbeatEvent
from pylibob.types import ContentType
from pylibob.utils import TaskManager, authorize, background_task

from aiohttp import (
    ClientError,
    ClientSession,
    ClientWebSocketResponse,
    WSMsgType,
)
import msgpack
import msgspec
from starlette.status import HTTP_401_UNAUTHORIZED
from starlette.websockets import (
    WebSocket as WS,
    WebSocketDisconnect,
)
from websockets.exceptions import ConnectionClosed

log = Logger()
logger = log.get_logger(filename="connection_ws")


class ConnectClosed(Exception):
    ...


class WSProtocol(abc.ABC):
    """抽象 WS 协议类。

    用于内部的统一处理。
    """

    @abc.abstractmethod
    async def send_json(self, data: Any) -> None:
        """以 JSON 形式发送数据。

        Args:
            data (Any): 要发送的数据
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def send_msgpack(self, data: Any) -> None:
        """以 MessagePack 形式发送数据。

        Args:
            data (Any): 要发送的数据
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def receive(self) -> tuple[ContentType, Any]:
        """接收数据

        Returns:
            前者为数据传输类型，后者为数据
        """
        raise NotImplementedError


class ServerWSProtocol(WSProtocol):
    """服务器 WS 协议类。

    包装 `starlette.websockets.WebSocket`。
    """

    def __init__(self, ws: WS) -> None:
        self.ws = ws

    async def send_json(self, data: Any) -> None:
        logger.debug(f"[SEND_JSON => {self.ws.url}] {data}")
        await self.ws.send_json(data)

    async def send_msgpack(self, data: Any):
        logger.debug(f"[SEND_MSGPACK => {self.ws.url}] {data}")
        await self.ws.send_bytes(msgpack.packb(data))  # type: ignore

    async def receive(self) -> tuple[ContentType, Any]:
        message = await self.ws.receive()
        self.ws._raise_on_disconnect(message)  # noqa: SLF001
        if "text" in message:
            # JSON
            data = json.loads(message["text"])
            content_type = ContentType.JSON
        else:
            # MessagePack
            data = msgpack.unpackb(message["bytes"])
            content_type = ContentType.MSGPACK
        logger.debug(f"[RECEIVE({content_type.name}) <= {self.ws.url}] {data}")
        return content_type, data


class ClientWSProtocol(WSProtocol):
    """客户端 WS 协议类。

    包装 `aiohttp.ClientWebSocketResponse`。
    """

    def __init__(self, ws: ClientWebSocketResponse) -> None:
        self.ws = ws

    async def send_json(self, data: Any):
        logger.debug(
            f"[SEND_JSON => {self.ws._response.url}] {data}",  # noqa: SLF001
        )
        await self.ws.send_json(data)

    async def send_msgpack(self, data: Any):
        logger.debug(
            "[SEND_MSGPACK => "
            f"{self.ws._response.url}] {data}",  # noqa: SLF001
        )
        await self.ws.send_bytes(msgpack.packb(data))  # type: ignore

    async def receive(self) -> Any:
        message = await self.ws.receive()
        if message.type in {
            WSMsgType.CLOSE,
            WSMsgType.ERROR,
            WSMsgType.CLOSED,
        }:
            raise ConnectClosed
        if message.type == WSMsgType.TEXT:
            # JSON
            data = json.loads(message.data)
            content_type = ContentType.JSON
        else:
            # MessagePack
            data = msgpack.unpackb(message.data)
            content_type = ContentType.MSGPACK
        logger.debug(
            f"[RECEIVE({content_type.name}) <= "
            f"{self.ws._response.url}] {data}",  # noqa: SLF001
        )
        return content_type, data


class WebSocketConnection(Connection):
    """WebSocket 连接基类。

    WebSocket 会在启用心跳时，启动心跳服务，每隔 `heartbeat_interval` 毫秒发送心跳。

    Attributes:
        access_token (str | None): 访问令牌
        enable_heartbeat (bool): 是否启用心跳
        heartbeat_interval (int): 心跳间隔。单位: 毫秒
    """  # noqa: E501

    def __init__(
        self,
        *,
        access_token: str | None = None,
        enable_heartbeat: bool = True,
        heartbeat_interval: int = 5000,
    ) -> None:
        """初始化 WebSocket 连接。

        Args:
            access_token (str | None): 访问令牌
            enable_heartbeat (bool): 是否启用心跳
            heartbeat_interval (int): 心跳间隔。单位: 毫秒
        """
        super().__init__(access_token=access_token)
        self.enable_heartbeat = enable_heartbeat
        if heartbeat_interval <= 0:
            raise ValueError("The interval of heartbeat must be positive")
        self.heartbeat_interval = heartbeat_interval
        self.task_manager = TaskManager()
        self.ws: list[WSProtocol] = []
        self._heartbeat_run = True

    async def _heartbeat(self) -> None:
        while self._heartbeat_run:
            try:
                for ws in self.ws:
                    if ws.ws.closed:
                        self.logger.warning("连接已关闭，尝试断开并重新连接")
                        try:
                            await ws.ws.close()
                        except Exception:
                            pass
                        await self.connect_to_remote()
                        continue
                    await ws.send_json(
                        MetaHeartbeatEvent(
                            id=str(uuid4()),
                            time=time.time(),
                            interval=self.heartbeat_interval,
                        ).dict(),
                    )
                await asyncio.sleep(self.heartbeat_interval / 1000)
            except Exception:
                logger.exception("推送心跳事件时发生异常")
                try:
                    await ws.ws.close()
                except Exception:
                    pass
                await self.connect_to_remote()

    async def _start_heartbeat(self) -> None:
        logger.info(f"启动 {self.__class__.__name__} 心跳服务")
        task = asyncio.create_task(self._heartbeat())
        background_task.add(task)
        task.add_done_callback(background_task.remove)

    async def _stop_heartbeat(self) -> None:
        logger.info(f"停止 {self.__class__.__name__} 心跳服务")
        self._heartbeat_run = False
        self.task_manager.cancel_all()

    async def listen_ws(self, ws: WSProtocol) -> NoReturn:
        """监听 WebSocket 连接。

        Args:
            ws (WSProtocol): WebSocket 协议实例
        """
        while True:
            content_type, message = await ws.receive()
            resp = await self.run_action(message)
            send_func = (
                ws.send_json
                if content_type == ContentType.JSON
                else ws.send_msgpack
            )
            await send_func(msgspec.to_builtins(resp))

    async def emit_event(self, event: Event) -> None:
        for ws in self.ws:
            event_dict = event.dict()
            # print(event_dict)
            task = asyncio.create_task(ws.send_json(event_dict))
            background_task.add(task)
            task.add_done_callback(background_task.remove)


class WebSocket(WebSocketConnection, ServerConnection):
    """[正向 WebSocket 连接](https://12.onebot.dev/connect/communication/websocket/)。

    Attributes:
        access_token (str | None): 访问令牌
        host (str): WebSocket 服务器监听 IP
        port (int): WebSocket 服务器端口
        enable_heartbeat (bool): 是否启用心跳
        heartbeat_interval (int): 心跳间隔。单位: 毫秒
    """

    def __init__(
        self,
        *,
        access_token: str | None = None,
        host: str = "0.0.0.0",
        port: int = 8080,
        enable_heartbeat: bool = True,
        heartbeat_interval: int = 5000,
    ) -> None:
        """初始化正向 WebSocket 连接。

        Args:
            access_token (str | None): 访问令牌
            host (str): WebSocket 服务器监听 IP
            port (int): WebSocket 服务器端口
            enable_heartbeat (bool): 是否启用心跳
            heartbeat_interval (int): 心跳间隔。单位: 毫秒
        """
        super().__init__(
            access_token=access_token,
            enable_heartbeat=enable_heartbeat,
            heartbeat_interval=heartbeat_interval,
        )
        super(WebSocketConnection, self).__init__(host=host, port=port)
        self.logger = log.get_logger(filename="connection_ws.websocket")

    def _enable_heartbeat(self):
        asgi_lifespan_manager.on_startup(self._start_heartbeat)
        asgi_lifespan_manager.on_shutdown(self._stop_heartbeat)

    def init_connection(self) -> None:
        asgi_app.add_websocket_route(
            "/",
            self.handle_ws_request,
            f"{self.impl.name}-{self.impl.version}-ws",
        )

        if self.enable_heartbeat:
            self._enable_heartbeat()

    async def handle_ws_request(self, ws: WS) -> None:
        if not authorize(self.access_token, ws):
            # 如果鉴权失败，必须返回 HTTP 状态码 401 Unauthorized
            self.logger.warning(f"{ws.url} 鉴权失败")
            await ws.close(HTTP_401_UNAUTHORIZED)
        await ws.accept()
        self.logger.info(f"接受连接: {ws.url}")
        ws_protocol = ServerWSProtocol(ws)
        await ws_protocol.send_json(
            MetaConnectEvent(
                id=str(uuid4()),
                time=time.time(),
                version=self.impl.impl_ver,
            ).dict(),
        )
        self.ws.append(ws_protocol)
        try:
            await self.listen_ws(ws_protocol)
        except (WebSocketDisconnect, ConnectionClosed):
            self.logger.warning(f"连接中断: {ws.url}")
            self.ws.remove(ws_protocol)


class WebSocketReverse(
    ClientConnection,
    WebSocketConnection,
):
    """[反向 WebSocket 连接](https://12.onebot.dev/connect/communication/websocket-reverse/)。

    Attributes:
        access_token (str | None): 访问令牌
        reconnect_interval (int): 重连间隔。单位: 毫秒
        enable_heartbeat (bool): 是否启用心跳
        heartbeat_interval (int): 心跳间隔。单位: 毫秒
    """

    def __init__(
        self,
        url: str,
        *,
        access_token: str | None = None,
        reconnect_interval: int = 5000,
        enable_heartbeat: bool = True,
        heartbeat_interval: int = 5000,
    ) -> None:
        """初始化反向 WebSocket 连接。

        Args:
            access_token (str | None): 访问令牌
            reconnect_interval (int): 重连间隔。单位: 毫秒
            enable_heartbeat (bool): 是否启用心跳
            heartbeat_interval (int): 心跳间隔。单位: 毫秒
        """
        super().__init__(
            url=url,
            access_token=access_token,
        )
        super(ClientConnection, self).__init__(
            enable_heartbeat=enable_heartbeat,
            heartbeat_interval=heartbeat_interval,
        )
        self.url = url
        if reconnect_interval <= 0:
            raise ValueError("The interval of reconnection must be positive")
        self.reconnect_interval = reconnect_interval
        self.logger = log.get_logger(
            "pylibob.connection_ws.websocket_reverse",
        )

    async def connect_to_remote(self) -> NoReturn:
        async with ClientSession() as session:
            self.logger.info(f"尝试连接到反向 WS 服务器: {self.url}")
            ws_protocol: ClientWSProtocol | None = None
            while True:
                try:
                    async with session.ws_connect(
                        self.url,
                        headers={
                            "User-Agent": self.ua,
                            "Sec-WebSocket-Protocol": (
                                f"{self.impl.onebot_version}.{self.impl.name}"
                            ),
                        },
                    ) as resp:
                        ws_protocol = ClientWSProtocol(resp)
                        self.ws.append(ws_protocol)
                        await ws_protocol.send_json(
                            MetaConnectEvent(
                                id=str(uuid4()),
                                time=time.time(),
                                version=self.impl.impl_ver,
                            ).dict(),
                        )
                        self.logger.info(
                            f"连接到反向 WS 服务器成功 - URL: {self.url} | 协议版本: {self.impl.onebot_version}.{self.impl.name} | 实现版本: {self.impl.impl_ver}"
                        )
                        await self.listen_ws(
                            ws=ws_protocol,
                        )
                except (ClientError, ConnectClosed, ConnectionError) as e:
                    if ws_protocol:
                        self.ws.remove(ws_protocol)
                        ws_protocol = None
                    self.logger.warning(
                        f"连接到反向 WS 服务器 {self.url} 失败: {e}, "
                        f"将在 {self.reconnect_interval} 毫秒后重连",
                    )
                    await asyncio.sleep(
                        self.reconnect_interval / 1000,
                    )
                except Exception:
                    self.logger.exception("监听 WS 连接时出错")
                finally:
                    if ws_protocol:
                        self.ws.remove(ws_protocol)
                        ws_protocol = None

    async def run(self) -> None:
        self.task_manager.task_nowait(self.connect_to_remote)
