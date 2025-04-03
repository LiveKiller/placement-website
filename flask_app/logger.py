"""Solely based to log errors, why?
IDFK, CAN'T SEE THEM ERRORS IN TERMINAL CAN YA?"""
import logging
import json
from datetime import datetime
import traceback


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
            "stack_trace": traceback.format_exc() if record.exc_info else None
        }
        return json.dumps(log_entry)


def configure_logger():
    logger = logging.getLogger("app")
    logger.setLevel(logging.ERROR)

    file_handler = logging.FileHandler("error_log.json")
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)

    return logger