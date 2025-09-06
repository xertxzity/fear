#!/usr/bin/env python3
"""
Logger utility for Fortnite Season 7 Emulator
Provides consistent logging across all components
"""

import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime

def setup_logger(name: str, log_file: str = None, level: str = "INFO") -> logging.Logger:
    """
    Setup logger with file and console handlers
    
    Args:
        name: Logger name
        log_file: Log file path (optional)
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file is None:
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
    
    try:
        # Rotating file handler (10MB max, 5 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
    except Exception as e:
        logger.warning(f"Could not setup file logging: {e}")
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get existing logger or create new one
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

class LogCapture:
    """
    Context manager to capture log messages
    """
    
    def __init__(self, logger_name: str, level: str = "INFO"):
        self.logger_name = logger_name
        self.level = getattr(logging, level.upper())
        self.messages = []
        self.handler = None
    
    def __enter__(self):
        # Create custom handler to capture messages
        self.handler = logging.Handler()
        self.handler.setLevel(self.level)
        self.handler.emit = self._capture_message
        
        # Add handler to logger
        logger = logging.getLogger(self.logger_name)
        logger.addHandler(self.handler)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Remove handler
        if self.handler:
            logger = logging.getLogger(self.logger_name)
            logger.removeHandler(self.handler)
    
    def _capture_message(self, record):
        """Capture log message"""
        self.messages.append(record.getMessage())
    
    def get_messages(self) -> list:
        """Get captured messages"""
        return self.messages.copy()

class ColoredFormatter(logging.Formatter):
    """
    Colored console formatter for better readability
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Add color to level name
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
        
        return super().format(record)

def setup_colored_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Setup logger with colored console output
    
    Args:
        name: Logger name
        level: Logging level
        
    Returns:
        Configured logger with colored output
    """
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Colored console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    colored_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(colored_formatter)
    logger.addHandler(console_handler)
    
    return logger

def log_function_call(func):
    """
    Decorator to log function calls
    
    Usage:
        @log_function_call
        def my_function(arg1, arg2):
            pass
    """
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed with error: {e}")
            raise
    
    return wrapper

def log_performance(func):
    """
    Decorator to log function performance
    
    Usage:
        @log_performance
        def slow_function():
            pass
    """
    import time
    
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"{func.__name__} completed in {duration:.3f} seconds")
            return result
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            logger.error(f"{func.__name__} failed after {duration:.3f} seconds: {e}")
            raise
    
    return wrapper