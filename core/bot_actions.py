# core/bot_actions.py

from __future__ import annotations

import asyncio
import base64
import json
import mimetypes
import os
import time
from typing import Any
from urllib.parse import urlparse

import aiofiles
import aiohttp
from pylibob import Bot, OneBotImpl
from core.logger import Logger
from config import SEND_PROXY, PROXY_ENABLED
log = Logger()
logger = log.get_logger(filename="bot_actions")
# --- Friend Management ---

class FriendManager:
    def __init__(self, impl: OneBotImpl):
        self.impl = impl
        self.friend_dict: dict[str, str] = {}
        self.storage_path = "friend_list.json"
        self.last_update_time = 0
        self._load_friend_list()

    def _load_friend_list(self) -> None:
        """从文件加载好友列表"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    self.friend_dict = json.load(f)
                # logger.debug("成功加载好友列表")
        except Exception as e:
            logger.error(f"加载好友列表失败: {e}")

    def _save_friend_list(self) -> None:
        """保存好友列表到文件"""
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.friend_dict, f, ensure_ascii=False, indent=2)
            # logger.debug("成功保存好友列表")
        except Exception as e:
            logger.error(f"保存好友列表失败: {e}")

    async def update_friend_info(self, user_id: str) -> None:
        """更新好友信息"""
        current_time = time.time()
        if current_time - self.last_update_time < 600:  # 10分钟 = 600秒
            return
            
        try:
            bot = _get_bot(self.impl)
            server_url = bot.extra["server_url"]
            api_key = bot.extra["api_key"]

            async with aiohttp.ClientSession() as session:
                headers = {"x-api-key": api_key}
                url = f"{server_url}/api/bot/user/{"{uid}"}?uid={user_id}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.friend_dict[user_id] = data.get("name", "")
                        self._save_friend_list()
                        self.last_update_time = current_time
                        logger.debug(f"更新好友信息成功: {user_id}")
                    else:
                        logger.error(f"获取用户信息失败: {response.status}")
        except Exception as e:
            logger.error(f"更新好友信息失败: {e}")

# --- Helper Functions --- (Moved from main.py)

def _get_bot(impl: OneBotImpl) -> Bot:
    """Helper function to get the bot instance."""
    if not impl.bots:
        raise RuntimeError("No bot configured")
    # Assuming only one bot for now
    return list(impl.bots.values())[0]

def _get_vocechat_headers(bot: Bot) -> dict[str, str]:
    """Helper function to get Vocechat API request headers."""
    return {
        "x-api-key": bot.extra.get("api_key", ""),
        "accept": "application/json",
    }

async def _vocechat_prepare_file(bot: Bot, session: aiohttp.ClientSession, filename: str, content_type: str) -> str:
    """Calls the Vocechat prepare API and returns the file_id (string)."""
    try:
        api_base = bot.extra.get("server_url", "")
        if not api_base:
            raise ValueError("Missing server_url in bot configuration")
            
        headers = _get_vocechat_headers(bot)
        # Prepare API needs JSON payload but returns plain text file_id
        headers["accept"] = "*/*"
        prepare_url = f"{api_base}/api/bot/file/prepare"
        payload = {"filename": filename, "content_type": content_type}

        try:
            async with session.post(prepare_url, headers=headers, json=payload) as resp:
                if resp.status >= 400:
                    error_text = await resp.text()
                    logger.error(f"文件准备API调用失败: HTTP {resp.status}, {error_text}")
                    raise ValueError(f"Vocechat prepare API failed with status {resp.status}: {error_text}")
                    
                # Docs say it returns the file_id string directly
                file_id = await resp.text()
                if not file_id:
                    raise ValueError("Vocechat prepare API returned an empty file_id")
                return file_id.strip('"') # Remove potential surrounding quotes
        except aiohttp.ClientError as e:
            logger.error(f"文件准备API调用时网络错误: {e}")
            raise ValueError(f"Network error during prepare file API call: {e}")
    except Exception as e:
        logger.error(f"文件准备过程中发生未处理的异常: {e}")
        raise

async def _vocechat_upload_file(bot: Bot, session: aiohttp.ClientSession, file_id: str, chunk_data: bytes, filename: str, content_type: str) -> dict[str, Any]:
    """Calls the Vocechat upload API and returns the JSON response containing 'path'."""
    try:
        api_base = bot.extra.get("server_url", "")
        if not api_base:
            raise ValueError("Missing server_url in bot configuration")
            
        headers = _get_vocechat_headers(bot)
        headers.update({
            "accept": "*/*",
            "cache-control": "no-cache",
            "pragma": "no-cache"
        })
        # Remove Content-Type if present in base headers, as FormData sets it
        headers.pop("Content-Type", None)

        upload_url = f"{api_base}/api/bot/file/upload"

        form = aiohttp.FormData()
        form.add_field("file_id", file_id)
        form.add_field("chunk_data", chunk_data, filename=filename, content_type=content_type)
        # Docs: set chunk_is_last to true for single-part uploads
        form.add_field("chunk_is_last", "true")

        try:
            async with session.post(upload_url, headers=headers, data=form, proxy=SEND_PROXY if PROXY_ENABLED else None) as resp:
                if resp.status >= 400:
                    error_text = await resp.text()
                    logger.error(f"文件上传API调用失败: HTTP {resp.status}, {error_text}")
                    raise ValueError(f"Vocechat upload API failed with status {resp.status}: {error_text}")
                    
                # Docs say the final response is JSON containing 'path'
                if "application/json" in resp.headers.get("Content-Type", ""):
                    try:
                        result = await resp.json()
                        if isinstance(result, dict) and "path" in result:
                            return result
                        else:
                            logger.error(f"文件上传API响应缺少'path'字段: {result}")
                            raise ValueError(f"Vocechat upload API response missing 'path': {result}")
                    except json.JSONDecodeError as e:
                        logger.error(f"解析文件上传响应时JSON解析错误: {e}")
                        raise ValueError(f"Failed to parse JSON response from upload API: {e}")
                else:
                    text_response = await resp.text()
                    logger.error(f"文件上传API未返回JSON格式: {text_response}")
                    raise ValueError(f"Vocechat upload API did not return JSON: {text_response}")
        except aiohttp.ClientError as e:
            logger.error(f"文件上传API调用时网络错误: {e}")
            raise ValueError(f"Network error during upload file API call: {e}")
    except Exception as e:
        logger.error(f"文件上传过程中发生未处理的异常: {e}")
        raise

# --- Action Handlers --- (Moved from main.py)

def register_actions(impl: OneBotImpl):
    """Register OneBot actions with the implementation."""
    friend_manager = FriendManager(impl)

    @impl.action("get_friend_list")
    async def get_friend_list() -> list[dict[str, Any]]:
        """获取好友列表"""
        friend_list = []
        for user_id, name in friend_manager.friend_dict.items():
            friend_list.append({
                "user_id": user_id,
                "user_name": name,
                "user_displayname": "",
                "user_remark": ""
            })
        return friend_list

    @impl.action("send_message")
    async def send_message(
        detail_type: str,
        user_id: str = "",
        group_id: str = "",
        message: list[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        try:
            bot = _get_bot(impl)
            api_base = bot.extra.get("server_url", "")
            if not api_base:
                raise ValueError("Missing server_url in bot configuration")
                
            api_key = bot.extra.get("api_key", "")
            if not api_key:
                raise ValueError("Missing api_key in bot configuration")
                
            message_id = "0"  # 初始化message_id变量

            headers = {
                'x-api-key': api_key,
                'accept': 'application/json; charset=utf-8'
            }

            if message and isinstance(message, list) and len(message) > 0:
                # 处理多个消息段
                text_segments = []
                file_segments = []
                reply_segments = []

                for segment in message:
                    msg_type = segment.get("type")
                    if not msg_type:
                        logger.warning("消息段缺少类型信息，已跳过")
                        continue
                        
                    msg_data = segment.get("data", {})

                    if msg_type in ["image", "voice", "audio", "video", "file"]:
                        # 处理文件类型的消息段
                        file_id = msg_data.get("file_id")
                        if not file_id:
                            raise ValueError(f"Missing 'file_id' for message type '{msg_type}'")
                        file_segments.append({"type": msg_type, "file_id": file_id})
                    elif msg_type == "text":
                        text_segments.append(msg_data.get("text", ""))
                    elif msg_type == "mention":
                        # 处理@消息段
                        mention_user_id = msg_data.get("user_id")
                        if mention_user_id:
                            text_segments.append(f"@{mention_user_id} ")
                    elif msg_type == "reply":
                        # 处理回复类型的消息段
                        message_id = msg_data.get("message_id")
                        if not message_id:
                            raise ValueError("Missing 'message_id' for reply message type")
                        reply_segments.append({
                            "message_id": message_id,
                            "user_id": msg_data.get("user_id", "")
                        })
                    else:
                        # 对于不支持的类型，添加提示文本
                        logger.warning(f"不支持的消息类型: {msg_type}")
                        text_segments.append(f"[Unsupported message type: {msg_type}]")

                # 发送reply消息段
                for reply_segment in reply_segments:
                    try:
                        endpoint = f'{api_base}/api/bot/reply/{reply_segment["message_id"]}'
                        payload = {"user_id": reply_segment["user_id"]} if reply_segment["user_id"] else {}
                        headers['Content-Type'] = 'application/json'
                        async with aiohttp.ClientSession() as client:
                            async with client.post(endpoint, json=payload, headers=headers, proxy=SEND_PROXY if PROXY_ENABLED else None) as response:
                                if response.status >= 400:
                                    error_text = await response.text()
                                    logger.error(f"发送回复消息失败: HTTP {response.status}, {error_text}")
                                    raise ValueError(f"Failed to send reply message: HTTP {response.status}, {error_text}")
                    except aiohttp.ClientError as e:
                        logger.error(f"发送回复消息时网络错误: {e}")
                        raise ValueError(f"Network error while sending reply message: {e}")
                    except Exception as e:
                        logger.error(f"发送回复消息时发生错误: {e}")
                        raise ValueError(f"Error while sending reply message: {e}")

                # 发送file消息段
                for file_segment in file_segments:
                    try:
                        if detail_type == "private":
                            if not user_id: raise ValueError("Missing 'user_id' for private message")
                            endpoint = f'{api_base}/api/bot/send_to_user/{user_id}'
                        elif detail_type == "group":
                            if not group_id: raise ValueError("Missing 'group_id' for group message")
                            endpoint = f'{api_base}/api/bot/send_to_group/{group_id}'
                        else:
                            raise ValueError(f"Unsupported detail_type: {detail_type}")
                            
                        payload = {"path": file_segment["file_id"]}
                        headers['Content-Type'] = 'vocechat/file'
                        async with aiohttp.ClientSession() as client:
                            async with client.post(endpoint, json=payload, headers=headers, proxy=SEND_PROXY if PROXY_ENABLED else None) as response:
                                if response.status >= 400:
                                    error_text = await response.text()
                                    logger.error(f"发送文件消息失败: HTTP {response.status}, {error_text}")
                                    raise ValueError(f"Failed to send file message: HTTP {response.status}, {error_text}")
                    except aiohttp.ClientError as e:
                        logger.error(f"发送文件消息时网络错误: {e}")
                        raise ValueError(f"Network error while sending file message: {e}")
                    except Exception as e:
                        logger.error(f"发送文件消息时发生错误: {e}")
                        raise ValueError(f"Error while sending file message: {e}")

                # 发送text消息段
                if text_segments:
                    try:
                        payload = "".join(text_segments)
                        headers['Content-Type'] = 'text/plain'
                        if detail_type == "private":
                            if not user_id: raise ValueError("Missing 'user_id' for private message")
                            endpoint = f'{api_base}/api/bot/send_to_user/{user_id}'
                        elif detail_type == "group":
                            if not group_id: raise ValueError("Missing 'group_id' for group message")
                            endpoint = f'{api_base}/api/bot/send_to_group/{group_id}'
                        else:
                            raise ValueError(f"Unsupported detail_type: {detail_type}")

                        async with aiohttp.ClientSession() as client:
                            async with client.post(endpoint, data=str(payload).encode('utf-8'), headers=headers, proxy=SEND_PROXY if PROXY_ENABLED else None) as response:
                                if response.status >= 400:
                                    error_text = await response.text()
                                    logger.error(f"发送文本消息失败: HTTP {response.status}, {error_text}")
                                    raise ValueError(f"Failed to send text message: HTTP {response.status}, {error_text}")
                                    
                                response_data = await response.text()
                                try:
                                    parsed_response = json.loads(response_data)
                                    # Vocechat send API might return message ID directly or in JSON
                                    # Adjust based on actual Vocechat API response. Assume it might be a simple int ID.
                                    if isinstance(parsed_response, int):
                                        message_id = str(parsed_response)
                                    elif isinstance(parsed_response, dict) and 'message_id' in parsed_response:
                                        message_id = str(parsed_response['message_id'])
                                    else:
                                        # Fallback if response is unexpected JSON or plain text
                                        message_id = response_data
                                        logger.warning(f"消息ID格式异常: {response_data}")
                                except json.JSONDecodeError:
                                    # If response is not JSON, use the raw text as message_id (might be the ID directly)
                                    message_id = response_data
                    except aiohttp.ClientError as e:
                        logger.error(f"发送文本消息时网络错误: {e}")
                        raise ValueError(f"Network error while sending text message: {e}")
                    except Exception as e:
                        logger.error(f"发送文本消息时发生错误: {e}")
                        raise ValueError(f"Error while sending text message: {e}")

            return {
                "message_id": message_id,
                "time": time.time()
            }
        except Exception as e:
            logger.error(f"发送消息时发生未处理的异常: {e}")
            # 使用OneBotImplError抛出异常，让impl.py中的handle_action捕获并返回FailedActionResponse
            from pylibob.exception import OneBotImplError
            from pylibob.status import INTERNAL_HANDLER_ERROR
            raise OneBotImplError(
                retcode=INTERNAL_HANDLER_ERROR,
                message=f"Error sending message: {e}",
                data=None
            )

    @impl.action("upload_file")
    async def upload_file(
        type: str,
        name: str,
        url: str = "",
        headers: dict[str, str] = None,
        path: str = "",
        data: str = "", # OneBot spec uses 'bytes' type, which is base64 string in JSON
        sha256: str = "", # Not used in Vocechat API examples, but part of OneBot spec
    ) -> dict[str, Any]:
        try:
            bot = _get_bot(impl)
            file_data: bytes | None = None
            content_type: str | None = None
            filename = name # Use provided name first

            # Guess content type early if possible
            if filename:
                content_type, _ = mimetypes.guess_type(filename)
            if content_type is None:
                content_type = "application/octet-stream" # Default

            async with aiohttp.ClientSession() as session:
                try:
                    if type == "url":
                        if not url:
                            raise ValueError("Missing 'url' parameter for type 'url'")
                        try:
                            async with session.get(url, headers=headers or {}) as resp:
                                if resp.status >= 400:
                                    error_text = await resp.text()
                                    logger.error(f"下载URL文件失败: HTTP {resp.status}, {error_text}")
                                    raise ValueError(f"Failed to download file from URL: HTTP {resp.status}")
                                    
                                file_data = await resp.read()
                                # Update content_type from response header if available
                                content_type = resp.headers.get("Content-Type", content_type)
                                # Determine filename from URL if not provided
                                if not filename:
                                    parsed_url = urlparse(url)
                                    filename = os.path.basename(parsed_url.path) or "downloaded_file"
                                    # TODO: Check Content-Disposition header for filename
                        except aiohttp.ClientError as e:
                            logger.error(f"下载URL文件时网络错误: {e}")
                            raise ValueError(f"Network error while downloading from URL: {e}")

                    elif type == "path":
                        if not path:
                            raise ValueError("Missing 'path' parameter for type 'path'")
                        try:
                            async with aiofiles.open(path, "rb") as f:
                                file_data = await f.read()
                            # Determine filename from path if not provided
                            if not filename:
                                filename = os.path.basename(path)
                        except FileNotFoundError:
                            logger.error(f"文件不存在: {path}")
                            raise ValueError(f"File not found: {path}")
                        except PermissionError:
                            logger.error(f"无权限读取文件: {path}")
                            raise ValueError(f"Permission denied when reading file: {path}")
                        except Exception as e:
                            logger.error(f"读取文件时发生错误: {e}")
                            raise ValueError(f"Error reading file: {e}")

                    elif type == "data":
                        if not data:
                            raise ValueError("Missing 'data' parameter for type 'data'")
                        try:
                            file_data = base64.b64decode(data)
                        except Exception as e:
                            logger.error(f"解码base64数据失败: {e}")
                            raise ValueError(f"Failed to decode base64 data: {e}")
                        # Determine filename if not provided (using extension from guessed content type)
                        if not filename:
                            ext = mimetypes.guess_extension(content_type) or ".bin"
                            filename = f"uploaded_file{ext}"

                    else:
                        logger.error(f"不支持的上传类型: {type}")
                        raise ValueError(f"Unsupported upload type: {type}")

                    # Final checks before uploading
                    if file_data is None:
                        raise ValueError("Could not retrieve file data")
                    if not filename:
                        raise ValueError("Could not determine filename")
                    # Ensure content_type has a value
                    if content_type is None:
                        content_type = "application/octet-stream"

                    try:
                        # Step 1: Prepare file upload with Vocechat API (get temporary file_id string)
                        temp_vocechat_file_id = await _vocechat_prepare_file(bot, session, filename, content_type)

                        # Step 2: Upload file data with Vocechat API (get JSON response with 'path')
                        upload_response = await _vocechat_upload_file(bot, session, temp_vocechat_file_id, file_data, filename, content_type)

                        # Extract 'path' from upload response. This 'path' acts as the persistent file_id for sending messages.
                        vocechat_path = upload_response.get("path")
                        if not vocechat_path:
                            logger.error(f"上传响应中缺少'path'字段: {upload_response}")
                            raise ValueError(f"Could not extract 'path' from Vocechat upload response: {upload_response}")

                        # Return the 'path' as the 'file_id' for OneBot send_message action
                        return {"file_id": vocechat_path}
                    except ValueError as e:
                        # 这里捕获的是_vocechat_prepare_file和_vocechat_upload_file中抛出的异常
                        logger.error(f"文件上传过程中发生错误: {e}")
                        raise
                except Exception as e:
                    logger.error(f"处理文件上传时发生错误: {e}")
                    raise ValueError(f"Error during file upload processing: {e}")
        except Exception as e:
            logger.error(f"文件上传时发生未处理的异常: {e}")
            # 使用OneBotImplError抛出异常，让impl.py中的handle_action捕获并返回FailedActionResponse
            from pylibob.exception import OneBotImplError
            from pylibob.status import INTERNAL_HANDLER_ERROR
            raise OneBotImplError(
                retcode=INTERNAL_HANDLER_ERROR,
                message=f"Error uploading file: {e}",
                data=None
            )

    @impl.action("upload_file_fragmented")
    async def upload_file_fragmented(**kwargs: Any):
        # Not implemented as OneBot spec doesn't match Vocechat API examples
        # Vocechat API seems to use prepare + single upload call
        raise NotImplementedError("Fragmented file upload is not currently supported by this implementation.")

    @impl.action("get_file")
    async def get_file(file_id: str, type: str, **kwargs: Any):
        # Not implemented - requires Vocechat API endpoint to get file info/data by ID
        raise NotImplementedError("Get file is not currently supported by this implementation.")

    @impl.action("get_file_fragmented")
    async def get_file_fragmented(**kwargs: Any):
        # Not implemented - requires Vocechat API endpoint for chunked download
        raise NotImplementedError("Fragmented file download is not currently supported by this implementation.")


    @impl.action("get_self_info")
    async def get_self_info() -> dict[str, Any]:
        try:
            bot = _get_bot(impl)
            api_base = bot.extra.get("server_url", "")
            if not api_base:
                raise ValueError("Missing server_url in bot configuration")
                
            api_key = bot.extra.get("api_key", "")
            if not api_key:
                raise ValueError("Missing api_key in bot configuration")

            endpoint = f'{api_base}/api/bot/user/{"{uid}"}?uid={bot.user_id}'
            headers = {
                'x-api-key': api_key,
                'accept': 'application/json; charset=utf-8'
            }

            async with aiohttp.ClientSession() as client:
                try:
                    async with client.get(endpoint, headers=headers) as response:
                        if response.status >= 400:
                            error_text = await response.text()
                            logger.error(f"获取自身信息失败: HTTP {response.status}, {error_text}")
                            raise ValueError(f"Failed to get self info: HTTP {response.status}, {error_text}")
                        
                        response_data = await response.json()
                except aiohttp.ClientError as e:
                    logger.error(f"获取自身信息时网络错误: {e}")
                    raise ValueError(f"Network error while getting self info: {e}")
                except json.JSONDecodeError as e:
                    logger.error(f"解析自身信息响应时JSON解析错误: {e}")
                    raise ValueError(f"JSON decode error while parsing self info response: {e}")

            return {
                "user_id": bot.user_id,
                "user_name": response_data.get("name", ""),
                "user_displayname": response_data.get("name", "")
            }
        except Exception as e:
            logger.error(f"获取自身信息时发生未处理的异常: {e}")
            # 使用OneBotImplError抛出异常，让impl.py中的handle_action捕获并返回FailedActionResponse
            from pylibob.exception import OneBotImplError
            from pylibob.status import INTERNAL_HANDLER_ERROR
            raise OneBotImplError(
                retcode=INTERNAL_HANDLER_ERROR,
                message=f"Error getting self info: {e}",
                data=None
            )

    @impl.action("get_user_info")
    async def get_user_info(user_id: str) -> dict[str, Any]:
        try:
            bot = _get_bot(impl)
            api_base = bot.extra.get("server_url", "")
            if not api_base:
                raise ValueError("Missing server_url in bot configuration")
                
            api_key = bot.extra.get("api_key", "")
            if not api_key:
                raise ValueError("Missing api_key in bot configuration")

            endpoint = f'{api_base}/api/bot/user/{"{uid}"}?uid={user_id}'
            headers = {
                'x-api-key': api_key,
                'accept': 'application/json; charset=utf-8'
            }

            async with aiohttp.ClientSession() as client:
                try:
                    async with client.get(endpoint, headers=headers) as response:
                        if response.status >= 400:
                            error_text = await response.text()
                            logger.error(f"获取用户信息失败: HTTP {response.status}, {error_text}")
                            raise ValueError(f"Failed to get user info: HTTP {response.status}, {error_text}")
                        
                        response_data = await response.json()
                except aiohttp.ClientError as e:
                    logger.error(f"获取用户信息时网络错误: {e}")
                    raise ValueError(f"Network error while getting user info: {e}")
                except json.JSONDecodeError as e:
                    logger.error(f"解析用户信息响应时JSON解析错误: {e}")
                    raise ValueError(f"JSON decode error while parsing user info response: {e}")

            return {
                    "user_id": user_id,
                    "user_name": response_data.get("name", ""),
                    "user_displayname": response_data.get("name", ""),
                    "user_avatar": f"https://vocechat.xf-yun.cn/api/resource/avatar?uid={user_id}",
                    "user_remark": ""
            }
        except Exception as e:
            logger.error(f"获取用户信息时发生未处理的异常: {e}")
            # 使用OneBotImplError抛出异常，让impl.py中的handle_action捕获并返回FailedActionResponse
            from pylibob.exception import OneBotImplError
            from pylibob.status import INTERNAL_HANDLER_ERROR
            raise OneBotImplError(
                retcode=INTERNAL_HANDLER_ERROR,
                message=f"Error getting user info: {e}",
                data=None
            )

    # @impl.action("get_group_info")
    async def get_group_info(group_id: str) -> dict[str, Any]:
        try:
            bot = _get_bot(impl)
            api_base = bot.extra.get("server_url", "")
            if not api_base:
                raise ValueError("Missing server_url in bot configuration")
                
            api_key = bot.extra.get("api_key", "")
            if not api_key:
                raise ValueError("Missing api_key in bot configuration")

            endpoint = f'{api_base}/api/bot/group/{'{gid}'}?gid={group_id}'
            headers = {
                'x-api-key': api_key,
                'accept': 'application/json; charset=utf-8'
            }

            async with aiohttp.ClientSession() as client:
                try:
                    async with client.get(endpoint, headers=headers) as response:
                        if response.status >= 400:
                            error_text = await response.text()
                            logger.error(f"获取群组信息失败: HTTP {response.status}, {error_text}")
                            raise ValueError(f"Failed to get group info: HTTP {response.status}, {error_text}")
                        
                        response_data = await response.json()
                except aiohttp.ClientError as e:
                    logger.error(f"获取群组信息时网络错误: {e}")
                    raise ValueError(f"Network error while getting group info: {e}")
                except json.JSONDecodeError as e:
                    logger.error(f"解析群组信息响应时JSON解析错误: {e}")
                    raise ValueError(f"JSON decode error while parsing group info response: {e}")

            return {
                "group_id": str(response_data.get("gid", "")),
                "group_name": response_data.get("name", ""),
                "group_remark": response_data.get("description", ""),
                "member_count": len(response_data.get("members", [])),
                "max_member_count": 0,  # VoceChat API doesn't provide this info
                "owner_id": str(response_data.get("owner", ""))
            }
        except Exception as e:
            logger.error(f"获取群组信息时发生未处理的异常: {e}")
            # 使用OneBotImplError抛出异常，让impl.py中的handle_action捕获并返回FailedActionResponse
            from pylibob.exception import OneBotImplError
            from pylibob.status import INTERNAL_HANDLER_ERROR
            raise OneBotImplError(
                retcode=INTERNAL_HANDLER_ERROR,
                message=f"Error getting group info: {e}",
                data=None
            )


    @impl.action("get_group_list")
    async def get_group_list() -> dict[str, Any]:
        try:
            bot = _get_bot(impl)
            api_base = bot.extra.get("server_url", "")
            if not api_base:
                raise ValueError("Missing server_url in bot configuration")
                
            api_key = bot.extra.get("api_key", "")
            if not api_key:
                raise ValueError("Missing api_key in bot configuration")
        
            endpoint = f'{api_base}/api/bot'
            headers = {
                'x-api-key': api_key,
                'accept': 'application/json; charset=utf-8'
            }
        
            async with aiohttp.ClientSession() as client:
                try:
                    async with client.get(endpoint, headers=headers) as response:
                        if response.status >= 400:
                            error_text = await response.text()
                            logger.error(f"获取群组列表失败: HTTP {response.status}, {error_text}")
                            raise ValueError(f"Failed to get group list: HTTP {response.status}, {error_text}")
                        
                        response_data = await response.json()
                except aiohttp.ClientError as e:
                    logger.error(f"获取群组列表时网络错误: {e}")
                    raise ValueError(f"Network error while getting group list: {e}")
                except json.JSONDecodeError as e:
                    logger.error(f"解析群组列表响应时JSON解析错误: {e}")
                    raise ValueError(f"JSON decode error while parsing group list response: {e}")
        
            groups = []
            try:
                for group in response_data:
                    groups.append({
                        "group_id": str(group.get("gid", "")),
                        "group_name": group.get("name", "")
                    })
            except Exception as e:
                logger.error(f"处理群组数据时发生错误: {e}")
                raise ValueError(f"Error processing group data: {e}")
        
            return groups
        except Exception as e:
            logger.error(f"获取群组列表时发生未处理的异常: {e}")
            # 使用OneBotImplError抛出异常，让impl.py中的handle_action捕获并返回FailedActionResponse
            from pylibob.exception import OneBotImplError
            from pylibob.status import INTERNAL_HANDLER_ERROR
            raise OneBotImplError(
                retcode=INTERNAL_HANDLER_ERROR,
                message=f"Error getting group list: {e}",
                data=None
            )