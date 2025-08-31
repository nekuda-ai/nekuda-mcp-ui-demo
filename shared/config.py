#!/usr/bin/env python3
"""
Centralized Configuration for MCP E-commerce Demo
All product metadata, URLs, and configuration in one place
"""

import os
from typing import Dict, List, Any
from dataclasses import dataclass

# =============================================================================
# ENVIRONMENT & GENERAL SETTINGS
# =============================================================================

@dataclass
class AppConfig:
    environment: str = "development"
    debug: bool = True
    media_base_url: str = os.getenv("MEDIA_SERVER_URL", "http://localhost:3003") + "/media"
    mcp_server_port: int = 3003
    backend_port: int = 3002
    frontend_port: int = 3001

def get_app_config() -> AppConfig:
    """Get app configuration based on environment variables"""
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        return AppConfig(
            environment="production",
            debug=False,
            media_base_url=os.getenv("MEDIA_SERVER_URL", "http://localhost:3003") + "/media",
            mcp_server_port=int(os.getenv("MCP_SERVER_PORT", "3003")),
            backend_port=int(os.getenv("BACKEND_PORT", "3002")),
            frontend_port=int(os.getenv("FRONTEND_PORT", "3001"))
        )
    else:
        return AppConfig()

# =============================================================================
# PRODUCT CATEGORIES & METADATA
# =============================================================================

CATEGORY_METADATA = {
    "nba-jerseys": {
        "name": "NBA Jerseys",
        "description": "Authentic NBA player jerseys from legendary superstars",
        "icon": "🏀",
        "color": "#FF6B35"
    }
}

# =============================================================================
# PRODUCT DEFINITIONS WITH CENTRALIZED METADATA
# =============================================================================

PRODUCT_DEFINITIONS = [
    # 🏀 NBA JERSEY COLLECTION - 6 LEGENDARY PLAYERS
    {
        "id": "lebron-lakers-jersey",
        "name": "LeBron James Lakers Jersey #6",
        "category": "nba-jerseys", 
        "store": "nba.demo.store",
        "price": 149.99,
        "description": "Official Los Angeles Lakers jersey worn by the King himself. Features premium stitching, authentic team colors, and the iconic #6. Perfect for showing your Lakers pride and basketball legacy.",
        "image_filename": "lebron-lakers-home.jpg",
        "highlight_gif": "lebron-dunk.gif",
        "player_stats": "4x NBA Champion, 4x Finals MVP",
        "variants": [
            {"id": "size-s", "name": "Small", "price_modifier": 0.0},
            {"id": "size-m", "name": "Medium", "price_modifier": 0.0},
            {"id": "size-l", "name": "Large", "price_modifier": 0.0},
            {"id": "size-xl", "name": "X-Large", "price_modifier": 5.0}
        ],
        "icon": "👑",
        "color": "#552583"  # Lakers purple
    },
    {
        "id": "curry-warriors-jersey", 
        "name": "Stephen Curry Warriors Jersey #30",
        "category": "nba-jerseys",
        "store": "nba.demo.store",
        "price": 139.99,
        "description": "Golden State Warriors jersey of the greatest shooter in NBA history. Features the iconic #30 and championship-winning team colors. Represent the 3-point revolution.",
        "image_filename": "curry-warriors-home.jpg",
        "highlight_gif": "curry-three-pointer.gif", 
        "player_stats": "4x NBA Champion, 2x MVP",
        "variants": [
            {"id": "size-s", "name": "Small", "price_modifier": 0.0},
            {"id": "size-m", "name": "Medium", "price_modifier": 0.0},
            {"id": "size-l", "name": "Large", "price_modifier": 0.0},
            {"id": "size-xl", "name": "X-Large", "price_modifier": 5.0}
        ],
        "icon": "🏹",
        "color": "#1D428A"  # Warriors blue
    },
    {
        "id": "giannis-bucks-jersey",
        "name": "Giannis Antetokounmpo Bucks Jersey #34",
        "category": "nba-jerseys",
        "store": "nba.demo.store",
        "price": 134.99,
        "description": "Milwaukee Bucks jersey of the Greek Freak. Features the championship-winning #34 and represents the heart of Milwaukee basketball. Wear the jersey of a true superstar.",
        "image_filename": "giannis-bucks-home.jpg",
        "highlight_gif": "giannis-dunk.gif",
        "player_stats": "NBA Champion, 2x MVP, Finals MVP",
        "variants": [
            {"id": "size-s", "name": "Small", "price_modifier": 0.0},
            {"id": "size-m", "name": "Medium", "price_modifier": 0.0},
            {"id": "size-l", "name": "Large", "price_modifier": 0.0},
            {"id": "size-xl", "name": "X-Large", "price_modifier": 5.0}
        ],
        "icon": "🇬🇷",
        "color": "#00471B"  # Bucks green
    },
    {
        "id": "luka-mavs-jersey",
        "name": "Luka Dončić Mavericks Jersey #77",
        "category": "nba-jerseys",
        "store": "nba.demo.store",
        "price": 124.99,
        "description": "Dallas Mavericks jersey of the Slovenian sensation. Features the unique #77 and represents the future of basketball. Join the Luka Magic phenomenon.",
        "image_filename": "luka-mavs-home.jpg",
        "highlight_gif": "luka-stepback.gif",
        "player_stats": "5x All-Star, Rookie of the Year",
        "variants": [
            {"id": "size-s", "name": "Small", "price_modifier": 0.0},
            {"id": "size-m", "name": "Medium", "price_modifier": 0.0},
            {"id": "size-l", "name": "Large", "price_modifier": 0.0},
            {"id": "size-xl", "name": "X-Large", "price_modifier": 5.0}
        ],
        "icon": "🏀",
        "color": "#00538C"  # Mavs blue
    },
    {
        "id": "tatum-celtics-jersey",
        "name": "Jayson Tatum Celtics Jersey #0",
        "category": "nba-jerseys",
        "store": "nba.demo.store",
        "price": 144.99,
        "description": "Boston Celtics jersey of the rising superstar. Features the iconic #0 and the legendary green of 18-time NBA champions. Represent Celtic pride and championship tradition.",
        "image_filename": "tatum-celtics-home.jpg",
        "highlight_gif": "tatum-dunk.gif",
        "player_stats": "NBA Champion, 5x All-Star",
        "variants": [
            {"id": "size-s", "name": "Small", "price_modifier": 0.0},
            {"id": "size-m", "name": "Medium", "price_modifier": 0.0},
            {"id": "size-l", "name": "Large", "price_modifier": 0.0},
            {"id": "size-xl", "name": "X-Large", "price_modifier": 5.0}
        ],
        "icon": "☘️",
        "color": "#007A33"  # Celtics green
    },
    {
        "id": "jordan-bulls-jersey",
        "name": "Michael Jordan Bulls Jersey #23",
        "category": "nba-jerseys",
        "store": "nba.demo.store",
        "price": 299.99,
        "description": "Chicago Bulls jersey of the GOAT. The legendary #23 that defined basketball greatness. A timeless piece of sports history that transcends generations.",
        "image_filename": "jordan-bulls-home.jpg",
        "highlight_gif": "michael_jordan_dunk2.gif",
        "player_stats": "6x NBA Champion, 5x MVP, GOAT",
        "variants": [
            {"id": "size-s-authentic", "name": "Small Authentic", "price_modifier": 0.0},
            {"id": "size-m-authentic", "name": "Medium Authentic", "price_modifier": 0.0},
            {"id": "size-l-authentic", "name": "Large Authentic", "price_modifier": 0.0},
            {"id": "size-xl-authentic", "name": "X-Large Authentic", "price_modifier": 10.0}
        ],
        "icon": "🐐",
        "color": "#CE1141"  # Bulls red
    }
]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_product_metadata(product_id: str) -> Dict[str, Any]:
    """Get icon and color metadata for a product"""
    for product in PRODUCT_DEFINITIONS:
        if product["id"] == product_id:
            return {
                "icon": product["icon"],
                "color": product["color"]
            }
    return {"icon": "📦", "color": "#3b82f6"}

