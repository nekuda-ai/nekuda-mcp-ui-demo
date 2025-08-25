"""MCP server error handling utilities"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Any, Dict, Optional, Callable, TypeVar, Awaitable
from functools import wraps
import logging

from models import MCPResponse
from shared.error_handling import (
    setup_structured_logging, log_error, create_error_response, 
    ErrorContext, AppError, ValidationError, NotFoundError, CartError, CheckoutError
)

# Generic type for async functions
T = TypeVar('T')

# Setup logger for error utilities
logger = setup_structured_logging("mcp-handlers")

def create_mcp_error_response(
    request_id: str | int, 
    error: Exception, 
    operation: str,
    session_id: Optional[str] = None
) -> MCPResponse:
    context = ErrorContext(
        request_id=str(request_id),
        operation=operation,
        session_id=session_id,
        component="mcp-handler"
    )
    
    # Log the error
    log_error(logger, error, context)
    
    # Create structured error response
    if isinstance(error, AppError):
        return MCPResponse(
            id=request_id,
            error={
                "code": error.get_mcp_error_code(),
                "message": error.user_message,
                "data": {
                    "error_code": error.error_code.value,
                    "operation": operation,
                    "session_id": session_id
                }
            }
        )
    else:
        return MCPResponse(
            id=request_id,
            error={
                "code": -32603,
                "message": "An unexpected error occurred",
                "data": {
                    "error_code": "UNKNOWN_ERROR",
                    "operation": operation,
                    "session_id": session_id
                }
            }
        )

def validate_required_params(params: Dict[str, Any], required_fields: list[str]) -> None:
    missing_fields = [field for field in required_fields if field not in params or params[field] is None]
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

def validate_product_exists(product_id: str, products: Dict[str, Any]) -> Any:
    product = products.get(product_id)
    if not product:
        raise NotFoundError(f"Product not found: {product_id}")
    return product

def validate_variant_exists(variant_id: str, product: Any) -> Any:
    """Validate variant exists in product and return it"""
    variant = next((v for v in product.variants if v.id == variant_id), None)
    if not variant:
        raise NotFoundError(f"Variant not found: {variant_id}")
    return variant

def validate_cart_not_empty(cart: Dict[str, Any], session_id: str) -> None:
    """Validate cart is not empty"""
    if not cart.get("items"):
        raise CartError(f"Cart is empty for session: {session_id}")

def safe_mcp_handler(operation_name: str):
    """
    Decorator for MCP handlers to provide consistent error handling
    SAFE: Only adds logging and error formatting, doesn't change core logic
    """
    def decorator(func: Callable[..., Awaitable[MCPResponse]]) -> Callable[..., Awaitable[MCPResponse]]:
        @wraps(func)
        async def wrapper(request_id: str | int, *args, **kwargs) -> MCPResponse:
            session_id = kwargs.get('session_id', 'unknown')
            
            try:
                # Log operation start (DEBUG level)
                logger.debug(f"Starting {operation_name}", extra={
                    "request_id": str(request_id),
                    "session_id": session_id,
                    "operation": operation_name
                })
                
                # Execute original handler
                result = await func(request_id, *args, **kwargs)
                
                # Log successful completion (DEBUG level)
                logger.debug(f"Completed {operation_name}", extra={
                    "request_id": str(request_id),
                    "session_id": session_id,
                    "operation": operation_name
                })
                
                return result
                
            except Exception as e:
                # Return standardized error response
                return create_mcp_error_response(request_id, e, operation_name, session_id)
        
        return wrapper
    return decorator
