"""Logging configuration for the news agent system."""

import logging
import sys
from datetime import datetime
from typing import Optional

def setup_logger(name: str = "news_agent", level: int = logging.INFO) -> logging.Logger:
    """Set up structured logging for the news agent system."""
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler with UTF-8 encoding
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    # Set encoding to UTF-8 to handle Unicode characters
    if hasattr(console_handler.stream, 'reconfigure'):
        console_handler.stream.reconfigure(encoding='utf-8')
    logger.addHandler(console_handler)
    
    # File handler with UTF-8 encoding
    file_handler = logging.FileHandler(f'logs/news_agent_{datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

def log_agent_execution(agent_name: str, input_data: dict, output_data: dict, execution_time: float):
    """Log agent execution details."""
    logger = logging.getLogger("agent_execution")
    
    logger.info(f"Agent: {agent_name}")
    logger.info(f"Input: {input_data}")
    logger.info(f"Output: {output_data}")
    logger.info(f"Execution time: {execution_time:.2f}s")

def log_error(error: Exception, context: str = ""):
    """Log errors with context."""
    logger = logging.getLogger("error")
    logger.error(f"Error in {context}: {str(error)}", exc_info=True)

