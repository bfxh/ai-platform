#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一日志配置中心

用法:
    from logging_config import setup_logger
    
    logger = setup_logger("my_tool")
    logger.info("This is a log message")
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# 日志目录
LOG_DIR = Path("/python/Logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 日志格式
DETAILED_FORMAT = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

SIMPLE_FORMAT = logging.Formatter(
    '%(levelname)s: %(message)s'
)

# 日志级别颜色 (用于控制台)
class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
        'RESET': '\033[0m'      # 重置
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        record.levelname = f"{log_color}{record.levelname}{reset}"
        return super().format(record)

def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True,
    detailed: bool = True
) -> logging.Logger:
    """
    设置统一日志
    
    Args:
        name: 日志器名称
        level: 日志级别
        log_to_file: 是否写入文件
        log_to_console: 是否输出到控制台
        detailed: 是否使用详细格式
    
    Returns:
        配置好的日志器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 文件处理器
    if log_to_file:
        log_file = LOG_DIR / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(level)
        fh.setFormatter(DETAILED_FORMAT)
        logger.addHandler(fh)
    
    # 控制台处理器
    if log_to_console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        
        # Windows不支持颜色，使用简单格式
        if sys.platform == 'win32':
            ch.setFormatter(SIMPLE_FORMAT)
        else:
            ch.setFormatter(ColoredFormatter('%(levelname)s: %(message)s'))
        
        logger.addHandler(ch)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """获取已配置的日志器"""
    return logging.getLogger(name)

class LoggerMixin:
    """日志混入类"""
    
    def __init__(self):
        self._logger = None
    
    @property
    def logger(self) -> logging.Logger:
        if self._logger is None:
            self._logger = setup_logger(self.__class__.__name__)
        return self._logger

# 使用示例
if __name__ == "__main__":
    # 测试日志
    logger = setup_logger("test")
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    print(f"\n✅ 日志已保存到: {LOG_DIR}")