def get_all_product_metadata() -> Dict[str, Dict[str, str]]:
    """Get all product metadata as a mapping dict for frontend"""
    return {
        product["id"]: {
            "icon": product["icon"], 
            "color": product["color"]
        }
        for product in PRODUCT_DEFINITIONS
    }

def build_image_url(filename: str, config: AppConfig = None) -> str:
    """Build full image URL from filename"""
    if config is None:
        config = get_app_config()
    return f"{config.media_base_url}/{filename}"

def get_products_with_urls(config: AppConfig = None) -> List[Dict[str, Any]]:
    """Get all products with properly built image URLs"""
    if config is None:
        config = get_app_config()
    
    products = []
    for product_def in PRODUCT_DEFINITIONS:
        product = product_def.copy()
        product["image_url"] = build_image_url(product_def["image_filename"], config)
        del product["image_filename"]  # Remove the filename key
        products.append(product)
    
    return products

# =============================================================================
# UI THEME CONFIGURATION  
# =============================================================================

UI_THEME = {
    'colors': {
        'background': 'rgba(60, 60, 65, 0.95)',
        'surface': 'rgba(70, 70, 75, 0.8)',
        'border': 'rgba(80, 80, 85, 0.6)',
        'text_primary': '#ffffff',
        'text_secondary': 'rgba(255, 255, 255, 0.6)',
        'accent': 'linear-gradient(135deg, #00D2FF, #3A7BD5)',
        'success': '#4CAF50',
        'warning': '#FF9800',
        'danger': '#F44336'
    },
    'typography': {
        'font_family': '-apple-system, BlinkMacSystemFont, "SF Pro Display", "Inter", "Segoe UI", system-ui, sans-serif',
        'sizes': {
            'xs': '0.75rem',
            'sm': '0.85rem', 
            'base': '1rem',
            'lg': '1.125rem',
            'xl': '1.25rem',
            'xxl': '1.5rem'
        }
    },
    'spacing': {
        'xs': '4px',
        'sm': '8px',
        'md': '16px',
        'lg': '24px',
        'xl': '32px'
    },
    'radius': {
        'sm': '8px',
        'md': '12px',
        'lg': '16px'
    },
    'shadows': {
        'sm': '0 2px 8px rgba(0, 0, 0, 0.15)',
        'md': '0 8px 24px rgba(0, 0, 0, 0.3)',
        'lg': '0 12px 32px rgba(0, 210, 255, 0.35)'
    }
}

# =============================================================================
# EXPORTS FOR EASY IMPORT
# =============================================================================

__all__ = [
    'AppConfig',
    'get_app_config', 
    'CATEGORY_METADATA',
    'PRODUCT_DEFINITIONS',
    'get_product_metadata',
    'get_all_product_metadata',
    'build_image_url',
    'get_products_with_urls',
    'UI_THEME'
]