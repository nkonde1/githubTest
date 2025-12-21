# backend/app/core/logging.py
"""
Centralized logging configuration for the application.
Handles structured logging, log formatting, and log routing.
"""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Any, Dict, List, Union
import json
from datetime import datetime
import traceback
import uuid
import functools
import asyncio

from app.core.config import settings

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(), # Use getMessage() to get the formatted message
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add process and thread info
        log_entry["process_id"] = record.process
        log_entry["thread_id"] = record.thread
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # --- CRITICAL FIX/IMPROVEMENT FOR 'EXTRA' FIELDS ---
        # The 'extra' dictionary passed to logger.info is directly accessible in record.__dict__
        # as top-level keys. Your current loop *tries* to get them, but let's make it more explicit
        # by checking record.args and also ensure no clashes with standard attributes.
        
        # Merge dictionary arguments from msg if present (e.g., logger.info({"key": "value"}))
        if isinstance(record.msg, dict):
            log_entry.update(record.msg)
            # Potentially update the 'message' field to something generic or remove it
            log_entry["message"] = log_entry.get("message", "Structured log message") 

        # Merge keyword arguments passed via `extra` explicitly
        # `record.__dict__` contains all attributes, including those from `extra`
        # The original code's loop was mostly correct, but let's be more precise
        # about which attributes are standard and which are 'extra'
        
        standard_attrs = [
            'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
            'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
            'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
            'thread', 'threadName', 'processName', 'process', 'message',
            'asctime', # 'asctime' is added by formatter, not part of record.__dict__ for extra
            # Add any other standard attributes you don't want to treat as 'extra'
        ]

        for key, value in record.__dict__.items():
            # Exclude internal _keys and standard log record attributes
            if not key.startswith('_') and key not in standard_attrs:
                # Handle UUID and datetime objects in extra fields for JSON serialization
                if isinstance(value, uuid.UUID):
                    log_entry[key] = str(value)
                elif isinstance(value, datetime):
                    log_entry[key] = value.isoformat()
                else:
                    try:
                        # Attempt to serialize to JSON. If it fails, convert to string.
                        # This handles complex objects that might be in 'extra'.
                        json.dumps(value) 
                        log_entry[key] = value
                    except TypeError:
                        log_entry[key] = str(value)
        
        return json.dumps(log_entry)



class HealthCheckFilter(logging.Filter):
    """Filter to exclude health check logs from cluttering the logs."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter out health check requests."""
        message = record.getMessage()
        return not any(
            endpoint in message 
            for endpoint in ['/health', '/metrics', '/favicon.ico']
        )



