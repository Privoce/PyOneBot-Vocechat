import os
import sys
from datetime import datetime
from loguru import logger

class Logger:
    def __init__(self, log_config=None):
        # 默认配置
        self.log_config = log_config or {
            'enabled': True,
            'level': 'INFO'
        }
        
        # 创建日志目录
        self.log_path = os.path.join('', 'logs')
        if not os.path.exists(self.log_path):
            os.makedirs(self.log_path)
        
        # 清除默认的处理器
        logger.remove()
        
        # 添加控制台输出
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | {level} | <level>{message}</level>",
            level=self.log_config.get('level', "INFO")
        )
        
        # 添加默认的文件日志处理器
        self._add_default_file_handler()
        
        # 添加logger实例缓存
        self.logger_instances = {}

    def _add_default_file_handler(self):
        """添加默认的文件日志处理器"""
        if self.log_config.get('enabled', True):
            # 生成日志文件路径 (按天分类)
            today = datetime.now().strftime('%Y-%m-%d')
            daily_log_path = os.path.join(self.log_path, today)
            
            # 创建当天的日志目录
            if not os.path.exists(daily_log_path):
                os.makedirs(daily_log_path)
                
            # 完整的日志文件路径
            log_file = os.path.join(daily_log_path, "vocechat_bot.log")
            
            # 添加主文件日志处理器
            logger.add(
                log_file,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
                rotation="00:00",
                retention="30 days",
                encoding="utf-8",
                enqueue=True,
                level=self.log_config.get('level', "INFO")
            )

    def get_logger(self, filename=None):
        """
        获取logger实例
        :param filename: 日志文件名 (可选，用于标识日志来源)
        :return: logger实例
        """
        # 如果没有提供文件名，返回默认logger
        if not filename:
            return logger
            
        # 如果已经存在该文件名的logger实例，直接返回
        if filename in self.logger_instances:
            return self.logger_instances[filename]
            
        try:
            # 创建新的 logger 实例，带有模块标识
            new_logger = logger.bind(module=filename)
            
            # 缓存logger实例
            self.logger_instances[filename] = new_logger
            return new_logger
            
        except Exception as e:
            print(f"创建日志器时出错: {str(e)}")
            # 出错时返回默认logger
            return logger