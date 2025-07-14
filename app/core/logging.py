import logging
import logging.config
import os

from .logging_config import LOGGING_CONFIG

def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    import os
    
    # Create logs directory if it doesn't exist
    os.makedirs("/app/logs", exist_ok=True)
    
    # Follow these conventions https://docs.python.org/3/library/logging.config.html
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # Set root level based on environment
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"app.{name}")
