"""
Tests for the logging system.
"""

import logging
import tempfile
import os
import sys
from pathlib import Path

# Add src directory to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from muto_link.logging import setup_logger, get_logger, set_global_log_level


def test_basic_logger_creation():
    """Test basic logger creation and configuration."""
    logger = get_logger("test_module")
    
    assert logger is not None
    assert logger.name == "test_module"
    assert len(logger.handlers) > 0


def test_log_level_setting():
    """Test setting log levels."""
    logger = setup_logger("test_level", level="DEBUG")
    
    assert logger.level == logging.DEBUG
    assert all(h.level == logging.DEBUG for h in logger.handlers)


def test_file_logging():
    """Test logging to file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        log_file = f.name
    
    try:
        logger = setup_logger("test_file", log_file=log_file)
        logger.info("Test message")
        
        # Check file was created and contains log message
        with open(log_file, 'r') as f:
            content = f.read()
            assert "Test message" in content
            assert "test_file" in content
            
    finally:
        if os.path.exists(log_file):
            os.unlink(log_file)


def test_json_formatter():
    """Test JSON formatting."""
    logger = setup_logger("test_json", format_type="json")
    
    # Should not raise an exception
    logger.info("JSON test message")


def test_global_log_level():
    """Test global log level setting."""
    # Create multiple loggers with muto_link prefix
    logger1 = get_logger("muto_link.test_global1")
    logger2 = get_logger("muto_link.test_global2")
    
    # Set global level
    set_global_log_level("ERROR")
    
    # Both loggers should have ERROR level
    assert logger1.level == logging.ERROR
    assert logger2.level == logging.ERROR


def test_environment_variable():
    """Test environment variable configuration."""
    # Set environment variable
    os.environ['MUTO_LOG_LEVEL'] = 'WARN'
    
    try:
        logger = setup_logger("test_env")
        assert logger.level == logging.WARNING
    finally:
        # Clean up
        if 'MUTO_LOG_LEVEL' in os.environ:
            del os.environ['MUTO_LOG_LEVEL']
