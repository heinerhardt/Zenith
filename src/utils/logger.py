"""
Logging utilities for Zenith PDF Chatbot
Provides centralized logging configuration
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from loguru import logger as loguru_logger

from ..core.config import get_logs_dir, config


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """
    Setup logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file name
    """
    # Create logs directory
    logs_dir = get_logs_dir()
    logs_dir.mkdir(exist_ok=True)
    
    # Configure loguru
    loguru_logger.remove()  # Remove default handler
    
    # Add console handler
    loguru_logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        colorize=True
    )
    
    # Add file handler
    if log_file:
        log_path = logs_dir / log_file
    else:
        log_path = logs_dir / "zenith.log"
    
    loguru_logger.add(
        str(log_path),
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="100 MB",
        retention="30 days",
        compression="zip"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    # Setup logging if not already done
    if not hasattr(get_logger, '_setup_done'):
        setup_logging(config.log_level)
        get_logger._setup_done = True
    
    # Create standard logger that bridges to loguru
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Create a handler that forwards to loguru
        class LoguruHandler(logging.Handler):
            def emit(self, record):
                # Get corresponding Loguru level if it exists
                try:
                    level = loguru_logger.level(record.levelname).name
                except ValueError:
                    level = record.levelno

                # Find caller from where logging method was called
                frame, depth = logging.currentframe(), 2
                while frame.f_code.co_filename == logging.__file__:
                    frame = frame.f_back
                    depth += 1

                loguru_logger.opt(depth=depth, exception=record.exc_info).log(
                    level, record.getMessage()
                )

        logger.addHandler(LoguruHandler())
        logger.setLevel(getattr(logging, config.log_level))
    
    return logger


def log_function_call(func_name: str, args: dict = None, kwargs: dict = None):
    """
    Log function calls for debugging
    
    Args:
        func_name: Function name
        args: Function arguments
        kwargs: Function keyword arguments
    """
    logger = get_logger(__name__)
    args_str = f"args={args}" if args else ""
    kwargs_str = f"kwargs={kwargs}" if kwargs else ""
    separator = ", " if args and kwargs else ""
    
    logger.debug(f"Calling {func_name}({args_str}{separator}{kwargs_str})")


def log_performance(func_name: str, duration: float, success: bool = True):
    """
    Log performance metrics
    
    Args:
        func_name: Function name
        duration: Execution duration in seconds
        success: Whether the function succeeded
    """
    logger = get_logger(__name__)
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"Performance: {func_name} - {status} - {duration:.3f}s")


def log_error(error: Exception, context: str = ""):
    """
    Log errors with context
    
    Args:
        error: Exception object
        context: Additional context information
    """
    logger = get_logger(__name__)
    context_str = f" | Context: {context}" if context else ""
    logger.error(f"Error: {type(error).__name__}: {str(error)}{context_str}")


def log_memory_usage():
    """Log current memory usage"""
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        logger = get_logger(__name__)
        logger.info(f"Memory usage: {memory_mb:.2f} MB")
        
    except ImportError:
        pass  # psutil not available


# Performance monitoring decorator
def monitor_performance(func):
    """
    Decorator to monitor function performance
    
    Args:
        func: Function to monitor
        
    Returns:
        Wrapped function
    """
    import time
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        success = True
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            success = False
            log_error(e, f"in {func.__name__}")
            raise
        finally:
            duration = time.time() - start_time
            log_performance(func.__name__, duration, success)
    
    return wrapper
