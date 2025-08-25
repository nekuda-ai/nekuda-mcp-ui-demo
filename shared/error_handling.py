"""
Centralized error handling utilities for MCP E-commerce Demo
Provides consistent error types, logging, and response formatting
"""

import logging
import traceback
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass


class ErrorCode(Enum):
    """Standard error codes across the application"""
    # General errors
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # MCP protocol errors (following JSON-RPC 2.0 spec)
    MCP_PARSE_ERROR = "MCP_PARSE_ERROR"  # -32700
    MCP_INVALID_REQUEST = "MCP_INVALID_REQUEST"  # -32600
    MCP_METHOD_NOT_FOUND = "MCP_METHOD_NOT_FOUND"  # -32601
    MCP_INVALID_PARAMS = "MCP_INVALID_PARAMS"  # -32602
    MCP_INTERNAL_ERROR = "MCP_INTERNAL_ERROR"  # -32603
    
    # Business logic errors
    CART_ERROR = "CART_ERROR"
    PRODUCT_ERROR = "PRODUCT_ERROR"
    CHECKOUT_ERROR = "CHECKOUT_ERROR"
    SESSION_ERROR = "SESSION_ERROR"
    
    # External service errors
    OPENAI_ERROR = "OPENAI_ERROR"
    NEKUDA_ERROR = "NEKUDA_ERROR"
    MCP_SERVER_ERROR = "MCP_SERVER_ERROR"


# Map error codes to HTTP status codes
ERROR_CODE_TO_HTTP_STATUS = {
    ErrorCode.UNKNOWN_ERROR: 500,
    ErrorCode.VALIDATION_ERROR: 400,
    ErrorCode.AUTHENTICATION_ERROR: 401,
    ErrorCode.AUTHORIZATION_ERROR: 403,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.RATE_LIMIT_EXCEEDED: 429,
    ErrorCode.MCP_PARSE_ERROR: 400,
    ErrorCode.MCP_INVALID_REQUEST: 400,
    ErrorCode.MCP_METHOD_NOT_FOUND: 404,
    ErrorCode.MCP_INVALID_PARAMS: 400,
    ErrorCode.MCP_INTERNAL_ERROR: 500,
    ErrorCode.CART_ERROR: 400,
    ErrorCode.PRODUCT_ERROR: 400,
    ErrorCode.CHECKOUT_ERROR: 400,
    ErrorCode.SESSION_ERROR: 400,
    ErrorCode.OPENAI_ERROR: 502,
    ErrorCode.NEKUDA_ERROR: 502,
    ErrorCode.MCP_SERVER_ERROR: 502,
}

# Map error codes to MCP JSON-RPC error codes
ERROR_CODE_TO_MCP_CODE = {
    ErrorCode.MCP_PARSE_ERROR: -32700,
    ErrorCode.MCP_INVALID_REQUEST: -32600,
    ErrorCode.MCP_METHOD_NOT_FOUND: -32601,
    ErrorCode.MCP_INVALID_PARAMS: -32602,
    ErrorCode.MCP_INTERNAL_ERROR: -32603,
    ErrorCode.UNKNOWN_ERROR: -32603,
    ErrorCode.VALIDATION_ERROR: -32602,
    ErrorCode.NOT_FOUND: -32601,
    ErrorCode.CART_ERROR: -32603,
    ErrorCode.PRODUCT_ERROR: -32603,
    ErrorCode.CHECKOUT_ERROR: -32603,
    ErrorCode.SESSION_ERROR: -32603,
    ErrorCode.OPENAI_ERROR: -32603,
    ErrorCode.NEKUDA_ERROR: -32603,
    ErrorCode.MCP_SERVER_ERROR: -32603,
}


