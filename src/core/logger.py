import logging
import sys

def setup_logger(name: str, log_file: str = None) -> logging.Logger:
    """
    Configure structured logging for the application.

    Args:
        name: Logger name (e.g., 'cadet.nodes', 'cadet.graph')
        log_file: Optional file path for persistent logging

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logger('cadet.nodes')
        >>> logger.info('Processing started')
        >>> logger.error('An error occurred', exc_info=True)
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers if logger already exists
    if logger.handlers:
        return logger

    # Console handler with simple formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s [%(name)s] %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Suppress noisy logs from external libraries
    logging.getLogger("langgraph").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)

    # File handler for persistent logs (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger
