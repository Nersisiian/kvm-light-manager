import logging
import sys
from contextvars import ContextVar

from pythonjsonlogger import jsonlogger

from app.core.config import settings

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")

def set_correlation_id(cid: str):
    correlation_id_var.set(cid)

def get_correlation_id() -> str:
    return correlation_id_var.get()


class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = get_correlation_id()
        return True


def setup_logging() -> None:
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)

    if settings.LOG_JSON:
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(correlation_id)s %(message)s"
        )
        handler.setFormatter(formatter)

    handler.addFilter(CorrelationIdFilter())
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    root_logger.addHandler(handler)

    logging.getLogger("uvicorn.access").handlers = [handler]
    logging.getLogger("uvicorn.error").handlers = [handler]


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)