class SecurityFilter(logging.Filter):
    """Filter to sanitize sensitive information from logs."""
    
    SENSITIVE_PATTERNS = [
        'password', 'token', 'secret', 'key', 'authorization',
        'api_key', 'access_token', 'refresh_token', 'jwt' # Added 'jwt'
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Sanitize sensitive information from log records."""
        
        # Sanitize message arguments (if they are structured)
        if isinstance(record.args, tuple) and record.args:
            sanitized_args = []
            for arg in record.args:
                if isinstance(arg, dict):
                    sanitized_args.append(self._sanitize_dict(arg))
                elif isinstance(arg, str):
                    sanitized_args.append(self._sanitize_string(arg))
                else:
                    sanitized_args.append(arg)
            record.args = tuple(sanitized_args)
        
        # Sanitize the message itself if it's a string or dict
        # Note: If record.msg is a dict, it will eventually be merged into log_entry
        # by JSONFormatter, which then handles sanitization of its values.
        if hasattr(record, 'msg'):
            if isinstance(record.msg, str):
                record.msg = self._sanitize_string(record.msg)
            # If record.msg is a dict, the JSONFormatter will handle its keys/values
            # but for consistency, we can also apply here if needed
            # elif isinstance(record.msg, dict):
            #     record.msg = self._sanitize_dict(record.msg)
        
        # Sanitize values directly in record.__dict__ that came from 'extra'
        # This is crucial for structured logging.
        # We iterate over a copy to allow modification during iteration
        for key, value in list(record.__dict__.items()): 
            if any(pattern in key.lower() for pattern in self.SENSITIVE_PATTERNS):
                setattr(record, key, "[REDACTED]") # Redact the value directly on the record
            elif isinstance(value, dict):
                setattr(record, key, self._sanitize_dict(value))
            elif isinstance(value, list):
                sanitized_list = []
                for item in value:
                    if isinstance(item, dict):
                        sanitized_list.append(self._sanitize_dict(item))
                    elif isinstance(item, str):
                        sanitized_list.append(self._sanitize_string(item))
                    else:
                        sanitized_list.append(item)
                setattr(record, key, sanitized_list)
            elif isinstance(value, str):
                setattr(record, key, self._sanitize_string(value))

        return True
    
    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize dictionary values recursively."""
        sanitized = {}
        for key, value in data.items():
            if any(pattern in key.lower() for pattern in self.SENSITIVE_PATTERNS):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_dict(item) if isinstance(item, dict) else
                    self._sanitize_string(item) if isinstance(item, str) else
                    item for item in value
                ]
            elif isinstance(value, str):
                sanitized[key] = self._sanitize_string(value)
            else:
                sanitized[key] = value
        return sanitized
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitize string content. Enhanced with regex for common patterns."""
        import re
        for pattern in self.SENSITIVE_PATTERNS:
            # Simple case-insensitive replacement for generic patterns
            text = re.sub(re.escape(pattern), '[REDACTED]', text, flags=re.IGNORECASE)
        
        # More specific regex for tokens, if desired (e.g., JWTs, API keys in headers)
        text = re.sub(r"Bearer\s+[\w.-]+", "Bearer [REDACTED_TOKEN]", text, flags=re.IGNORECASE)
        text = re.sub(r"api_key=\w+", "api_key=[REDACTED]", text, flags=re.IGNORECASE)
        
        return text



def setup_logging() -> None:
    """Configure application logging."""
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Determine log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper())
    
    # Logging configuration
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json": {
                "()": JSONFormatter,
            }
        },
        "filters": {
            "health_check": {
                "()": HealthCheckFilter,
            },
            "security": {
                "()": SecurityFilter,
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                # Always use JSON formatter for structured logs if you're passing 'extra'
                "formatter": "json", 
                "stream": sys.stdout,
                "filters": ["security"]
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "json", # Ensure JSON formatter for file logs too
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "filters": ["security"]
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json",
                "filename": "logs/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "filters": ["security"]
            },
            "access_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": "logs/access.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "filters": ["health_check", "security"]
            }
        },
        "loggers": {
            # Application loggers
            "app": {
                "level": log_level,
                "handlers": ["console", "file", "error_file"], # error_file for app level errors
                "propagate": False
            },
            # FastAPI access logs - crucial for seeing HTTP requests/responses
            "uvicorn.access": {
                "level": "INFO", # Keep this at INFO to see requests
                "handlers": ["console", "access_file"], # Send access logs to console and file
                "propagate": False
            },
            "uvicorn": { # General uvicorn logger, often includes startup/shutdown
                "level": log_level,
                "handlers": ["console", "file"],
                "propagate": False
            },
            # Database logs
            "sqlalchemy.engine": {
                "level": "WARNING" if settings.ENVIRONMENT == "production" else "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
            # Celery logs
            "celery": {
                "level": log_level,
                "handlers": ["console", "file"],
                "propagate": False
            },
            # Redis logs
            "redis": {
                "level": "WARNING",
                "handlers": ["console", "file"],
                "propagate": False
            },
            # Third-party library logs
            "httpx": {
                "level": "WARNING",
                "handlers": ["console", "file"],
                "propagate": False
            },
            "stripe": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
            # Dedicated loggers for API, Security, Business events
            "api": {
                "level": log_level,
                "handlers": ["console", "file"],
                "propagate": False
            },
            "security": {
                "level": log_level,
                "handlers": ["console", "file", "error_file"], # Send security events to error file too
                "propagate": False
            },
            "business": {
                "level": log_level,
                "handlers": ["console", "file"],
                "propagate": False
            }
        },
        "root": {
            "level": log_level,
            "handlers": ["console", "file", "error_file"]
        }
    }
    
    # Apply logging configuration
    logging.config.dictConfig(logging_config)
    
    # Disable propagation for specific loggers to avoid duplicate messages
    # as handlers are already defined for them
    logging.getLogger("uvicorn.access").propagate = False
    logging.getLogger("uvicorn").propagate = False
    logging.getLogger("sqlalchemy.engine").propagate = False
    logging.getLogger("celery").propagate = False
    logging.getLogger("redis").propagate = False
    logging.getLogger("httpx").propagate = False
    logging.getLogger("stripe").propagate = False
    logging.getLogger("api").propagate = False
    logging.getLogger("security").propagate = False
    logging.getLogger("business").propagate = False

    # Set up structured logging for the main application
    logger = logging.getLogger("app")
    logger.info(
        "Logging configured",
        extra={
            "environment": settings.ENVIRONMENT,
            "log_level": settings.LOG_LEVEL,
            "app_name": settings.PROJECT_NAME
        }
    )



def get_logger(name: str) -> logging.Logger:
    """Get logger instance with consistent configuration."""
    return logging.getLogger(name)



class LoggerMixin:
    """Mixin class to add logging capability to any class."""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        # Use a logger name that reflects the class's module path for better organization
        return get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")



def log_function_call(func):
    """Decorator to log function calls with parameters and execution time."""
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = asyncio.get_event_loop().time() if asyncio.iscoroutinefunction(func) else time.time()
        
        # Log arguments if not too verbose and not sensitive
        log_kwargs = {k: v for k, v in kwargs.items() if k not in SecurityFilter.SENSITIVE_PATTERNS} # Basic redaction
        
        logger.debug(
            f"Calling {func.__name__}",
            extra={
                "function": func.__name__,
                "module": func.__module__,
                "args_count": len(args),
                "kwargs": log_kwargs, # Log kwargs explicitly in extra
                "event_type": "function_call_start"
            }
        )
        try:
            result = await func(*args, **kwargs)
            execution_time = (asyncio.get_event_loop().time() if asyncio.iscoroutinefunction(func) else time.time()) - start_time
            logger.debug(
                f"Completed {func.__name__}",
                extra={
                    "function": func.__name__,
                    "execution_time_ms": round(execution_time * 1000, 2),
                    "success": True,
                    "event_type": "function_call_end"
                }
            )
            return result
        except Exception as e:
            execution_time = (asyncio.get_event_loop().time() if asyncio.iscoroutinefunction(func) else time.time()) - start_time
            logger.error(
                f"Error in {func.__name__}: {str(e)}",
                extra={
                    "function": func.__name__,
                    "execution_time_ms": round(execution_time * 1000, 2),
                    "error_type": type(e).__name__,
                    "success": False,
                    "event_type": "function_call_error"
                },
                exc_info=True
            )
            raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()

        # Log arguments if not too verbose and not sensitive
        log_kwargs = {k: v for k, v in kwargs.items() if k not in SecurityFilter.SENSITIVE_PATTERNS} # Basic redaction

        logger.debug(
            f"Calling {func.__name__}",
            extra={
                "function": func.__name__,
                "module": func.__module__,
                "args_count": len(args),
                "kwargs": log_kwargs, # Log kwargs explicitly in extra
                "event_type": "function_call_start"
            }
        )
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(
                f"Completed {func.__name__}",
                extra={
                    "function": func.__name__,
                    "execution_time_ms": round(execution_time * 1000, 2),
                    "success": True,
                    "event_type": "function_call_end"
                }
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Error in {func.__name__}: {str(e)}",
                extra={
                    "function": func.__name__,
                    "execution_time_ms": round(execution_time * 1000, 2),
                    "error_type": type(e).__name__,
                    "success": False,
                    "event_type": "function_call_error"
                },
                exc_info=True
            )
            raise

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper



def log_api_request(request_id: str, method: str, path: str, client_host: str = None, user_id: str = None, headers: dict = None, body: Any = None):
    """Log API request details."""
    logger = get_logger("api")
    
    # Sanitize sensitive headers and body if present
    sanitized_headers = SecurityFilter()._sanitize_dict(headers or {})
    sanitized_body = SecurityFilter()._sanitize_dict(body) if isinstance(body, dict) else body # Simple dict body sanitization

    logger.info(
        "API Request Received",
        extra={
            "request_id": request_id,
            "method": method,
            "path": path,
            "client_host": client_host,
            "user_id": user_id,
            "event_type": "api_request",
            "request_headers": sanitized_headers,
            "request_body_preview": str(sanitized_body)[:200] if sanitized_body else None # Log a preview of the body
        }
    )

def log_api_response(request_id: str, status_code: int, execution_time: float, user_id: str = None, response_data: Any = None):
    """Log API response details."""
    logger = get_logger("api")

    sanitized_response_data = SecurityFilter()._sanitize_dict(response_data) if isinstance(response_data, dict) else response_data

    logger.info(
        "API Response Sent",
        extra={
            "request_id": request_id,
            "status_code": status_code,
            "execution_time_ms": round(execution_time * 1000, 2),
            "user_id": user_id,
            "event_type": "api_response",
            "response_data_preview": str(sanitized_response_data)[:200] if sanitized_response_data else None # Log a preview
        }
    )

def log_security_event(event_type: str, user_id: str = None, email: str = None, ip_address: str = None, details: dict = None):
    """Log security-related events."""
    logger = get_logger("security")
    sanitized_details = SecurityFilter()._sanitize_dict(details or {})
    logger.warning(
        f"Security Event: {event_type}",
        extra={
            "event_type": event_type,
            "user_id": user_id,
            "email": email, # The SecurityFilter should handle redacting this if it's sensitive
            "ip_address": ip_address,
            "details": sanitized_details,
            "category": "security"
        }
    )

def log_business_event(event_type: str, user_id: str, data: dict = None):
    """Log business logic events for analytics."""
    logger = get_logger("business")
    sanitized_data = SecurityFilter()._sanitize_dict(data or {})
    logger.info(
        f"Business Event: {event_type}",
        extra={
            "event_type": event_type,
            "user_id": user_id,
            "data": sanitized_data,
            "category": "business"
        }
    )