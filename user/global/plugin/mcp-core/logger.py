#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - 日志系统

功能:
- 统一的日志管理
- 文件和控制台双输出
- 日志轮转
- 结构化日志支持

用法:
    from logger import get_logger
    logger = get_logger("mcp.skill.network_transfer")
    logger.info("技能启动")
    logger.error("执行失败", exc_info=True)
"""

import logging
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import threading


class JSONFormatter(logging.Formatter):
    """JSON格式日志"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # 添加额外字段
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """带颜色的控制台日志"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
        'RESET': '\033[0m'       # 重置
    }
    
    def format(self, record: logging.LogRecord) -> str:
        # 保存原始级别名称
        original_levelname = record.levelname
        
        # 添加颜色
        if sys.platform == 'win32':
            # Windows 需要启用 ANSI 支持
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        
        result = super().format(record)
        
        # 恢复原始级别名称
        record.levelname = original_levelname
        
        return result


class MCPLogger:
    """MCP日志管理器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.log_dir = Path("/python/MCP_Core/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.loggers: Dict[str, logging.Logger] = {}
        self.default_level = logging.INFO
        self.max_bytes = 10 * 1024 * 1024  # 10MB
        self.backup_count = 5
        
        self._initialized = True
    
    def get_logger(
        self,
        name: str,
        level: Optional[int] = None,
        json_format: bool = False,
        colored: bool = True
    ) -> logging.Logger:
        """获取日志记录器"""
        if name in self.loggers:
            return self.loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(level or self.default_level)
        
        # 避免重复添加处理器
        if logger.handlers:
            return logger
        
        # 文件处理器 - 按天轮转
        file_handler = TimedRotatingFileHandler(
            filename=self.log_dir / f"{name.replace('.', '_')}.log",
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        file_handler.setLevel(level or self.default_level)
        
        if json_format:
            file_formatter = JSONFormatter()
        else:
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level or self.default_level)
        
        if colored and sys.stdout.isatty():
            console_formatter = ColoredFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
        else:
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # 错误日志单独文件
        error_handler = RotatingFileHandler(
            filename=self.log_dir / f"{name.replace('.', '_')}_error.log",
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        logger.addHandler(error_handler)
        
        self.loggers[name] = logger
        return logger
    
    def set_level(self, level: int):
        """设置全局日志级别"""
        self.default_level = level
        for logger in self.loggers.values():
            logger.setLevel(level)
    
    def cleanup_old_logs(self, days: int = 30):
        """清理旧日志文件"""
        cutoff = datetime.now() - timedelta(days=days)
        
        for log_file in self.log_dir.glob("*.log*"):
            try:
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if mtime < cutoff:
                    log_file.unlink()
                    print(f"[Logger] 删除旧日志: {log_file.name}")
            except Exception as e:
                print(f"[Logger] 删除日志失败 {log_file}: {e}")


# 便捷函数
def get_logger(
    name: str = "mcp",
    level: Optional[int] = None,
    json_format: bool = False
) -> logging.Logger:
    """获取日志记录器"""
    return MCPLogger().get_logger(name, level, json_format)


def log_execution(logger: logging.Logger):
    """执行日志装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"开始执行: {func.__name__}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"执行完成: {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"执行失败: {func.__name__} - {e}", exc_info=True)
                raise
        return wrapper
    return decorator


if __name__ == '__main__':
    # 测试日志系统
    print("测试 MCP 日志系统")
    print("=" * 50)
    
    # 获取日志记录器
    logger = get_logger("test")
    
    # 测试各级别日志
    logger.debug("这是一条 DEBUG 日志")
    logger.info("这是一条 INFO 日志")
    logger.warning("这是一条 WARNING 日志")
    logger.error("这是一条 ERROR 日志")
    logger.critical("这是一条 CRITICAL 日志")
    
    # 测试异常日志
    try:
        1 / 0
    except Exception as e:
        logger.exception("捕获到异常")
    
    # 测试 JSON 格式
    json_logger = get_logger("test_json", json_format=True)
    json_logger.info("JSON 格式日志", extra={'extra_data': {'key': 'value'}})
    
    print("\n日志文件位置:")
    print(f"  {Path('/python/MCP_Core/logs').absolute()}")
