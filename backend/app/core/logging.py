import logging
import sys
from datetime import datetime
import json

# Configure logger
logger = logging.getLogger("gptgram")
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Formatter
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if hasattr(record, "trace_id"):
            log_obj["trace_id"] = record.trace_id
        
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_obj)

# Set formatter
json_formatter = JSONFormatter()
console_handler.setFormatter(json_formatter)

# Add handler to logger
logger.addHandler(console_handler)

# Prevent propagation to avoid duplicate logs
logger.propagate = False
