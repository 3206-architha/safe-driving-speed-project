"""
Structured logging. In production this writes JSON lines to stdout,
which Railway/Render capture automatically — you don't need to manage
log files yourself for a 24/7 deployment.
"""
import logging
import sys
from app.core.config import get_settings

settings = get_settings()


def setup_logging() -> None:
    log_format = (
        '{"time": "%(asctime)s", "level": "%(levelname)s", '
        '"logger": "%(name)s", "message": "%(message)s"}'
    )
    logging.basicConfig(
        level=logging.INFO if not settings.DEBUG else logging.DEBUG,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    # quiet noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


logger = logging.getLogger("safe_driving_api")
