from __future__ import annotations

# from typing_extensions import Annotated  # python<3.9
from typing import Annotated  # python>=3.9
from typing import Any
import asyncio
import aiohttp
import os
from core.logger import Logger

from pylibob import OneBotImpl, Event  # Keep necessary pylibob imports
from core.bot_actions import register_actions # Import the registration function
from config import IMPL_NAME, IMPL_VERSION, CONNECTIONS, BOT_CONFIG, BOT_SERVER_URL # Import config

# 检查并生成.env文件
if not os.path.exists('.env'):
    with open('.env', 'w', encoding='utf-8') as f:
        f.write("""# 通信方式配置
HTTP_ENABLED=false
HTTP_HOST=0.0.0.0
HTTP_PORT=8080
HTTP_EVENT_ENABLED=true
HTTP_EVENT_BUFFER_SIZE=20
HTTP_ACCESS_TOKEN=your_access_token

HTTP_WEBHOOK_ENABLED=false
HTTP_WEBHOOK_URL=http://your_webhook_url/

WEBSOCKET_ENABLED=false
WEBSOCKET_ENABLE_HEARTBEAT=true
WEBSOCKET_HEARTBEAT_INTERVAL=5000

WEBSOCKET_REVERSE_ENABLED=true
WEBSOCKET_REVERSE_URL=ws://127.0.0.1:8080/onebot/v12/

# 对外监听vocechat的Webhook服务器配置
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8000

# Vocechat机器人配置
BOT_USER_ID=12 # 机器人用户ID
BOT_SERVER_URL=https://example.com # vocechat服务器地址
BOT_API_KEY=your_api_key

SEND_PROXY=http://127.0.0.1:7897

# 日志配置
LOG_ENABLED=true
LOG_LEVEL=INFO
""")
    print("已生成.env配置文件，请修改配置后重新启动程序...")
    input("按回车键退出...")
    exit()

# 初始化Logger
from config import LOG_CONFIG
log = Logger(LOG_CONFIG)
logger = log.get_logger(filename="main")

# Initialize OneBotImpl using config
impl = OneBotImpl(
    IMPL_NAME,
    IMPL_VERSION,
    CONNECTIONS,
    BOT_CONFIG,
)

# Register the action handlers from the core module
register_actions(impl)


async def check_version():
    """检查服务器版本是否为0.4.2"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{BOT_SERVER_URL}/api/admin/system/version"
            async with session.get(url) as response:
                if response.status == 200:
                    version = await response.text()
                    if version != '0.4.2':
                        logger.warning(f"当前服务器版本为{version}，暂未经过测试，可能无法正常使用")
                    else:
                        logger.info("服务器版本兼容性检查通过 (0.4.2)")
                else:
                    logger.error(f"获取版本信息失败: {response.status}")
    except Exception as e:
        logger.error(f"版本检查异常: {e}")

if __name__ == "__main__":
    async def main():
        await check_version()
        for bot in impl.bots.values():
            bot.online = True
        impl.is_good = True
        await impl.update_status()

    # 使用 asyncio.run() 来运行异步任务
    asyncio.run(main())
    impl.run()