@dataclass
class ErrorContext:
    """Additional context for error reporting"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    operation: Optional[str] = None
    component: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


class AppError(Exception):
    """Base application error class with structured error information"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        context: Optional[ErrorContext] = None,
        cause: Optional[Exception] = None,
        user_message: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or ErrorContext()
        self.cause = cause
        self.user_message = user_message or self._get_default_user_message()
        self.timestamp = datetime.utcnow()
        
    def _get_default_user_message(self) -> str:
        """Get user-friendly error message based on error code"""
        user_messages = {
            ErrorCode.VALIDATION_ERROR: "Invalid input provided. Please check your data and try again.",
            ErrorCode.NOT_FOUND: "The requested resource was not found.",
            ErrorCode.RATE_LIMIT_EXCEEDED: "Too many requests. Please wait and try again.",
            ErrorCode.CART_ERROR: "There was an issue with your cart. Please try again.",
            ErrorCode.PRODUCT_ERROR: "Product information is temporarily unavailable.",
            ErrorCode.CHECKOUT_ERROR: "Checkout failed. Please review your information and try again.",
            ErrorCode.SESSION_ERROR: "Your session has expired. Please refresh the page.",
            ErrorCode.OPENAI_ERROR: "AI service is temporarily unavailable. Please try again.",
            ErrorCode.NEKUDA_ERROR: "Payment service is temporarily unavailable. Please try again.",
            ErrorCode.MCP_SERVER_ERROR: "Service is temporarily unavailable. Please try again.",
        }
        return user_messages.get(self.error_code, "An unexpected error occurred. Please try again.")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON serialization"""
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "user_message": self.user_message,
            "timestamp": self.timestamp.isoformat(),
            "context": {
                "user_id": self.context.user_id,
                "session_id": self.context.session_id,
                "request_id": self.context.request_id,
                "operation": self.context.operation,
                "component": self.context.component,
                "additional_data": self.context.additional_data,
            } if self.context else None,
            "cause": str(self.cause) if self.cause else None,
        }
    
    def get_http_status(self) -> int:
        """Get appropriate HTTP status code for this error"""
        return ERROR_CODE_TO_HTTP_STATUS.get(self.error_code, 500)
    
    def get_mcp_error_code(self) -> int:
        """Get appropriate MCP JSON-RPC error code"""
        return ERROR_CODE_TO_MCP_CODE.get(self.error_code, -32603)


class ValidationError(AppError):
    """Error for validation failures"""
    def __init__(self, message: str, context: Optional[ErrorContext] = None, cause: Optional[Exception] = None):
        super().__init__(message, ErrorCode.VALIDATION_ERROR, context, cause)


class NotFoundError(AppError):
    """Error for resource not found"""
    def __init__(self, message: str, context: Optional[ErrorContext] = None, cause: Optional[Exception] = None):
        super().__init__(message, ErrorCode.NOT_FOUND, context, cause)


class CartError(AppError):
    """Error for cart operations"""
    def __init__(self, message: str, context: Optional[ErrorContext] = None, cause: Optional[Exception] = None):
        super().__init__(message, ErrorCode.CART_ERROR, context, cause)


class CheckoutError(AppError):
    """Error for checkout operations"""
    def __init__(self, message: str, context: Optional[ErrorContext] = None, cause: Optional[Exception] = None):
        super().__init__(message, ErrorCode.CHECKOUT_ERROR, context, cause)


class ExternalServiceError(AppError):
    """Error for external service failures"""
    def __init__(
        self, 
        service_name: str, 
        message: str, 
        context: Optional[ErrorContext] = None, 
        cause: Optional[Exception] = None
    ):
        error_code = {
            "openai": ErrorCode.OPENAI_ERROR,
            "nekuda": ErrorCode.NEKUDA_ERROR,
            "mcp_server": ErrorCode.MCP_SERVER_ERROR,
        }.get(service_name.lower(), ErrorCode.UNKNOWN_ERROR)
        
        super().__init__(f"{service_name} error: {message}", error_code, context, cause)


def setup_structured_logging(component: str, level: str = None) -> logging.Logger:
    """Setup structured logging for a component with environment-based configuration"""
    import os
    
    # Get log level from environment or use provided level or default to INFO
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Get environment type
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    logger = logging.getLogger(component)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        
        # Different formatting for production vs development
        if environment == "production":
            # Cleaner format for production
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        else:
            # More detailed format for development
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)8s | %(name)15s | %(filename)s:%(lineno)d | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Log configuration on first setup
    if component not in getattr(setup_structured_logging, '_configured_components', set()):
        if not hasattr(setup_structured_logging, '_configured_components'):
            setup_structured_logging._configured_components = set()
        setup_structured_logging._configured_components.add(component)
        logger.info(f"Logging configured for {component}: level={level}, environment={environment}")
    
    return logger


def log_error(
    logger: logging.Logger,
    error: Union[AppError, Exception],
    context: Optional[ErrorContext] = None
) -> None:
    """Log an error with structured information"""
    if isinstance(error, AppError):
        error_data = error.to_dict()
        logger.error(
            f"[{error.error_code.value}] {error.message}",
            extra={
                "error_code": error.error_code.value,
                "context": error_data.get("context"),
                "cause": error_data.get("cause"),
                "user_message": error.user_message,
            }
        )
        if error.cause:
            logger.error(f"Caused by: {error.cause}")
            if hasattr(error.cause, '__traceback__'):
                logger.debug("Traceback: %s", traceback.format_exception(
                    type(error.cause), error.cause, error.cause.__traceback__
                ))
    else:
        context_info = ""
        if context:
            context_parts = []
            if context.operation:
                context_parts.append(f"op={context.operation}")
            if context.session_id:
                context_parts.append(f"session={context.session_id}")
            if context.component:
                context_parts.append(f"component={context.component}")
            if context_parts:
                context_info = f" [{', '.join(context_parts)}]"
        
        logger.error(f"Unexpected error{context_info}: {error}")
        logger.debug("Traceback: %s", traceback.format_exception(
            type(error), error, error.__traceback__
        ))


def handle_error_recovery(
    error: Exception,
    operation: str,
    fallback_action: Optional[callable] = None,
    logger: Optional[logging.Logger] = None
) -> Any:
    """Handle error recovery with optional fallback action"""
    if logger:
        context = ErrorContext(operation=operation)
        log_error(logger, error, context)
    
    if fallback_action:
        try:
            return fallback_action()
        except Exception as fallback_error:
            if logger:
                logger.error(f"Fallback action failed for {operation}: {fallback_error}")
            raise error  # Re-raise original error
    
    raise error


def create_error_response(error: Union[AppError, Exception], request_id: Optional[str] = None) -> Dict[str, Any]:
    """Create standardized error response"""
    if isinstance(error, AppError):
        return {
            "error": {
                "code": error.get_mcp_error_code(),
                "message": error.user_message,
                "data": {
                    "error_code": error.error_code.value,
                    "details": error.message,
                    "timestamp": error.timestamp.isoformat(),
                    "request_id": request_id,
                }
            }
        }
    else:
        return {
            "error": {
                "code": -32603,
                "message": "An unexpected error occurred",
                "data": {
                    "error_code": "UNKNOWN_ERROR",
                    "details": str(error),
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": request_id,
                }
            }
        }
