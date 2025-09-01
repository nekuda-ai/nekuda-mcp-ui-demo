#!/usr/bin/env python3
"""MCP E-commerce Server with MCP-UI components"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

# Import error handling utilities
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.error_handling import (
    setup_structured_logging, log_error, create_error_response, 
    ErrorContext, AppError, ValidationError, NotFoundError
)

# Import models and handlers
from models import (
    MCPRequest, MCPResponse, MCPInitializeRequest, MCPInitializeResponse,
    Product, CartItem, Variant, products, carts
)
from quote_service import (
    merchant_quote_service, ShippingAddress, EstimationHints, Cart, CartItemForQuote
)
from simple_handlers import (
    handle_get_cart_state,
    handle_clear_cart,
    handle_remove_from_cart,
    handle_set_cart_quantity
)
from remote_dom_handlers import (
    handle_get_products_remote_dom,
    handle_get_product_details_remote_dom,
    handle_add_to_cart_remote_dom,
    handle_get_cart_remote_dom,
    handle_checkout_remote_dom,
    handle_process_checkout_remote_dom
)

# Additional models for MCP protocol
from pydantic import BaseModel

class MCPTool(BaseModel):
    name: str
    description: str
    inputSchema: Dict[str, Any]

app = FastAPI(title="MCP E-commerce Server", version="1.0.0")

# Setup structured logging
logger = setup_structured_logging("mcp-server")

# Mount static files for serving product images
app.mount("/media", StaticFiles(directory="../media"), name="media")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "MCP E-commerce Server", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/mcp")
async def mcp_endpoint(raw_request: Dict[str, Any]):
    """Main MCP protocol endpoint"""
    request_id = raw_request.get("id", "unknown")
    method = raw_request.get("method", "unknown")
    
    # Log incoming request (DEBUG level to avoid spam)
    logger.debug(f"MCP request received", extra={
        "request_id": request_id,
        "method": method,
        "has_params": "params" in raw_request
    })
    
    try:
        # Handle JSON-RPC format by extracting the relevant fields
        if "jsonrpc" in raw_request:
            request = MCPRequest(
                id=raw_request["id"],
                method=raw_request["method"],
                params=raw_request.get("params") or {}
            )
        else:
            # Handle direct MCPRequest format
            if raw_request.get("params") is None:
                raw_request["params"] = {}
            request = MCPRequest(**raw_request)
        if request.method == "initialize":
            return MCPResponse(
                id=request.id,
                result={
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "MCP E-commerce Server",
                        "version": "1.0.0"
                    }
                }
            )
        
        elif request.method == "tools/list":
            logger.debug("Creating tools list...")
            tools = [
                MCPTool(
                    name="get_products",
                    description="Get all available products with interactive React UI",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "Filter by category (electronics, fashion)",
                                "enum": ["electronics", "fashion"]
                            }
                        }
                    }
                ),
                MCPTool(
                    name="get_cart_state",
                    description="Return a structured cart snapshot (no UI)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string"}
                        }
                    }
                ),
                MCPTool(
                    name="clear_cart",
                    description="Clear all items from the cart and return a snapshot (no UI)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string"}
                        },
                        "required": ["session_id"]
                    }
                ),
                MCPTool(
                    name="remove_from_cart",
                    description="Remove a specific product variant from the cart and return a snapshot (no UI)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "string"},
                            "variant_id": {"type": "string"},
                            "session_id": {"type": "string"}
                        },
                        "required": ["product_id", "variant_id", "session_id"]
                    }
                ),
                MCPTool(
                    name="set_cart_quantity",
                    description="Set the quantity for a product variant in the cart and return a snapshot (no UI)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "string"},
                            "variant_id": {"type": "string"},
                            "quantity": {"type": "integer", "minimum": 0},
                            "session_id": {"type": "string"}
                        },
                        "required": ["product_id", "variant_id", "quantity", "session_id"]
                    }
                ),
                MCPTool(
                    name="get_product_details",
                    description="Get detailed information about a specific product with React UI",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "product_id": {
                                "type": "string",
                                "description": "The ID of the product"
                            }
                        },
                        "required": ["product_id"]
                    }
                ),
                MCPTool(
                    name="add_to_cart",
                    description="Add a product variant to the cart with React success UI",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "string"},
                            "variant_id": {"type": "string"},
                            "quantity": {"type": "integer", "minimum": 1, "default": 1},
                            "session_id": {"type": "string", "description": "Session ID for cart"}
                        },
                        "required": ["product_id", "variant_id"]
                    }
                ),
                MCPTool(
                    name="checkout",
                    description="Checkout with current cart contents using React checkout form",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string"},
                            "name": {"type": "string"},
                            "email": {"type": "string"},
                            "address": {"type": "string"},
                            "payment_method": {"type": "string"}
                        },
                        "required": ["session_id"]
                    }
                ),
                MCPTool(
                    name="process_checkout",
                    description="Process the checkout form submission and complete the order",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string"},
                            "name": {"type": "string"},
                            "email": {"type": "string"},
                            "address": {"type": "string"},
                            "payment_method": {"type": "string"}
                        },
                        "required": ["session_id", "name", "email", "address"]
                    }
                ),
                MCPTool(
                    name="get_nba_jerseys",
                    description="Get all NBA jerseys with interactive UI carousel showing legendary players",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                MCPTool(
                    name="get_lebron_jersey",
                    description="Show LeBron James Lakers Jersey #6 with detailed view and interactive features",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                MCPTool(
                    name="get_jordan_jersey",
                    description="Show Michael Jordan Bulls Jersey #23 with detailed view and GOAT achievements",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                MCPTool(
                    name="get_curry_jersey",
                    description="Show Stephen Curry Warriors Jersey #30 with detailed view and shooting records",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                MCPTool(
                    name="get_basketballs",
                    description="Get all premium basketballs with interactive UI carousel showing official NBA balls, training balls, and outdoor basketballs",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                ),
                MCPTool(
                    name="get_spalding_official_ball",
                    description="Show Spalding NBA Official Game Ball - the authentic ball used in NBA games",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                ),
                MCPTool(
                    name="get_wilson_basketball",
                    description="Show Wilson NBA Official Game Basketball - premium Wilson basketball with composite leather",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                ),
                MCPTool(
                    name="get_giannis_jersey",
                    description="Show Giannis Antetokounmpo Bucks Jersey #34 with detailed view and Greek Freak achievements",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                MCPTool(
                    name="get_luka_jersey",
                    description="Show Luka Dončić Mavericks Jersey #77 with detailed view and Luka Magic stats",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                MCPTool(
                    name="get_tatum_jersey",
                    description="Show Jayson Tatum Celtics Jersey #0 with detailed view and championship legacy",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                # Quote Management Tools - Core merchant functionality
                MCPTool(
                    name="create_or_update_quote",
                    description="Create or update a price quote with shipping, tax, and discount calculations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "quote_session_id": {"type": "string", "description": "Quote session identifier"},
                            "cart": {
                                "type": "object",
                                "properties": {
                                    "currency": {"type": "string", "default": "USD"},
                                    "items": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "quantity": {"type": "integer"},
                                                "unit_price": {"type": "number"},
                                                "name": {"type": "string"}
                                            },
                                            "required": ["quantity", "unit_price", "name"]
                                        }
                                    }
                                },
                                "required": ["items"]
                            },
                            "shipping_address": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "phone": {"type": "string"},
                                    "address_line1": {"type": "string"},
                                    "address_line2": {"type": "string"},
                                    "city": {"type": "string"},
                                    "state": {"type": "string"},
                                    "postal_code": {"type": "string"},
                                    "country": {"type": "string", "default": "US"}
                                }
                            },
                            "selected_shipping_id": {"type": "string", "description": "ID of selected shipping option"},
                            "estimation_hints": {
                                "type": "object",
                                "properties": {
                                    "fallback_state": {"type": "string"},
                                    "fallback_postal_code": {"type": "string"},
                                    "fallback_country": {"type": "string", "default": "US"}
                                }
                            }
                        },
                        "required": ["quote_session_id", "cart"]
                    }
                ),
                MCPTool(
                    name="get_quote",
                    description="Retrieve an existing price quote",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "quote_session_id": {"type": "string", "description": "Quote session identifier"}
                        },
                        "required": ["quote_session_id"]
                    }
                ),
                MCPTool(
                    name="validate_quote_for_payment",
                    description="Validate a quote before payment processing",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "quote_session_id": {"type": "string"},
                            "version": {"type": "integer", "description": "Quote version to validate"}
                        },
                        "required": ["quote_session_id", "version"]
                    }
                ),
                MCPTool(
                    name="apply_coupon",
                    description="Apply a coupon code to an existing quote",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "quote_session_id": {"type": "string"},
                            "coupon_code": {"type": "string", "description": "Coupon code to apply"}
                        },
                        "required": ["quote_session_id", "coupon_code"]
                    }
                ),
                MCPTool(
                    name="remove_coupon",
                    description="Remove a coupon from an existing quote",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "quote_session_id": {"type": "string"},
                            "coupon_code": {"type": "string", "description": "Coupon code to remove"}
                        },
                        "required": ["quote_session_id", "coupon_code"]
                    }
                ),
                MCPTool(
                    name="get_available_coupons",
                    description="Get list of available coupon codes for a quote",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "quote_session_id": {"type": "string"}
                        },
                        "required": ["quote_session_id"]
                    }
                ),
            ]
            
            logger.debug(f"Created {len(tools)} tools total")
            for i, tool in enumerate(tools):
                logger.debug(f"Tool {i+1}: {tool.name}")
            
            return MCPResponse(
                id=request.id,
                result={
                    "tools": [tool.model_dump() for tool in tools]
                }
            )
        
        elif request.method == "tools/call":
            tool_name = request.params.get("name")
            arguments = request.params.get("arguments") or {}
            
            # Route to appropriate handler - All tools now use Remote-DOM React components ONLY
            if tool_name == "get_products":
                return await handle_get_products_remote_dom(request.id, arguments)
            elif tool_name == "get_product_details":
                return await handle_get_product_details_remote_dom(request.id, arguments)
            elif tool_name == "add_to_cart":
                session_id = arguments.get("session_id") or "default"
                return await handle_add_to_cart_remote_dom(request.id, arguments, session_id)
            elif tool_name == "checkout":
                session_id = arguments.get("session_id") or "default"
                return await handle_checkout_remote_dom(request.id, session_id, arguments)
            elif tool_name == "get_cart_state":
                session_id = arguments.get("session_id") or "default"
                return await handle_get_cart_state(request.id, session_id)
            elif tool_name == "clear_cart":
                session_id = arguments.get("session_id") or "default"
                return await handle_clear_cart(request.id, session_id)
            elif tool_name == "remove_from_cart":
                session_id = arguments.get("session_id") or "default"
                return await handle_remove_from_cart(request.id, arguments, session_id)
            elif tool_name == "set_cart_quantity":
                session_id = arguments.get("session_id") or "default"
                return await handle_set_cart_quantity(request.id, arguments, session_id)
            elif tool_name == "process_checkout":
                session_id = arguments.get("session_id") or "default"
                return await handle_process_checkout_remote_dom(request.id, session_id, arguments)
            elif tool_name == "get_nba_jerseys":
                # Filter to show only NBA jerseys
                arguments["category"] = "nba-jerseys"
                return await handle_get_products_remote_dom(request.id, arguments)
            elif tool_name == "get_basketballs":
                # Filter to show only basketballs
                arguments["category"] = "college-basketball"
                return await handle_get_products_remote_dom(request.id, arguments)
            elif tool_name == "get_spalding_official_ball":
                # Use detailed product view for Spalding official ball
                arguments["product_id"] = "spalding-nba-official-game-ball"
                arguments["source_tool"] = "get_basketballs"
                return await handle_get_product_details_remote_dom(request.id, arguments)
            elif tool_name == "get_wilson_basketball":
                # Use detailed product view for Wilson basketball
                arguments["product_id"] = "wilson-nba-official-basketball"
                arguments["source_tool"] = "get_basketballs"
                return await handle_get_product_details_remote_dom(request.id, arguments)
            elif tool_name == "get_lebron_jersey":
                # Use detailed product view for individual jersey
                arguments["product_id"] = "lebron-lakers-jersey" 
                arguments["source_tool"] = "get_nba_jerseys"
                return await handle_get_product_details_remote_dom(request.id, arguments)
            elif tool_name == "get_jordan_jersey":
                # Use detailed product view for individual jersey
                arguments["product_id"] = "jordan-bulls-jersey"
                arguments["source_tool"] = "get_nba_jerseys"
                return await handle_get_product_details_remote_dom(request.id, arguments)
            elif tool_name == "get_curry_jersey":
                # Use detailed product view for individual jersey
                arguments["product_id"] = "curry-warriors-jersey"
                arguments["source_tool"] = "get_nba_jerseys"
                return await handle_get_product_details_remote_dom(request.id, arguments)
            elif tool_name == "get_giannis_jersey":
                # Use detailed product view for individual jersey
                arguments["product_id"] = "giannis-bucks-jersey"
                arguments["source_tool"] = "get_nba_jerseys"
                return await handle_get_product_details_remote_dom(request.id, arguments)
            elif tool_name == "get_luka_jersey":
                # Use detailed product view for individual jersey
                arguments["product_id"] = "luka-mavs-jersey"
                arguments["source_tool"] = "get_nba_jerseys"
                return await handle_get_product_details_remote_dom(request.id, arguments)
            elif tool_name == "get_tatum_jersey":
                # Use detailed product view for individual jersey
                arguments["product_id"] = "tatum-celtics-jersey"
                arguments["source_tool"] = "get_nba_jerseys"
                return await handle_get_product_details_remote_dom(request.id, arguments)
            
            # Quote Management Tools
            elif tool_name == "create_or_update_quote":
                return await handle_create_or_update_quote(request.id, arguments)
            elif tool_name == "get_quote":
                return await handle_get_quote(request.id, arguments)
            elif tool_name == "validate_quote_for_payment":
                return await handle_validate_quote_for_payment(request.id, arguments)
            elif tool_name == "apply_coupon":
                return await handle_apply_coupon(request.id, arguments)
            elif tool_name == "remove_coupon":
                return await handle_remove_coupon(request.id, arguments)
            elif tool_name == "get_available_coupons":
                return await handle_get_available_coupons(request.id, arguments)
            
            else:
                return MCPResponse(
                    id=request.id,
                    error={
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}"
                    }
                )
        
        else:
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32601,
                    "message": f"Unknown method: {request.method}"
                }
            )
            
    except Exception as e:
        # Try to get request id, fallback to raw_request id if available
        request_id = getattr(request, 'id', None) if 'request' in locals() else raw_request.get('id', 'unknown')
        
        # Log the error with context
        context = ErrorContext(
            request_id=str(request_id),
            operation=f"mcp_endpoint:{method}",
            component="mcp-server"
        )
        log_error(logger, e, context)
        
        # Create structured error response
        error_response = create_error_response(e, str(request_id))
        return MCPResponse(
            id=request_id,
            **error_response
        )

@app.post("/sessions")
async def create_session():
    """Create a new cart session and return a session ID"""
    session_id = str(uuid.uuid4())
    # Initialize the session with an empty cart and other necessary structures
    carts[session_id] = {
        "items": [],
        "total": 0.0,
        "currency": "USD"
    }
    logger.info(f"Created new session: {session_id}")
    return {"session_id": session_id}

# Quote Management Handler Functions
async def handle_create_or_update_quote(request_id: str, arguments: Dict[str, Any]) -> MCPResponse:
    """Handle create or update quote MCP tool call"""
    try:
        quote_session_id = arguments["quote_session_id"]
        cart_data = arguments["cart"]
        
        # Convert cart data to Cart object
        cart_items = [
            CartItemForQuote(
                sku=f"item_{i}",
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                name=item["name"]
            ) for i, item in enumerate(cart_data["items"])
        ]
        
        cart = Cart(
            currency=cart_data.get("currency", "USD"),
            items=cart_items
        )
        
        # Convert optional shipping address
        shipping_address = None
        if "shipping_address" in arguments:
            addr_data = arguments["shipping_address"]
            shipping_address = ShippingAddress(
                name=addr_data.get("name"),
                phone=addr_data.get("phone"),
                address_line1=addr_data.get("address_line1"),
                address_line2=addr_data.get("address_line2"),
                city=addr_data.get("city"),
                state=addr_data.get("state"),
                postal_code=addr_data.get("postal_code"),
                country=addr_data.get("country", "US")
            )
        
        # Convert optional estimation hints
        estimation_hints = None
        if "estimation_hints" in arguments:
            hints_data = arguments["estimation_hints"]
            estimation_hints = EstimationHints(
                fallback_state=hints_data.get("fallback_state"),
                fallback_postal_code=hints_data.get("fallback_postal_code"),
                fallback_country=hints_data.get("fallback_country", "US")
            )
        
        selected_shipping_id = arguments.get("selected_shipping_id")
        
        # Create or update quote
        quote = merchant_quote_service.create_or_update_quote(
            quote_session_id=quote_session_id,
            cart=cart,
            shipping_address=shipping_address,
            estimation_hints=estimation_hints,
            selected_shipping_id=selected_shipping_id
        )
        
        # Convert quote to JSON-serializable format
        quote_data = {
            "quote_session_id": quote.quote_session_id,
            "version": quote.version,
            "status": quote.status.value,
            "address_confidence": quote.address_confidence.value,
            "merchandise_total": quote.merchandise_total,
            "shipping_options": [
                {
                    "id": opt.id,
                    "label": opt.label,
                    "amount": opt.amount,
                    "estimated_days": opt.estimated_days,
                    "selected": opt.selected
                } for opt in quote.shipping_options
            ],
            "selected_shipping": {
                "id": quote.selected_shipping.id,
                "label": quote.selected_shipping.label,
                "amount": quote.selected_shipping.amount,
                "estimated_days": quote.selected_shipping.estimated_days,
                "selected": quote.selected_shipping.selected
            } if quote.selected_shipping else None,
            "tax": quote.tax,
            "discounts": [
                {
                    "code": disc.code,
                    "amount": disc.amount,
                    "description": disc.description
                } for disc in quote.discounts
            ],
            "subtotal": quote.subtotal,
            "total": quote.total,
            "currency": quote.currency,
            "expires_at": quote.expires_at.isoformat(),
            "requires_address": quote.requires_address,
            "warnings": quote.warnings
        }
        
        return MCPResponse(
            id=request_id,
            result={"quote": quote_data}
        )
        
    except Exception as e:
        logger.error(f"Error in create_or_update_quote: {e}")
        return MCPResponse(
            id=request_id,
            error={
                "code": -32603,
                "message": f"Failed to create or update quote: {str(e)}"
            }
        )

async def handle_get_quote(request_id: str, arguments: Dict[str, Any]) -> MCPResponse:
    """Handle get quote MCP tool call"""
    try:
        quote_session_id = arguments["quote_session_id"]
        quote = merchant_quote_service.get_quote(quote_session_id)
        
        if not quote:
            return MCPResponse(
                id=request_id,
                error={
                    "code": -32602,
                    "message": "Quote not found or expired"
                }
            )
        
        # Convert quote to JSON-serializable format
        quote_data = {
            "quote_session_id": quote.quote_session_id,
            "version": quote.version,
            "status": quote.status.value,
            "address_confidence": quote.address_confidence.value,
            "merchandise_total": quote.merchandise_total,
            "shipping_options": [
                {
                    "id": opt.id,
                    "label": opt.label,
                    "amount": opt.amount,
                    "estimated_days": opt.estimated_days,
                    "selected": opt.selected
                } for opt in quote.shipping_options
            ],
            "selected_shipping": {
                "id": quote.selected_shipping.id,
                "label": quote.selected_shipping.label,
                "amount": quote.selected_shipping.amount,
                "estimated_days": quote.selected_shipping.estimated_days,
                "selected": quote.selected_shipping.selected
            } if quote.selected_shipping else None,
            "tax": quote.tax,
            "discounts": [
                {
                    "code": disc.code,
                    "amount": disc.amount,
                    "description": disc.description
                } for disc in quote.discounts
            ],
            "subtotal": quote.subtotal,
            "total": quote.total,
            "currency": quote.currency,
            "expires_at": quote.expires_at.isoformat(),
            "requires_address": quote.requires_address,
            "warnings": quote.warnings
        }
        
        return MCPResponse(
            id=request_id,
            result={"quote": quote_data}
        )
        
    except Exception as e:
        logger.error(f"Error in get_quote: {e}")
        return MCPResponse(
            id=request_id,
            error={
                "code": -32603,
                "message": f"Failed to get quote: {str(e)}"
            }
        )

async def handle_validate_quote_for_payment(request_id: str, arguments: Dict[str, Any]) -> MCPResponse:
    """Handle validate quote for payment MCP tool call"""
    try:
        quote_session_id = arguments["quote_session_id"]
        version = arguments["version"]
        
        is_valid, message = merchant_quote_service.validate_quote_for_payment(quote_session_id, version)
        
        return MCPResponse(
            id=request_id,
            result={
                "valid": is_valid,
                "message": message
            }
        )
        
    except Exception as e:
        logger.error(f"Error in validate_quote_for_payment: {e}")
        return MCPResponse(
            id=request_id,
            error={
                "code": -32603,
                "message": f"Failed to validate quote: {str(e)}"
            }
        )

async def handle_apply_coupon(request_id: str, arguments: Dict[str, Any]) -> MCPResponse:
    """Handle apply coupon MCP tool call"""
    try:
        quote_session_id = arguments["quote_session_id"]
        coupon_code = arguments["coupon_code"]
        
        success, message, updated_quote = merchant_quote_service.apply_coupon(quote_session_id, coupon_code)
        
        result = {
            "success": success,
            "message": message
        }
        
        if updated_quote:
            # Include updated quote data
            result["quote"] = {
                "quote_session_id": updated_quote.quote_session_id,
                "version": updated_quote.version,
                "status": updated_quote.status.value,
                "address_confidence": updated_quote.address_confidence.value,
                "merchandise_total": updated_quote.merchandise_total,
                "shipping_options": [
                    {
                        "id": opt.id,
                        "label": opt.label,
                        "amount": opt.amount,
                        "estimated_days": opt.estimated_days,
                        "selected": opt.selected
                    } for opt in updated_quote.shipping_options
                ],
                "selected_shipping": {
                    "id": updated_quote.selected_shipping.id,
                    "label": updated_quote.selected_shipping.label,
                    "amount": updated_quote.selected_shipping.amount,
                    "estimated_days": updated_quote.selected_shipping.estimated_days,
                    "selected": updated_quote.selected_shipping.selected
                } if updated_quote.selected_shipping else None,
                "tax": updated_quote.tax,
                "discounts": [
                    {
                        "code": disc.code,
                        "amount": disc.amount,
                        "description": disc.description
                    } for disc in updated_quote.discounts
                ],
                "subtotal": updated_quote.subtotal,
                "total": updated_quote.total,
                "currency": updated_quote.currency,
                "expires_at": updated_quote.expires_at.isoformat(),
                "requires_address": updated_quote.requires_address,
                "warnings": updated_quote.warnings
            }
        
        return MCPResponse(
            id=request_id,
            result=result
        )
        
    except Exception as e:
        logger.error(f"Error in apply_coupon: {e}")
        return MCPResponse(
            id=request_id,
            error={
                "code": -32603,
                "message": f"Failed to apply coupon: {str(e)}"
            }
        )

async def handle_remove_coupon(request_id: str, arguments: Dict[str, Any]) -> MCPResponse:
    """Handle remove coupon MCP tool call"""
    try:
        quote_session_id = arguments["quote_session_id"]
        coupon_code = arguments["coupon_code"]
        
        success, message, updated_quote = merchant_quote_service.remove_coupon(quote_session_id, coupon_code)
        
        result = {
            "success": success,
            "message": message
        }
        
        if updated_quote:
            # Include updated quote data
            result["quote"] = {
                "quote_session_id": updated_quote.quote_session_id,
                "version": updated_quote.version,
                "status": updated_quote.status.value,
                "address_confidence": updated_quote.address_confidence.value,
                "merchandise_total": updated_quote.merchandise_total,
                "shipping_options": [
                    {
                        "id": opt.id,
                        "label": opt.label,
                        "amount": opt.amount,
                        "estimated_days": opt.estimated_days,
                        "selected": opt.selected
                    } for opt in updated_quote.shipping_options
                ],
                "selected_shipping": {
                    "id": updated_quote.selected_shipping.id,
                    "label": updated_quote.selected_shipping.label,
                    "amount": updated_quote.selected_shipping.amount,
                    "estimated_days": updated_quote.selected_shipping.estimated_days,
                    "selected": updated_quote.selected_shipping.selected
                } if updated_quote.selected_shipping else None,
                "tax": updated_quote.tax,
                "discounts": [
                    {
                        "code": disc.code,
                        "amount": disc.amount,
                        "description": disc.description
                    } for disc in updated_quote.discounts
                ],
                "subtotal": updated_quote.subtotal,
                "total": updated_quote.total,
                "currency": updated_quote.currency,
                "expires_at": updated_quote.expires_at.isoformat(),
                "requires_address": updated_quote.requires_address,
                "warnings": updated_quote.warnings
            }
        
        return MCPResponse(
            id=request_id,
            result=result
        )
        
    except Exception as e:
        logger.error(f"Error in remove_coupon: {e}")
        return MCPResponse(
            id=request_id,
            error={
                "code": -32603,
                "message": f"Failed to remove coupon: {str(e)}"
            }
        )

async def handle_get_available_coupons(request_id: str, arguments: Dict[str, Any]) -> MCPResponse:
    """Handle get available coupons MCP tool call"""
    try:
        quote_session_id = arguments["quote_session_id"]
        available_coupons = merchant_quote_service.get_available_coupons(quote_session_id)
        
        return MCPResponse(
            id=request_id,
            result={
                "coupons": available_coupons
            }
        )
        
    except Exception as e:
        logger.error(f"Error in get_available_coupons: {e}")
        return MCPResponse(
            id=request_id,
            error={
                "code": -32603,
                "message": f"Failed to get available coupons: {str(e)}"
            }
        )

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 3003))
    host = os.getenv("HOST", "0.0.0.0")
    environment = os.getenv("ENVIRONMENT", "development")
    
    uvicorn.run(
        app, 
        host=host, 
        port=port,
        reload=environment == "development"
    )