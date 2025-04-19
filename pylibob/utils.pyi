"""pylibob 辅助函数。"""
from enum import Enum, auto
import inspect
from typing import Any, Awaitable, Callable, ForwardRef

from pylibob.types import ActionHandler, ContentType

from starlette.requests import HTTPConnection

background_task: set

def detect_content_type(type_: str) -> ContentType | None:
    """根据 MIME Type 选中 Content-Type。

    若无此类型则返回 `None`。

    Args:
        type_ (str): MIME Type

    Returns:
        Content-Type
    """

def authorize(access_token: str | None, request: HTTPConnection) -> bool:
    """对请求进行鉴权。

    若 `access_token` 为 None，则视为无访问密钥。

    Args:
        access_token (str | None): 访问密钥
        request (HTTPConnection): 请求

    Returns:
        鉴权是否通过
    """

class TypingType(Enum):
    """类型标注类型。"""

    NORMAL = auto()
    BOT = auto()
    ANNOTATED = auto()

def evaluate_forwardref(
    type_: ForwardRef,
    globalns: Any,
    localns: Any,
) -> Any:
    """解析 ForwardRef。

    Args:
        type_ (ForwardRef): ForwardRef
        globalns (Any): 当前全局作用域
        localns (Any): 当前局部作用域

    Returns:
        解析后的类型
    """

def get_signature(call: Callable[..., Any]) -> inspect.Signature:
    """获取函数签名。

    Args:
        call (Callable[..., Any]): 函数

    Returns:
        函数签名
    """

def analytic_typing(
    func: ActionHandler,
) -> list[tuple[str, type, Any, TypingType]]:
    """分析动作响应器类型。

    类型信息:
        - 0: 参数名称
        - 1: 参数类型
        - 2: 参数默认值（若为空则为 `inspect.Parameter.empty`）
        - 3: 参数的类型标注类型

    Args:
        func (ActionHandler): 动作响应器

    Returns:
        一个含有类型信息的列表
    """

class TaskManager:
    """异步任务管理器。"""

    async def task(self, func, result=None, *args, **kwargs) -> Any | None:
        """运行任务。

        Args:
            func (Callable[..., Any]): 任务函数
            result (Any | None): 任务被取消的默认返回值
            *args (Any): 任务函数的参数
            **kwargs (Any): 任务函数的关键字参数
        """
    def task_nowait(self, func, *args, **kwargs) -> None:
        """无等待添加任务。

        Args:
            func (Callable[..., Any]): 任务函数
            *args (Any): 任务函数的参数
            **kwargs (Any): 任务函数的关键字参数
        """
    def cancel_all(self) -> None:
        """取消所有任务。"""

L_FUNC = Callable[[], Awaitable[Any]]

class LifespanManager:
    """生命周期管理器。"""

    def on_startup(self, func: L_FUNC) -> None:
        """注册 startup 生命周期函数

        Args:
            func (L_FUNC): startup 生命周期函数
        """
    def on_shutdown(self, func: L_FUNC) -> None:
        """注册 shutdown 生命周期函数

        Args:
            func (L_FUNC): shutdown 生命周期函数
        """
    async def startup(self) -> None:
        """执行 startup 生命周期。"""
    async def shutdown(self) -> None:
        """执行 shutdown 生命周期。"""
