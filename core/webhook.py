from __future__ import annotations

import asyncio
import json
from core.logger import Logger
from config import LOG_CONFIG

log = Logger(LOG_CONFIG)
import re
from typing import Any
from uuid import uuid4

from aiohttp import web
from pylibob.event import Event
from pylibob.event.message import PrivateMessageEvent, GroupMessageEvent
from pylibob.impl import OneBotImpl

logger = log.get_logger(filename="webhook")

class VoceChatWebhook:
    def __init__(self, impl: OneBotImpl, host: str, port: int) -> None:
        self.impl = impl
        self.host = host
        self.port = port
        self.app = web.Application()
        self.app.router.add_get("/", self.health_check)
        self.app.router.add_post("/", self.handle_webhook)
        self.runner: web.AppRunner | None = None

    async def health_check(self, request: web.Request) -> web.Response:
        """健康检查，返回200状态码"""
        return web.Response(status=200)

    async def handle_webhook(self, request: web.Request) -> web.Response:
        """处理VoceChat的webhook请求"""
        try:
            data = await request.json()
            logger.debug(f"Received webhook data: {data}")
            
            # 提取基本信息
            message_id = str(data.get("mid", ""))
            from_user_id = str(data.get("from_uid", ""))
            target = data.get("target", {})
            detail = data.get("detail", {})
            content = detail.get("content", "")
            content_type = detail.get("content_type", "")
            
            # 构建消息内容
            message = []
            
            # 处理回复消息
            if detail.get("type") == "reply":
                reply_mid = str(detail.get("mid", ""))  # 被回复的消息ID
                message.append({
                    "type": "reply",
                    "data": {
                        "message_id": reply_mid,
                        "user_id": from_user_id
                    }
                })
            
            # 处理@消息
            mention_pattern = r"@(\d+)\s"
            current_pos = 0
            for match in re.finditer(mention_pattern, content):
                # 添加@之前的文本
                if match.start() > current_pos:
                    message.append({
                        "type": "text",
                        "data": {"text": content[current_pos:match.start()]}
                    })
                
                # 添加@消息段
                message.append({
                    "type": "mention",
                    "data": {"user_id": match.group(1)}
                })
                current_pos = match.end()
            
            # 添加剩余文本
            if current_pos < len(content):
                message.append({
                    "type": "text",
                    "data": {"text": content[current_pos:]}
                })
            
            # 如果消息列表为空，添加一个空文本消息段
            if not message:
                message.append({
                    "type": "text",
                    "data": {"text": content}
                })
            
            # 如果是文件消息，添加文件信息
            if content_type == "vocechat/file":
                properties = detail.get("properties", {})
                file_type = properties.get("content_type", "")
                if file_type.startswith("image/"):
                    message.append({
                        "type": "image",
                        "data": {"file_id": content}
                    })
            
            # 确定消息类型（群聊/私聊）
            # 生成事件唯一标识符
            event_id = str(uuid4())
            created_at = data.get("created_at", 0) / 1000
            if "gid" in target:
                event = GroupMessageEvent(
                    self=list(self.impl.bots.values())[0],
                    id=event_id,
                    message_id=message_id,
                    message=message,
                    alt_message=content,
                    group_id=str(target["gid"]),
                    user_id=from_user_id,
                    time=created_at
                )
            else:
                event = PrivateMessageEvent(
                    self=list(self.impl.bots.values())[0],
                    id=event_id,
                    message_id=message_id,
                    message=message,
                    alt_message=content,
                    user_id=from_user_id,
                    time=created_at
                )
                # print(event.dict())
            
            # 创建并发送事件
            await self.impl.update_status()
            asyncio.create_task(self.impl.emit(event))
            # 更新好友信息
            from core.bot_actions import FriendManager
            friend_manager = FriendManager(self.impl)
            await friend_manager.update_friend_info(from_user_id)
            
            return web.Response(status=200)
            
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return web.Response(status=500)

    async def start(self) -> None:
        """启动webhook服务器"""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.host, self.port)
        await site.start()
        logger.info(f"VoceChat webhook server started at http://{self.host}:{self.port}")

    async def stop(self) -> None:
        """停止webhook服务器"""
        if self.runner:
            await self.runner.cleanup()
            logger.info("VoceChat webhook server stopped")