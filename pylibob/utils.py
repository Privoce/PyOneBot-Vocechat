"""pylibob 辅助函数。"""
from __future__ import annotations

import asyncio
from dataclasses import asdict
from enum import Enum, auto
import inspect
from core.logger import Logger
import sys
from typing import Any, Awaitable, Callable, ForwardRef, cast, get_origin

from pylibob.types import ActionHandler, Bot, ContentType

from starlette.requests import HTTPConnection

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated


background_task = set()
log = Logger()
typing_logger = log.get_logger(filename="utils.typing")
task_logger = log.get_logger(filename="utils.task_manager")
lifespan_logger = log.get_logger(filename="utils.lifespan_manager")


def detect_content_type(type_: str) -> ContentType | None:
    try:
        return ContentType(type_)
    except ValueError:
        return None


def authorize(access_token: str | None, request: HTTPConnection) -> bool:
    if access_token is None:
        return True
    # 首先检查请求头中是否存在 Authorization 头
    if (
        request_token := request.headers.get("Authorization")
    ) and request_token == f"Bearer {access_token}":
        return True
    # 继续检查是否存在 access_token URL query 参数
    return bool(
        (request_token := request.query_params.get("access_token"))
        and request_token == access_token,
    )


def asdict_exclude_none(obj) -> dict[str, Any]:
    return asdict(
        obj,
        dict_factory=lambda x: {k: v for k, v in x if v is not None},
    )


class TypingType(Enum):
    NORMAL = auto()
    BOT = auto()
    ANNOTATED = auto()


# https://github.com/pydantic/pydantic/blob/main/pydantic/v1/typing.py#L56-L66
if sys.version_info < (3, 9):

    def evaluate_forwardref(
        type_: ForwardRef,
        globalns: Any,
        localns: Any,
    ) -> Any:
        return type_._evaluate(globalns, localns)  # noqa: SLF001

else:

    def evaluate_forwardref(
        type_: ForwardRef,
        globalns: Any,
        localns: Any,
    ) -> Any:
        # Even though it is the right signature for python 3.9,
        # mypy complains with
        # `error: Too many arguments for "_evaluate" of
        # "ForwardRef"` hence the cast...
        return cast(Any, type_)._evaluate(  # noqa: SLF001
            globalns,
            localns,
            recursive_guard=set(),
        )


def get_annotation(param: inspect.Parameter, globalns: dict[str, Any]) -> Any:
    annotation = param.annotation
    if isinstance(annotation, str):
        annotation = ForwardRef(annotation)
        try:
            annotation = evaluate_forwardref(annotation, globalns, globalns)
        except Exception as e:
            typing_logger.warning(
                f'Unknown ForwardRef["{param.annotation}"] '
                f'for parameter {param.name}',
                exc_info=e,
            )
            return inspect.Parameter.empty
    return annotation


def get_signature(call: Callable[..., Any]) -> inspect.Signature:
    signature = inspect.signature(call)
    globalns = getattr(call, "__globals__", {})
    typed_params = [
        inspect.Parameter(
            name=param.name,
            kind=param.kind,
            default=param.default,
            annotation=get_annotation(param, globalns),
        )
        for param in signature.parameters.values()
    ]
    return inspect.Signature(typed_params)


def analytic_typing(
    func: ActionHandler,
) -> list[tuple[str, type, Any, TypingType]]:
    signature = get_signature(func)
    types: list[tuple[str, type, Any, TypingType]] = []
    for name, parameter in signature.parameters.items():
        if (annotation := parameter.annotation) is inspect.Parameter.empty:
            raise TypeError(f"Parameter `{name}` has no annotation")
        if inspect.ismethod(func) and parameter.name == "self":
            continue
        default = parameter.default
        if annotation is Bot:
            type_ = (name, annotation, inspect.Parameter.empty, TypingType.BOT)
        elif get_origin(annotation) is Annotated:
            annotation: Annotated
            if not isinstance(annotation.__metadata__[0], str):
                raise TypeError(
                    f"The first metadata of Annotated of param `{parameter!s}`"
                    " is not str",
                )
            type_ = (name, annotation, default, TypingType.ANNOTATED)
        else:
            type_ = (name, annotation, default, TypingType.NORMAL)
        types.append(type_)
    return types


# https://code.luasoftware.com/tutorials/python/asyncio-graceful-shutdown/
class TaskManager:
    def __init__(self):
        self.tasks = set()

    async def task(self, func, result=None, *args, **kwargs) -> Any | None:
        task_logger.debug(f"添加任务: {func}({args}, {kwargs})")
        task = asyncio.create_task(func(*args, **kwargs))
        self.tasks.add(task)
        try:
            return await task
        except asyncio.CancelledError:
            return result
        finally:
            self.tasks.remove(task)

    def task_nowait(self, func, *args, **kwargs):
        task_logger.debug(f"添加任务(nowait): {func}({args}, {kwargs})")
        task = asyncio.create_task(func(*args, **kwargs))
        self.tasks.add(task)
        task.add_done_callback(self.tasks.remove)

    def cancel_all(self):
        for _task in self.tasks:
            if not _task.done():
                _task.cancel()


L_FUNC = Callable[[], Awaitable[Any]]


class LifespanManager:
    def __init__(self) -> None:
        self._startup_funcs: list[L_FUNC] = []
        self._shutdown_funcs: list[L_FUNC] = []

    def on_startup(self, func: L_FUNC) -> L_FUNC:
        lifespan_logger.debug(f"添加 startup 生命周期函数: {func}")
        self._startup_funcs.append(func)
        return func

    def on_shutdown(self, func: L_FUNC) -> L_FUNC:
        lifespan_logger.debug(f"添加 shutdown 生命周期函数: {func}")
        self._shutdown_funcs.append(func)
        return func

    async def startup(self) -> None:
        if self._startup_funcs:
            for func in self._startup_funcs:
                lifespan_logger.debug(f"执行 startup 生命周期函数: {func}")
                await func()

    async def shutdown(self) -> None:
        if self._shutdown_funcs:
            for func in self._shutdown_funcs:
                lifespan_logger.debug(f"执行 shutdown 生命周期函数: {func}")
                await func()
