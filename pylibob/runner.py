"""OneBot Connect 连接 Runner。"""
from __future__ import annotations

import abc
import asyncio
from core.logger import Logger
import signal
from typing import Any

from pylibob.asgi import asgi_app, asgi_lifespan_manager
from pylibob.utils import L_FUNC, LifespanManager, TaskManager

import uvicorn

HANDLED_SIGNALS = {
    signal.SIGINT,  # Unix kill -2(CTRL + C)
    signal.SIGTERM,  # Unix kill -15
}

log = Logger()
logger = log.get_logger(filename="runner")


class Runner(abc.ABC):
    """抽象运行器基类。

    Attributes:
        lifespan_manager (LifespanManager): 异步生命周期管理器
    """

    @abc.abstractmethod
    async def run(self) -> None:
        """启动运行器。"""
        raise NotImplementedError

    @abc.abstractmethod
    def on_startup(self, func: L_FUNC) -> None:
        """添加 startup 生命周期函数。"""
        raise NotImplementedError

    @abc.abstractmethod
    def on_shutdown(self, func: L_FUNC) -> None:
        """添加 shutdown 生命周期。"""
        raise NotImplementedError

    @abc.abstractproperty
    def lifespan_manager(self) -> LifespanManager:
        """异步生命周期管理器。"""
        raise NotImplementedError


class ServerRunner(Runner):
    """服务器运行器。

    Attributes:
        host (str): 服务器监听 IP
        port (int): 服务器监听端口
        uvicorn_params (dict[str, Any]): 传入到 uvicorn 的其他参数
    """

    def __init__(self, host: str, port: int, **kwargs: Any) -> None:
        """初始化服务器运行器。

        Args:
            host (str): 服务器监听 IP
            port (int): 服务器监听端口
            **kwargs: 传入到 uvicorn 的其他参数
        """
        self.host = host
        self.port = port
        self.uvicorn_params: dict[str, Any] = kwargs

    async def run(self):
        logger.info("启动 ServerRunner")
        await uvicorn.Server(
            uvicorn.Config(
                asgi_app,
                host=self.host,
                port=self.port,
                **self.uvicorn_params,
            ),
        ).serve()

    def on_startup(self, func: L_FUNC):
        asgi_lifespan_manager.on_startup(func)

    def on_shutdown(self, func: L_FUNC):
        asgi_lifespan_manager.on_shutdown(func)

    @property
    def lifespan_manager(self) -> LifespanManager:
        return asgi_lifespan_manager


class ClientRunner(Runner):
    """客户端运行器。

    Attributes:
        task_manager (TaskManager): 任务管理器
    """

    def __init__(self, task_manager: TaskManager) -> None:
        """初始化客户端运行器。

        Args:
            task_manager (TaskManager): 任务管理器
        """
        self.should_exit: asyncio.Event = asyncio.Event()
        self.force_exit: bool = False
        self.task_manager = task_manager
        self._lifespan_manager = LifespanManager()

    @property
    def lifespan_manager(self) -> LifespanManager:
        return self._lifespan_manager

    async def _loop(self):
        await self.should_exit.wait()

    def _handle_exit(self, sig, frame):
        self.should_exit.set()

    async def _shutdown(self):
        await self.lifespan_manager.shutdown()
        self.task_manager.cancel_all()

    def on_startup(self, func: L_FUNC):
        self.lifespan_manager.on_startup(func)

    def on_shutdown(self, func: L_FUNC):
        self.lifespan_manager.on_shutdown(func)

    async def run(self):
        for sig in HANDLED_SIGNALS:
            logger.debug(f"注册信号 {sig} 捕获器")
            signal.signal(sig, self._handle_exit)
        logger.info("启动 ClientRunner")
        await self.lifespan_manager.startup()
        await self._loop()
        await self._shutdown()
