"""
Centralized logging configuration for muto_link.
"""

import logging
import os
import sys
from typing import Optional, Union


def setup_logger(
    name: str, 
    level: Union[str, int, None] = None,
    log_file: Optional[str] = None,
    format_type: str = "standard"
) -> logging.Logger:
    """
    Setup a standardized logger for muto_link modules.
    
    Args:
        name: Logger name (typically __name__)
        level: Log level (DEBUG, INFO, WARN, ERROR) or None for environment default
        log_file: Optional file path for log output
        format_type: Format type ("standard" or "json")
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if logger already configured
    if logger.handlers:
        return logger
    
    # Determine log level
    if level is None:
        level_str = os.getenv('MUTO_LOG_LEVEL', 'INFO').upper()
        log_level = getattr(logging, level_str, logging.INFO)
    elif isinstance(level, str):
        log_level = getattr(logging, level.upper(), logging.INFO)
    else:
        log_level = level
    
    logger.setLevel(log_level)
    
    # Create formatter
    if format_type == "json":
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Optional file handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger to avoid duplicate messages
    logger.propagate = False
    
    return logger


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        import json
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ('name', 'msg', 'args', 'levelname', 'levelno', 
                          'pathname', 'filename', 'module', 'lineno', 'funcName',
                          'created', 'msecs', 'relativeCreated', 'thread',
                          'threadName', 'processName', 'process', 'exc_info',
                          'exc_text', 'stack_info', 'getMessage'):
                log_data[key] = value
                
        return json.dumps(log_data)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with standard muto_link configuration.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return setup_logger(name)


# Module-level convenience functions
def set_global_log_level(level: Union[str, int]) -> None:
    """Set log level for all muto_link loggers."""
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    
    # Update all existing muto_link loggers
    for logger_name in logging.Logger.manager.loggerDict:
        if logger_name.startswith('muto_link'):
            logger = logging.getLogger(logger_name)
            logger.setLevel(level)
            for handler in logger.handlers:
                handler.setLevel(level)
