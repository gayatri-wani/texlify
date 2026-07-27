"""Production logging configuration."""
import logging
import logging.handlers
import os
from datetime import datetime


def setup_logging():
    """Set up structured logging for production."""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    log_format = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Console handler
    console = logging.StreamHandler()
    console.setFormatter(log_format)
    console.setLevel(logging.INFO)
    root_logger.addHandler(console)

    # File handler — rotating daily, keep 30 days
    today      = datetime.now().strftime("%Y-%m-%d")
    log_file   = os.path.join(log_dir, f"texlify_{today}.log")
    file_handler = logging.handlers.TimedRotatingFileHandler(
        log_file, when="midnight", interval=1,
        backupCount=30, encoding="utf-8"
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)

    # Security logger — separate file for security events
    security_logger  = logging.getLogger("texlify.security")
    sec_file         = os.path.join(log_dir, "security.log")
    sec_handler      = logging.handlers.TimedRotatingFileHandler(
        sec_file, when="midnight", interval=1,
        backupCount=90, encoding="utf-8"
    )
    sec_handler.setFormatter(log_format)
    security_logger.addHandler(sec_handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.info("Logging initialized")