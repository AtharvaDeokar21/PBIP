"""Structured JSON logging shared by the Credora services.

Every record is written to stdout as one JSON object so the log shipper
(Grafana Alloy → Loki) can parse it. The current request id is attached to
every record emitted while a request is being handled.

Never log request/response bodies, Authorization headers, tokens, passwords,
query strings or full account numbers.
"""

import json
import logging
import os
import sys
from contextvars import ContextVar
from datetime import datetime, timezone

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)

# Extra attributes copied from ``logger.info(..., extra={...})`` into the JSON.
EXTRA_FIELDS = (
    "method",
    "path",
    "route",
    "status",
    "duration_ms",
    "client_ip",
)


class JsonFormatter(logging.Formatter):
    def __init__(self, service: str):
        super().__init__()
        self.service = service

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "service": self.service,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = request_id_ctx.get()
        if request_id:
            payload["request_id"] = request_id
        for field in EXTRA_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(service: str) -> None:
    """Route the root and uvicorn loggers to a single JSON stdout handler."""
    service = os.getenv("SERVICE_NAME", service)
    level = os.getenv("LOG_LEVEL", "INFO").upper()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter(service))

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    for name in ("uvicorn", "uvicorn.error"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers = []
        uvicorn_logger.propagate = True
    # Replaced by the structured access record written by the request middleware.
    logging.getLogger("uvicorn.access").disabled = True
    # Avoid logging SQL statements or connection details.
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
