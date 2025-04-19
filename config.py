import os
from dotenv import load_dotenv
load_dotenv()

from pylibob import (
    HTTP,
    Bot,
    HTTPWebhook,
    WebSocket,
    WebSocketReverse,
)

# 配置启用的通信方式
CONNECTIONS = []
IMPL_NAME = "vocechat-onebot"
IMPL_VERSION = "0.1.0"
# HTTP 配置
if os.getenv('HTTP_ENABLED', 'false').lower() == 'true':
    CONNECTIONS.append(HTTP(
        host=os.getenv('HTTP_HOST', '0.0.0.0'),
        port=int(os.getenv('HTTP_PORT', '8080')),
        event_enabled=os.getenv('HTTP_EVENT_ENABLED', 'true').lower() == 'true',
        event_buffer_size=int(os.getenv('HTTP_EVENT_BUFFER_SIZE', '20')),
        access_token=os.getenv('HTTP_ACCESS_TOKEN', '')
    ))

# HTTP Webhook 配置
if os.getenv('HTTP_WEBHOOK_ENABLED', 'false').lower() == 'true':
    CONNECTIONS.append(HTTPWebhook(
        url=os.getenv('HTTP_WEBHOOK_URL', '')
    ))

# WebSocket 配置
if os.getenv('WEBSOCKET_ENABLED', 'false').lower() == 'true':
    CONNECTIONS.append(WebSocket(
        enable_heartbeat=os.getenv('WEBSOCKET_ENABLE_HEARTBEAT', 'true').lower() == 'true',
        heartbeat_interval=int(os.getenv('WEBSOCKET_HEARTBEAT_INTERVAL', '5000'))
    ))

# WebSocket Reverse 配置
if os.getenv('WEBSOCKET_REVERSE_ENABLED', 'true').lower() == 'true':
    CONNECTIONS.append(WebSocketReverse(
        url=os.getenv('WEBSOCKET_REVERSE_URL', 'ws://127.0.0.1:8080/onebot/v12/')
    ))

# WEBHOOK_HOST, WEBHOOK_PORT
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST', '0.0.0.0')
WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', '8000'))
BOT_SERVER_URL = os.getenv('BOT_SERVER_URL', 'http://127.0.0.1:3000')

# 配置 Vocechat 机器人信息
BOT_CONFIG = Bot(
    platform=os.getenv('BOT_PLATFORM', 'vocechat'),
    user_id=os.getenv('BOT_USER_ID', '2'),
    online=os.getenv('BOT_ONLINE', 'false').lower() == 'true',
    extra={
        "server_url": BOT_SERVER_URL,
        "api_key": os.getenv('BOT_API_KEY', '')
    }
)
SEND_PROXY = os.getenv('SEND_PROXY', 'http://127.0.0.1:7897')

# 日志配置
LOG_CONFIG = {
    'enabled': os.getenv('LOG_ENABLED', 'true').lower() == 'true',
    'level': os.getenv('LOG_LEVEL', 'INFO')
}