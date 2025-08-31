#!/usr/bin/env python3
"""MCP server data models and structures"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from shared.config import get_app_config, get_products_with_urls

# Pydantic models for API
class MCPRequest(BaseModel):
    id: str | int
    method: str
    params: Dict[str, Any]

class MCPResponse(BaseModel):
    id: str | int
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None

class MCPInitializeRequest(BaseModel):
    protocolVersion: str
    capabilities: Dict[str, Any]
    clientInfo: Dict[str, Any]

class MCPInitializeResponse(BaseModel):
    protocolVersion: str = "2024-11-05"
    capabilities: Dict[str, Any]
    serverInfo: Dict[str, str]

# Data classes
@dataclass
class Variant:
    id: str
    name: str
    price_modifier: float = 0.0
    in_stock: bool = True

@dataclass
class Product:
    id: str
    name: str
    category: str
    price: float
    description: str
    image_url: str
    variants: List[Variant]
    icon: str = "📦"
    color: str = "#3b82f6"
    in_stock: bool = True
    store: str = ""  # Store identifier for multi-store support
    # 🏀 POC: New fields for NBA jersey feature
    highlight_gif: str = ""
    player_stats: str = ""

@dataclass
class CartItem:
    id: str
    product_id: str
    variant_id: str
    name: str
    variant: str
    price: float
    quantity: int
    image_url: str

# Load products from centralized configuration
def _load_products_from_config():
    """Load products from centralized config"""
    config = get_app_config()
    products_data = get_products_with_urls(config)
    
    products = []
    for product_data in products_data:
        variants = [
            Variant(
                id=v["id"],
                name=v["name"], 
                price_modifier=v["price_modifier"]
            )
            for v in product_data["variants"]
        ]
        
        products.append(Product(
            id=product_data["id"],
            name=product_data["name"],
            category=product_data["category"],
            price=product_data["price"],
            description=product_data["description"],
            image_url=product_data["image_url"],
            variants=variants,
            icon=product_data["icon"],
            color=product_data["color"],
            store=product_data.get("store", ""),
            # 🏀 POC: Handle new NBA fields safely
            highlight_gif=product_data.get("highlight_gif", ""),
            player_stats=product_data.get("player_stats", "")
        ))
    
    return products

PRODUCTS = _load_products_from_config()

# Convert to dict for easy lookup
products = {product.id: product for product in PRODUCTS}

# Session storage for carts
carts: Dict[str, List[CartItem]] = {}

def create_ui_resource(content_type: str, content: str) -> Dict[str, Any]:
    """Create a UI resource for MCP-UI - supports both HTML and remote-dom"""
    if content_type == "html":
        return {
            "type": "resource",
            "resource": {
                "mimeType": "text/html",
                "text": content
            }
        }
    elif content_type == "remoteDom":
        return {
            "type": "resource",
            "resource": {
                "uri": f"ui://remote-component/{content_type}",
                "mimeType": "application/vnd.mcp-ui.remote-dom+javascript; framework=react",
                "framework": "react",
                "text": content
            }
        }
    else:
        # Fallback for legacy format
        return {
            "type": content_type,
            "content": content
        }