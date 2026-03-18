"""
三省六部制多AI Agent系统 - 日志系统
提供统一的日志记录功能
"""

import logging
from datetime import datetime
import os


class AgentLogger:
    """Agent系统日志记录器"""
    
    def __init__(self, log_dir="logs"):
        """初始化日志记录器"""
        os.makedirs(log_dir, exist_ok=True)
        self.logger = logging.getLogger("AgentSystem")
        self.logger.setLevel(logging.INFO)
        
        # 清除已有的handlers，避免重复添加
        self.logger.handlers.clear()
        
        # 文件处理器
        log_file = os.path.join(log_dir, f"execution_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 格式化器
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(stage)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log(self, stage: str, level: str, message: str):
        """记录日志"""
        if level == "INFO":
            self.logger.info(message, extra={'stage': stage})
        elif level == "WARN":
            self.logger.warning(message, extra={'stage': stage})
        elif level == "ERROR":
            self.logger.error(message, extra={'stage': stage})
        else:
            self.logger.info(message, extra={'stage': stage})
    
    @staticmethod
    def get_instance():
        """获取日志记录器单例"""
        if not hasattr(AgentLogger, '_instance'):
            AgentLogger._instance = AgentLogger()
        return AgentLogger._instance
