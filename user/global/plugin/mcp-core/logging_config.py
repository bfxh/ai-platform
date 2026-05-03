#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - 增强日志系统

功能:
- 结构化日志（JSON 格式）
- 日志轮转
- 日志聚合
- 日志过滤
- 性能日志
"""

import json
import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


class LogFilter(logging.Filter):
    """日志过滤器"""

    def __init__(self, level: int = logging.DEBUG, exclude_modules: list = None):
        super().__init__()
        self.level = level
        self.exclude_modules = exclude_modules or []

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno < self.level:
            return False

        for module in self.exclude_modules:
            if record.name.startswith(module):
                return False

        return True


class LogManager:
    """日志管理器"""

    def __init__(
        self,
        log_dir: str = "logs",
        log_level: int = logging.INFO,
        max_bytes: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 5,
        enable_json: bool = True,
        enable_console: bool = True,
    ):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_level = log_level
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.enable_json = enable_json
        self.enable_console = enable_console
        self.loggers: Dict[str, logging.Logger] = {}

        self._setup_root_logger()

    def _setup_root_logger(self) -> None:
        """设置根日志记录器"""
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)

        root_logger.handlers.clear()

        if self.enable_console:
            self._add_console_handler(root_logger)

        self._add_file_handler(root_logger, "mcp_core.log")

        if self.enable_json:
            self._add_json_handler(root_logger, "mcp_core.json.log")

    def _add_console_handler(self, logger: logging.Logger) -> None:
        """添加控制台处理器"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)

        formatter = ColoredFormatter(
            "%(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)d)",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    def _add_file_handler(self, logger: logging.Logger, filename: str) -> None:
        """添加文件处理器（带轮转）"""
        file_path = self.log_dir / filename
        file_handler = logging.handlers.RotatingFileHandler(
            file_path, maxBytes=self.max_bytes, backupCount=self.backup_count, encoding="utf-8"
        )
        file_handler.setLevel(self.log_level)

        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)d)",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

    def _add_json_handler(self, logger: logging.Logger, filename: str) -> None:
        """添加 JSON 格式处理器"""
        file_path = self.log_dir / filename
        json_handler = logging.handlers.RotatingFileHandler(
            file_path, maxBytes=self.max_bytes, backupCount=self.backup_count, encoding="utf-8"
        )
        json_handler.setLevel(self.log_level)

        formatter = StructuredFormatter()
        json_handler.setFormatter(formatter)

        logger.addHandler(json_handler)

    def get_logger(self, name: str) -> logging.Logger:
        """获取日志记录器"""
        if name not in self.loggers:
            logger = logging.getLogger(name)
            logger.setLevel(self.log_level)
            self.loggers[name] = logger
        return self.loggers[name]

    def log_performance(
        self, logger: logging.Logger, operation: str, duration: float, success: bool = True
    ) -> None:
        """记录性能日志"""
        extra_data = {"operation": operation, "duration_ms": duration * 1000, "success": success}
        logger.info(f"性能指标: {operation}", extra={"extra_data": extra_data})

    def log_audit(self, logger: logging.Logger, action: str, user: str = None, details: Dict = None) -> None:
        """记录审计日志"""
        extra_data = {"action": action, "user": user, "details": details or {}}
        logger.info(f"审计日志: {action}", extra={"extra_data": extra_data})

    def log_error_with_context(
        self,
        logger: logging.Logger,
        error: Exception,
        context: Dict[str, Any],
        level: int = logging.ERROR,
    ) -> None:
        """记录带上下文的错误日志"""
        extra_data = {"error_type": type(error).__name__, "error_message": str(error), "context": context}
        logger.log(level, f"错误: {error}", extra={"extra_data": extra_data}, exc_info=True)


_log_manager_instance: Optional[LogManager] = None


def get_log_manager(**kwargs) -> LogManager:
    """获取日志管理器实例"""
    global _log_manager_instance
    if _log_manager_instance is None:
        _log_manager_instance = LogManager(**kwargs)
    return _log_manager_instance


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器"""
    return get_log_manager().get_logger(name)


def setup_logging(
    log_dir: str = "logs",
    log_level: int = logging.INFO,
    enable_json: bool = True,
    enable_console: bool = True,
) -> LogManager:
    """设置日志系统"""
    return get_log_manager(
        log_dir=log_dir, log_level=log_level, enable_json=enable_json, enable_console=enable_console
    )
