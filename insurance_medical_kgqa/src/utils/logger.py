# 日志配置：统一格式与输出
import logging
import sys
from typing import Optional, Any

_DEFAULT_FMT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def get_logger(
    name: str,
    level: int = logging.INFO,
    format_string: Optional[str] = None,
    stream: Optional[Any] = None,
) -> logging.Logger:
    """
    获取具名 logger，统一格式。
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)
    fmt = format_string or _DEFAULT_FMT
    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setFormatter(logging.Formatter(fmt))
    logger.addHandler(handler)
    return logger


def setup_root_logger(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
) -> None:
    """配置根 logger（可选），便于全项目统一输出。"""
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        h = logging.StreamHandler(sys.stderr)
        h.setFormatter(logging.Formatter(fmt))
        root.addHandler(h)
    if log_file:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(logging.Formatter(fmt))
        root.addHandler(fh)
