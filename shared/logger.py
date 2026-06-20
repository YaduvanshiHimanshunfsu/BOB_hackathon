"""
shared/logger.py
================
Structured JSON logging for all CIFE microservices.
Provides consistent, machine-parseable log output across API, Worker, and Dashboard.
"""

import logging
import json
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects for easy parsing."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": getattr(record, "service", "unknown"),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        # Include extra fields if present
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "session_id"):
            log_entry["session_id"] = record.session_id
        if hasattr(record, "risk_score"):
            log_entry["risk_score"] = record.risk_score
        if hasattr(record, "action"):
            log_entry["action"] = record.action

        # Include exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


def get_logger(service_name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Create a structured JSON logger for a specific service.

    Args:
        service_name: Name of the microservice (e.g., 'api_gateway', 'ml_worker')
        level: Logging level (default: INFO)

    Returns:
        Configured logging.Logger instance
    """
    logger = logging.getLogger(f"cife.{service_name}")
    logger.setLevel(level)

    # Avoid duplicate handlers on repeated calls
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

    # Inject service name into all records from this logger
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.service = service_name
        return record

    logging.setLogRecordFactory(record_factory)

    return logger
