"""pylibob ASGI App 部分。"""
from __future__ import annotations

from contextlib import asynccontextmanager

from pylibob.utils import LifespanManager

from starlette.applications import Starlette

asgi_lifespan_manager = LifespanManager()
"""ASGI 生命周期管理器。"""


@asynccontextmanager
async def _lifespan(_: Starlette):
    await asgi_lifespan_manager.startup()
    try:
        yield
    finally:
        await asgi_lifespan_manager.shutdown()


asgi_app = Starlette(debug=True, lifespan=_lifespan)
"""ASGI App -- Starlette。"""
