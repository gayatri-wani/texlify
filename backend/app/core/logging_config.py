import logging
import logging.handlers
import os
import json
from datetime import datetime


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level":     record.levelname,
            "logger":    record.name,
            "message":   record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_obj["user_id"] = record.user_id
        return json.dumps(log_obj, ensure_ascii=False)


class PlainFormatter(logging.Formatter):
    def __init__(self):
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


def setup_logging(log_format: str = "json"):
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    formatter = JsonFormatter() if log_format == "json" else PlainFormatter()

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console.setLevel(logging.INFO)
    root_logger.addHandler(console)

    today    = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"texlify_{today}.log")
    file_handler = logging.handlers.TimedRotatingFileHandler(
        log_file, when="midnight", interval=1,
        backupCount=30, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)

    security_logger = logging.getLogger("texlify.security")
    sec_file        = os.path.join(log_dir, "security.log")
    sec_handler     = logging.handlers.TimedRotatingFileHandler(
        sec_file, when="midnight", interval=1,
        backupCount=90, encoding="utf-8"
    )
    sec_handler.setFormatter(formatter)
    security_logger.addHandler(sec_handler)

    logging.getLogger("watchfiles").setLevel(logging.ERROR)
    logging.getLogger("watchfiles.main").setLevel(logging.ERROR)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.info("Logging initialized (format=%s)", log_format)