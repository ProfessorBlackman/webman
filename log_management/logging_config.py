import json
import logging
from logging import Logger
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import traceback

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest

from config import Config, settings


class JsonFormatter(logging.Formatter):
    """Enhanced JSON formatter with additional context and sanitization"""

    SENSITIVE_FIELDS = {'password', 'token', 'authorization', 'api_key', 'secret',
                        'credential', 'credit_card', 'ssn'}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.default_fields = {
            'service': os.getenv('SERVICE_NAME', 'fastapi-app'),
            'environment': os.getenv('FASTAPI_ENV', 'development'),
        }

    def sanitize_value(self, key: str, value: Any) -> Any:
        """Remove sensitive information from log data"""
        if any(sensitive in str(key).lower() for sensitive in self.SENSITIVE_FIELDS):
            return '[REDACTED]'
        return value

    def get_request_context(self, request: Optional[StarletteRequest] = None) -> Dict[str, Any]:
        """Extract useful information from the current request"""
        if not request:
            return {}

        return {
            'request_id': request.headers.get('X-Request-ID'),
            'ip': request.client.host if request.client else None,
            'method': request.method,
            'path': request.url.path,
            'user_agent': request.headers.get('user-agent'),
        }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with enhanced context"""
        # Start with default fields
        log_record = self.default_fields.copy()

        # Add basic log information
        log_record.update({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        })

        # Add custom fields from extra
        if hasattr(record, 'extra'):
            for key, value in record.extra.items():
                log_record[key] = self.sanitize_value(key, value)

        # Add exception info if present
        if record.exc_info:
            log_record['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }

        # Add any extra attributes that were passed in LogRecord
        for key, value in record.__dict__.items():
            if key not in ['args', 'asctime', 'created', 'exc_info', 'exc_text',
                           'filename', 'funcName', 'levelname', 'levelno', 'lineno',
                           'module', 'msecs', 'msg', 'name', 'pathname', 'process',
                           'processName', 'relativeCreated', 'stack_info', 'thread',
                           'threadName', 'extra']:
                log_record[key] = self.sanitize_value(key, value)

        return json.dumps(log_record, default=str)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log incoming requests and responses"""

    async def dispatch(self, request: Request, call_next):
        # Create a logger for request logging
        request_logger = logging.getLogger('request_logger')

        # Log request details before processing
        request_logger.info('Incoming Request', extra={
            'method': request.method,
            'path': request.url.path,
            'headers': dict(request.headers),
            'client_ip': request.client.host
        })

        # Process the request
        response = await call_next(request)

        # Log response details
        request_logger.info('Request Processed', extra={
            'method': request.method,
            'path': request.url.path,
            'status_code': response.status_code,
            'client_ip': request.client.host
        })

        return response


def setup_logger(
        name: str,
        log_file: str,
        level: int = logging.INFO,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        add_console: bool = False
) -> Logger:
    """
    Create and configure logger with enhanced features

    Args:
        name: Name of the logger
        log_file: Path to log file
        level: Minimum log level
        max_bytes: Maximum size of each log file
        backup_count: Number of backup files to keep
        add_console: Whether to add console output (useful for development)
    """
    formatter = JsonFormatter()
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to prevent duplicates
    logger.handlers = []

    # File handler with rotation
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Optional console handler
    if add_console or os.getenv('FASTAPI_ENV') == 'development':
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


# Environment-specific configuration
ENV = settings.ENVIRONMENT
LOG_LEVEL = logging.DEBUG if ENV == 'development' else logging.INFO
CONSOLE_OUTPUT = ENV == 'development'

# Create loggers with enhanced configuration
loggers = {
    'main': setup_logger(
        'main_logger',
        'logs/main.log',
        level=LOG_LEVEL,
        add_console=CONSOLE_OUTPUT
    ),
    'db': setup_logger(
        'db_logger',
        'logs/db.log',
        level=LOG_LEVEL
    ),
    'email': setup_logger(
        'email_logger',
        'logs/emails.log',
        level=LOG_LEVEL
    ),
    'request': setup_logger(
        'request_logger',
        'logs/requests.log',
        level=LOG_LEVEL
    ),
'log_management': setup_logger(
        'log_management',
        'logs/log_management.log',
        level=LOG_LEVEL
    ),
'performance': setup_logger(
        'performance_logger',
        'logs/performance.log',
        level=LOG_LEVEL
    ),
'responsiveness': setup_logger(
        'responsiveness_logger',
        'logs/responsiveness.log',
        level=LOG_LEVEL
    ),
'accessibility': setup_logger(
        'accessibility_logger',
        'logs/accessibility.log',
        level=LOG_LEVEL
    ),
}


# Helper function to log with extra context
def log_with_context(logger: Logger, level: str, message: str, **extra):
    """Helper function to log with extra context"""
    log_method = getattr(logger, level.lower())
    log_method(message, extra=extra)


# Export individual loggers for backward compatibility
main_logger = loggers['main']
db_logger = loggers['db']
email_logger = loggers['email']
request_logger = loggers['request']
log_management_logger = loggers['log_management']
accessibility_logger = loggers['accessibility']
responsiveness_logger = loggers['responsiveness']
performance_logger = loggers['performance']

# Example usage in a FastAPI app
from fastapi import FastAPI


def setup_logging(app: FastAPI):
    """Setup logging middleware and configuration for FastAPI app"""
    # Add request logging middleware
    app.add_middleware(RequestLoggingMiddleware)

    # Optional: Configure uvicorn logger
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers = []  # Clear default handlers
    uvicorn_logger.propagate = False
    uvicorn_logger.setLevel(LOG_LEVEL)

    # Add handlers to uvicorn logger
    file_handler = RotatingFileHandler(
        'logs/uvicorn.log',
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(JsonFormatter())
    uvicorn_logger.addHandler(file_handler)

    # Add console handler if in development
    if CONSOLE_OUTPUT:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(JsonFormatter())
        uvicorn_logger.addHandler(console_handler)