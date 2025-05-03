import logging
import sys, os
from pathlib import Path

# Global logger dictionary to ensure we returnt he same logger instance for each module
_loggers = {}


def get_logger(name=None, level=None):
    """
    Returns the logger with the specified name, creating it if necessary.
    Using this function ensures the same logger instance is returned for the same name.

    Args:
        name: The logger name (typically __name__ from the calling module)
        level: Optional level to set for this specific logger

    Returns:
        A configured logger instance
    """
    global _loggers

    # Default to the root logger if no name is provided
    if name is None:
        name = "mcplite"

    if name in _loggers:
        logger = _loggers[name]
        if level is not None:
            logger.setLevel(level)
        return logger

    # Create a new logger
    logger = logging.getLogger(name)

    # Set level if provided; otherwise inherit from parent
    if level is not None:
        logger.setLevel(level)

    # Store in cache
    _loggers[name] = logger

    return logger


def configure_logging(
    level=logging.INFO,
    log_file=None,
    trace_mode=False,
    console=True,
):
    """
    Configure the root logging settings for the entire application.
    Call this once at application startup.

    Args:
        level: The logging level (default: INFO)
        log_file: Optional file to log to (default: None)
        trace_mode: If True, set the logging level to DEBUG
        console: If True, log to console
    """
    # Create a log formatter with trace information if requested
    if trace_mode:
        log_format = "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d (%(funcName)s) - %(message)s"
    else:
        log_format = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"

    formatter = logging.Formatter(log_format)

    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove any existing handlers to avoid duplicate logs
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add console handler if requested
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Add file handler if requested
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Create the main application logger
    logger = get_logger("mcplite")
    logger.info(
        "Logging configured with level: %s, trace_mode: %s",
        logging.getLevelName(level),
        trace_mode,
    )

    return logger


def enable_trace_mode():
    """Enable detailed tracing across all loggers"""
    # Reconfigure with trace mode enabled
    configure_logging(level=logging.DEBUG, trace_mode=True)


def disable_trace_mode():
    """Disable detailed tracing"""
    # Reconfigure with trace mode disabled
    configure_logging(level=logging.INFO, trace_mode=False)
