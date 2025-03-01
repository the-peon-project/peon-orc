import logging
import sys
import os

def configure_logging():
    # Clear any existing handlers to avoid duplicates
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set the log format and level
    log_format = '%(asctime)s %(thread)d [%(levelname)s] %(message)s'
    log_level = logging.DEBUG if os.environ.get('DEV_MODE', 'disabled') == 'enabled' else logging.INFO
    
    # Configure the root logger with a single stdout handler
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Verify configuration with a debug message
    logging.debug(f"Logging configured with level: {logging.getLevelName(log_level)}")