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
                    name="get_cart",
                    description="Get current cart contents with interactive React UI",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string", "description": "Session ID for cart"}
                        }
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
            ]
            
            logger.debug(f"Created {len(tools)} tools total")
            for i, tool in enumerate(tools):
                logger.debug(f"Tool {i+1}: {tool.name}")
            
            return MCPResponse(
                id=request.id,
                result={
                    "tools": [tool.dict() for tool in tools]
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
            elif tool_name == "get_cart":
                session_id = arguments.get("session_id") or "default"
                return await handle_get_cart_remote_dom(request.id, session_id)
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
            elif tool_name == "get_lebron_jersey":
                # Use detailed product view for individual jersey
                arguments["product_id"] = "lebron-lakers-jersey" 
                return await handle_get_product_details_remote_dom(request.id, arguments)
            elif tool_name == "get_jordan_jersey":
                # Use detailed product view for individual jersey
                arguments["product_id"] = "jordan-bulls-jersey"
                return await handle_get_product_details_remote_dom(request.id, arguments)
            elif tool_name == "get_curry_jersey":
                # Use detailed product view for individual jersey
                arguments["product_id"] = "curry-warriors-jersey"
                return await handle_get_product_details_remote_dom(request.id, arguments)
            elif tool_name == "get_giannis_jersey":
                # Use detailed product view for individual jersey
                arguments["product_id"] = "giannis-bucks-jersey"
                return await handle_get_product_details_remote_dom(request.id, arguments)
            elif tool_name == "get_luka_jersey":
                # Use detailed product view for individual jersey
                arguments["product_id"] = "luka-mavs-jersey"
                return await handle_get_product_details_remote_dom(request.id, arguments)
            elif tool_name == "get_tatum_jersey":
                # Use detailed product view for individual jersey
                arguments["product_id"] = "tatum-celtics-jersey"
                return await handle_get_product_details_remote_dom(request.id, arguments)
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