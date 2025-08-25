#!/usr/bin/env python3
"""Simple MCP tool handlers"""

import json
from typing import Dict, Any, List
from models import MCPResponse, products, carts, create_ui_resource

async def handle_get_products(request_id: str | int, arguments: Dict[str, Any]) -> MCPResponse:
    category = arguments.get("category")
    
    filtered_products = list(products.values())
    if category:
        filtered_products = [p for p in products.values() if p.category == category]
    product_icons = {
        "headphones-1": "🎧", "smartphone-1": "📱", "laptop-1": "💻",
        "tshirt-1": "👕", "shoes-1": "👟", "backpack-1": "🎒"
    }
    
    product_colors = {
        "headphones-1": "#3b82f6", "smartphone-1": "#6366f1", "laptop-1": "#8b5cf6",
        "tshirt-1": "#10b981", "shoes-1": "#f59e0b", "backpack-1": "#ef4444"
    }
    
    products_json = []
    for product in filtered_products:
        first_variant = product.variants[0] if product.variants else None
        display_price = product.price + (first_variant.price_modifier if first_variant else 0)
        
        products_json.append({
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": display_price,
            "category": product.category,
            "icon": product_icons.get(product.id, "📦"),
            "color": product_colors.get(product.id, "#6b7280"),
            "image_url": product.image_url,
            "variant_id": first_variant.id if first_variant else ""
        })
    
    products_data = json.dumps(products_json)
    
    # Create HTML content using string concatenation to avoid f-string issues
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Products - MCP-UI + nekuda wallet integration demo</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        /* Force dark theme on all elements */
        *, *::before, *::after {
            background-color: inherit !important;
        }
        
        html {
            background: #0a0a0b;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Inter', 'Segoe UI', system-ui, sans-serif;
            background: rgba(42, 42, 45, 0.95) !important;
            color: #ffffff;
            margin: 0;
            padding: 8px;
            height: 440px;
            overflow-y: auto;
            font-feature-settings: "cv02", "cv03", "cv04", "cv11";
            letter-spacing: -0.011em;
            font-size: 14px;
        }
        
        /* Custom scrollbar styling */
        html, body {
            scrollbar-width: thin;
            scrollbar-color: rgba(0, 210, 255, 0.3) transparent;
        }
        
        ::-webkit-scrollbar {
            width: 6px;
            background: transparent;
        }
        
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        
        ::-webkit-scrollbar-thumb {
            background: rgba(0, 210, 255, 0.3);
            border-radius: 3px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(0, 210, 255, 0.5);
        }
        
        .product-navigator {
            width: 100%;
            height: 420px;
            background: rgba(60, 60, 65, 0.9);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(80, 80, 85, 0.6);
            border-radius: 8px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
            padding: 16px;
            margin: 0;
            position: relative;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
        }
        
        .product-navigator::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
        }
        
        .product-main-area {
            flex: 1;
            display: flex;
            flex-direction: column;
            min-height: 0;
            overflow: visible;
        }
        
        .product-header {
            text-align: center;
            margin-bottom: 6px;
            flex-shrink: 0;
        }
        
        .product-counter {
            color: rgba(255, 255, 255, 0.6);
            font-size: 0.85rem;
            font-weight: 500;
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .product-title {
            background: linear-gradient(135deg, #00D2FF 0%, #3A7BD5 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .product-display {
            position: relative;
            text-align: center;
            margin-bottom: 4px;
            flex: 0 0 auto;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            min-height: 0;
        }
        
        .product-icon {
            width: 80px;
            height: 80px;
            border-radius: 12px;
            margin: 0 auto 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.5rem;
            color: white;
            position: relative;
            overflow: hidden;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            background: linear-gradient(135deg, var(--icon-color, #3b82f6) 0%, rgba(255,255,255,0.1) 100%);
        }
        
        .product-icon:hover {
            transform: translateY(-4px) scale(1.02);
            box-shadow: 0 16px 48px rgba(0, 0, 0, 0.4);
        }
        
        .price-tag {
            position: absolute;
            top: 8px;
            left: 8px;
            background: linear-gradient(135deg, #00D2FF 0%, #3A7BD5 100%);
            color: white;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 700;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
            z-index: 3;
            letter-spacing: -0.01em;
        }
        
        .product-name {
            color: #ffffff;
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 6px;
            letter-spacing: -0.02em;
            line-height: 1.2;
        }
        
        /* Price and category removed - price is now overlay on image */
        
        .product-actions {
            display: flex;
            gap: 6px;
            margin: 12px 0;
            padding: 0 12px;
        }
        
        .btn {
            flex: 1;
            padding: 8px 8px;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            letter-spacing: -0.01em;
        }
        
        .btn-details {
            background: rgba(80, 80, 85, 0.8);
            color: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(100, 100, 105, 0.8);
        }
        
        .btn-details:hover {
            background: rgba(100, 100, 105, 0.9);
            border-color: rgba(0, 210, 255, 0.4);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }
        
        .btn-add {
            background: linear-gradient(135deg, #00D2FF 0%, #3A7BD5 100%);
            color: white;
            box-shadow: 0 8px 24px rgba(0, 210, 255, 0.25);
            border: 1px solid rgba(0, 210, 255, 0.3);
        }
        
        .btn-add:hover {
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 16px 40px rgba(0, 210, 255, 0.35);
        }
        
        .btn-add:active {
            transform: translateY(-1px) scale(0.98);
        }
        
        .navigation {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            flex-shrink: 0;
            margin-top: 8px;
            margin-bottom: 8px;
            padding: 4px 0;
        }
        
        .nav-btn {
            width: 28px;
            height: 28px;
            border: none;
            border-radius: 8px;
            background: rgba(80, 80, 85, 0.8);
            color: rgba(255, 255, 255, 0.8);
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid rgba(100, 100, 105, 0.8);
            backdrop-filter: blur(20px);
        }
        
        .nav-btn:hover:not(:disabled) {
            background: rgba(0, 210, 255, 0.15);
            color: #00D2FF;
            border-color: rgba(0, 210, 255, 0.3);
            transform: translateY(-2px) scale(1.05);
            box-shadow: 0 8px 24px rgba(0, 210, 255, 0.2);
        }
        
        .nav-btn:disabled {
            opacity: 0.2;
            cursor: not-allowed;
        }
        
        .nav-dots {
            display: flex;
            gap: 4px;
        }
        
        .nav-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.3);
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .nav-dot.active {
            background: linear-gradient(135deg, #00D2FF 0%, #3A7BD5 100%);
            transform: scale(1.2);
            box-shadow: 0 2px 6px rgba(0, 210, 255, 0.4);
        }
        
        .product-content {
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
    </style>
</head>
<body>
    <div class="product-navigator">
        <div class="product-main-area">
            <div class="product-header">
                <div class="product-counter" id="productCounter">1 of """ + str(len(filtered_products)) + """</div>
                <div class="product-title"></div>
            </div>
            
            <div class="product-content" id="productContent">
                <!-- Product content will be populated by JavaScript -->
            </div>
        </div>
        
        <div class="navigation">
            <button class="nav-btn" id="prevBtn" onclick="previousProduct()">‹</button>
            <div class="nav-dots" id="navDots">
                <!-- Dots will be populated by JavaScript -->
            </div>
            <button class="nav-btn" id="nextBtn" onclick="nextProduct()">›</button>
        </div>
    </div>
    
    <script>
        const products = """ + products_data + """;
        let currentIndex = 0;
        
        function renderProduct(index) {
            const product = products[index];
            if (!product) return;
            
            const content = document.getElementById('productContent');
            content.innerHTML = `
                <div class="product-display">
                    <div class="product-icon" style="--icon-color: ${product.color}; position: relative;">
                        ${product.icon}
                        <div class="price-tag">$${product.price.toFixed(2)}</div>
                    </div>
                    <div class="product-name">${product.name}</div>
                </div>
                
                <div class="product-actions">
                    <button class="btn btn-details" onclick="viewProduct('${product.id}')">
                        View Details
                    </button>
                    <button class="btn btn-add" onclick="quickAdd('${product.id}', '${product.variant_id}')">
                        Add to Cart
                    </button>
                </div>
            `;
            
            // Update counter
            document.getElementById('productCounter').textContent = `${index + 1} of ${products.length}`;
            
            // Update navigation
            updateNavigation();
        }
        
        function updateNavigation() {
            const prevBtn = document.getElementById('prevBtn');
            const nextBtn = document.getElementById('nextBtn');
            
            prevBtn.disabled = currentIndex === 0;
            nextBtn.disabled = currentIndex === products.length - 1;
            
            // Update dots
            const dotsContainer = document.getElementById('navDots');
            dotsContainer.innerHTML = '';
            
            for (let i = 0; i < products.length; i++) {
                const dot = document.createElement('div');
                dot.className = `nav-dot ${i === currentIndex ? 'active' : ''}`;
                dot.onclick = () => goToProduct(i);
                dotsContainer.appendChild(dot);
            }
        }
        
        function previousProduct() {
            if (currentIndex > 0) {
                currentIndex--;
                renderProduct(currentIndex);
            }
        }
        
        function nextProduct() {
            if (currentIndex < products.length - 1) {
                currentIndex++;
                renderProduct(currentIndex);
            }
        }
        
        function goToProduct(index) {
            if (index >= 0 && index < products.length) {
                currentIndex = index;
                renderProduct(currentIndex);
            }
        }
        
        function viewProduct(productId) {
            window.parent.postMessage({
                type: "tool",
                payload: {
                    toolName: "get_product_details",
                    params: { product_id: productId }
                }
            }, '*');
        }
        
        function quickAdd(productId, variantId) {
            if (!variantId) {
                alert('Please view details to select a variant first');
                return;
            }
            
            window.parent.postMessage({
                type: "tool",
                payload: {
                    toolName: "add_to_cart",
                    params: { 
                        product_id: productId, 
                        variant_id: variantId,
                        quantity: 1
                    }
                }
            }, '*');
        }
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') {
                e.preventDefault();
                previousProduct();
            } else if (e.key === 'ArrowRight') {
                e.preventDefault();
                nextProduct();
            }
        });
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            renderProduct(0);
        });
    </script>
</body>
</html>"""
    
    ui_resource = create_ui_resource(
        content_type="html",
        content=html_content
    )
    
    return MCPResponse(
        id=request_id,
        result={"content": [ui_resource]}
    )

# Simple implementations for other handlers
async def handle_get_product_details(request_id: str | int, arguments: Dict[str, Any]) -> MCPResponse:
    product_id = arguments.get("product_id")
    product = products.get(product_id)
    if not product:
        return MCPResponse(
            id=request_id,
            error={"code": -32602, "message": "Product not found: " + str(product_id)}
        )
    
    # Extract values for JavaScript to avoid f-string issues
    js_product_id = product.id
    js_variant_id = product.variants[0].id if product.variants else ""
    
    # Create product details HTML using string concatenation to avoid format issues
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Product Details - MCP-UI + nekuda wallet integration demo</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        html {
            background: #0a0a0b;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Inter', 'Segoe UI', system-ui, sans-serif;
            background: rgba(42, 42, 45, 0.95) !important;
            color: #ffffff;
            margin: 0;
            padding: 16px;
            height: 440px;
            overflow: visible;
            font-feature-settings: "cv02", "cv03", "cv04", "cv11";
            letter-spacing: -0.011em;
            font-size: 14px;
        }
        
        .product-details-container {
            width: 100%;
            height: auto;
            background: rgba(60, 60, 65, 0.9);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(80, 80, 85, 0.6);
            border-radius: 8px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
            padding: 24px 16px;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            position: relative;
            overflow: visible;
        }
        
        .product-icon {
            width: 80px;
            height: 80px;
            border-radius: 12px;
            margin: 0 auto 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.5rem;
            color: white;
            background: linear-gradient(135deg, """ + product.color + """ 0%, rgba(255,255,255,0.1) 100%);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }
        
        .product-name {
            color: #ffffff;
            font-size: 1.2rem;
            font-weight: 700;
            margin-bottom: 8px;
            letter-spacing: -0.02em;
        }
        
        .product-description {
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.85rem;
            line-height: 1.4;
            margin-bottom: 12px;
            text-align: center;
            max-width: 300px;
        }
        
        .product-price {
            background: linear-gradient(135deg, #00D2FF 0%, #3A7BD5 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 1.4rem;
            font-weight: 800;
            margin-bottom: 16px;
            letter-spacing: -0.02em;
        }
        
        .product-actions {
            display: flex;
            gap: 12px;
            justify-content: center;
        }
        
        .btn {
            padding: 10px 16px;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            letter-spacing: -0.01em;
        }
        
        .btn-back {
            background: rgba(80, 80, 85, 0.8);
            color: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(100, 100, 105, 0.8);
        }
        
        .btn-back:hover {
            background: rgba(100, 100, 105, 0.9);
            border-color: rgba(0, 210, 255, 0.4);
            transform: translateY(-1px);
        }
        
        .btn-add {
            background: linear-gradient(135deg, #00D2FF 0%, #3A7BD5 100%);
            color: white;
            box-shadow: 0 8px 24px rgba(0, 210, 255, 0.25);
            border: 1px solid rgba(0, 210, 255, 0.3);
        }
        
        .btn-add:hover {
            transform: translateY(-2px) scale(1.02);
            box-shadow: 0 12px 32px rgba(0, 210, 255, 0.35);
        }
        
        .btn-add:active {
            transform: translateY(-1px) scale(0.98);
        }
    </style>
</head>
<body>
    <div class="product-details-container">
        <div class="product-icon">
            """ + product.icon + """
        </div>
        <div class="product-name">""" + product.name + """</div>
        <div class="product-description">""" + (product.description[:120] + ('...' if len(product.description) > 120 else '')) + """</div>
        <div class="product-price">$""" + str(product.price) + """</div>
        <div class="product-actions">
            <button class="btn btn-back" onclick="goBack()">← Back</button>
            <button class="btn btn-add" onclick="addToCart()">Add to Cart</button>
        </div>
    </div>
</body>
    <script>
        function addToCart() {
            window.parent.postMessage({
                type: "tool",
                payload: {
                    toolName: "add_to_cart",
                    params: { 
                        product_id: '""" + js_product_id + """',
                        variant_id: '""" + js_variant_id + """',
                        quantity: 1
                    }
                }
            }, '*');
        }
        function goBack() {
            window.parent.postMessage({
                type: "tool",
                payload: {
                    toolName: "get_products",
                    params: {}
                }
            }, '*');
        }
    </script>
    """
    
    ui_resource = create_ui_resource(
        content_type="html", 
        content=html_content
    )
    
    return MCPResponse(
        id=request_id,
        result={"content": [ui_resource]}
    )

async def handle_add_to_cart(request_id: str | int, arguments: Dict[str, Any], session_id: str) -> MCPResponse:
    product_id = arguments.get("product_id")
    variant_id = arguments.get("variant_id") 
    quantity = arguments.get("quantity", 1)
    
    # Find the product and variant
    product = products.get(product_id)
    if not product:
        return MCPResponse(
            id=request_id,
            error={"code": -32602, "message": f"Product not found: {product_id}"}
        )
    
    variant = next((v for v in product.variants if v.id == variant_id), None)
    if not variant:
        return MCPResponse(
            id=request_id,
            error={"code": -32602, "message": f"Variant not found: {variant_id}"}
        )
    
    # Initialize cart if it doesn't exist
    if session_id not in carts:
        carts[session_id] = {"items": [], "total": 0.0}
    
    # Check if item already exists in cart
    existing_item = None
    for item in carts[session_id]["items"]:
        if item["product_id"] == product_id and item["variant_id"] == variant_id:
            existing_item = item
            break
    
    if existing_item:
        existing_item["quantity"] += quantity
    else:
        carts[session_id]["items"].append({
            "product_id": product_id,
            "variant_id": variant_id,
            "quantity": quantity,
            "added_at": "2024-01-01T00:00:00Z"  # In real app, use actual timestamp
        })
    
    # Recalculate cart total
    total = 0.0
    for item in carts[session_id]["items"]:
        item_product = products.get(item["product_id"])
        item_variant = next((v for v in item_product.variants if v.id == item["variant_id"]), None) if item_product else None
        if item_product and item_variant:
            item_price = item_product.price + item_variant.price_modifier
            total += item_price * item["quantity"]
    
    carts[session_id]["total"] = total
    
    # Now generate the UI response
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Added to Cart - MCP-UI + nekuda wallet integration demo</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        /* Force dark theme on all elements */
        *, *::before, *::after {
            background-color: inherit !important;
        }
        
        html {
            background: #0a0a0b;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Inter', 'Segoe UI', system-ui, sans-serif;
            background: rgba(42, 42, 45, 0.95) !important;
            color: #ffffff;
            padding: 16px;
            height: 440px;
            overflow: visible;
            display: flex;
            align-items: center;
            justify-content: center;
            font-feature-settings: "cv02", "cv03", "cv04", "cv11";
            letter-spacing: -0.011em;
            font-size: 14px;
        }
        
        .success-container {
            width: 100%;
            max-width: 380px;
            height: auto;
            background: rgba(60, 60, 65, 0.9);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(80, 80, 85, 0.6);
            border-radius: 8px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
            padding: 20px 16px;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            position: relative;
            overflow: visible;
            margin: 0 auto;
        }
        
        .success-container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
        }
        
        .success-icon {
            width: 50px;
            height: 50px;
            margin: 0 auto 12px;
            background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            animation: successBounce 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55);
            box-shadow: 0 4px 16px rgba(34, 197, 94, 0.3);
        }
        
        @keyframes successBounce {
            0% {
                transform: scale(0) rotate(180deg);
                opacity: 0;
            }
            50% {
                transform: scale(1.2) rotate(270deg);
            }
            100% {
                transform: scale(1) rotate(360deg);
                opacity: 1;
            }
        }
        
        .success-title {
            color: #ffffff;
            font-size: 1.625rem;
            font-weight: 700;
            margin-bottom: 12px;
            letter-spacing: -0.02em;
        }
        
        .success-message {
            color: rgba(255, 255, 255, 0.8);
            font-size: 1rem;
            line-height: 1.5;
            margin-bottom: 28px;
        }
        
        .action-buttons {
            display: flex;
            gap: 12px;
            flex-direction: column;
        }
        
        .continue-button {
            background: linear-gradient(135deg, #00D2FF 0%, #3A7BD5 100%);
            color: white;
            border: none;
            padding: 14px 28px;
            border-radius: 16px;
            font-size: 0.9375rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 6px 20px rgba(0, 210, 255, 0.25);
            border: 1px solid rgba(0, 210, 255, 0.3);
            letter-spacing: -0.01em;
        }
        
        .continue-button:hover {
            transform: translateY(-2px) scale(1.02);
            box-shadow: 0 12px 32px rgba(0, 210, 255, 0.35);
        }
        
        .continue-button:active {
            transform: translateY(0) scale(0.98);
        }
        
        .view-cart-button {
            background: rgba(30, 30, 32, 0.8);
            color: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(42, 42, 45, 0.8);
            padding: 12px 28px;
            border-radius: 16px;
            font-size: 0.9375rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            letter-spacing: -0.01em;
        }
        
        .view-cart-button:hover {
            background: rgba(42, 42, 45, 0.9);
            border-color: rgba(0, 210, 255, 0.3);
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
        }
        
        .cart-indicator {
            background: rgba(34, 197, 94, 0.15);
            border: 1px solid rgba(34, 197, 94, 0.3);
            border-radius: 12px;
            padding: 12px 16px;
            margin-bottom: 24px;
            font-size: 0.875rem;
            color: #22C55E;
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="success-container">
        <div class="success-icon">✅</div>
        <h1 class="success-title">Added to Cart!</h1>
        <p class="success-message">Item has been added to your cart successfully.</p>
        
        <div class="cart-indicator">
            🛒 Item is now in your cart
        </div>
        
        <div class="action-buttons">
            <button class="continue-button" onclick="continueShopping()">
                Continue Shopping
            </button>
            <button class="view-cart-button" onclick="viewCart()">
                View Cart
            </button>
        </div>
    </div>

    <script>
        function continueShopping() {
            window.parent.postMessage({
                type: "tool",
                payload: {
                    toolName: "get_products",
                    params: {}
                }
            }, '*');
        }
        
        function viewCart() {
            window.parent.postMessage({
                type: "ui-action",
                payload: {
                    action: "toggle-cart"
                }
            }, '*');
        }
    </script>
</body>
</html>"""
    
    ui_resource = create_ui_resource(
        content_type="html",
        content=html_content
    )
    
    # Include a structured cart snapshot as data
    snapshot = _build_cart_snapshot(session_id)
    return MCPResponse(
        id=request_id,
        result={
            "content": [ui_resource],
            "data": {"cart": snapshot}
        }
    )

async def handle_get_cart(request_id: str | int, session_id: str) -> MCPResponse:
    cart = carts.get(session_id, {"items": [], "total": 0.0})
    
    if not cart["items"]:
        # Empty cart - show beautiful empty state
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Cart - MCP-UI + nekuda wallet integration demo</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        /* Force dark theme on all elements */
        *, *::before, *::after {
            background-color: inherit !important;
        }
        
        html {
            background: #0a0a0b;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Inter', 'Segoe UI', system-ui, sans-serif;
            background: #0a0a0b !important;
            color: #ffffff;
            padding: 8px;
            height: 325px;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            font-feature-settings: "cv02", "cv03", "cv04", "cv11";
            letter-spacing: -0.011em;
        }
        
        .cart-container {
            max-width: 480px;
            width: 100%;
            background: rgba(17, 17, 19, 0.95);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(30, 30, 32, 0.8);
            border-radius: 24px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
            padding: 48px 32px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .cart-container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
        }
        
        .cart-icon {
            width: 80px;
            height: 80px;
            margin: 0 auto 24px;
            background: rgba(42, 42, 45, 0.6);
            border-radius: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.5rem;
            border: 2px dashed rgba(255, 255, 255, 0.2);
        }
        
        .cart-title {
            color: #ffffff;
            font-size: 1.875rem;
            font-weight: 700;
            margin-bottom: 16px;
            letter-spacing: -0.02em;
        }
        
        .cart-message {
            color: rgba(255, 255, 255, 0.6);
            font-size: 1.125rem;
            line-height: 1.6;
            margin-bottom: 32px;
        }
        
        .browse-button {
            background: linear-gradient(135deg, #00D2FF 0%, #3A7BD5 100%);
            color: white;
            border: none;
            padding: 16px 32px;
            border-radius: 16px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 8px 24px rgba(0, 210, 255, 0.25);
            border: 1px solid rgba(0, 210, 255, 0.3);
            letter-spacing: -0.01em;
        }
        
        .browse-button:hover {
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 16px 40px rgba(0, 210, 255, 0.35);
        }
        
        .browse-button:active {
            transform: translateY(-1px) scale(0.98);
        }
    </style>
</head>
<body>
    <div class="cart-container">
        <div class="cart-icon">🛒</div>
        <h1 class="cart-title">Your Cart</h1>
        <p class="cart-message">Your cart is empty.</p>
        <button class="browse-button" onclick="startShopping()">
            Browse Products
        </button>
    </div>

    <script>
        function startShopping() {
            window.parent.postMessage({
                type: "tool",
                payload: {
                    toolName: "get_products",
                    params: {}
                }
            }, '*');
        }
    </script>
</body>
</html>"""
    else:
        # Cart has items - show them with dark theme styling
        items_html = ""
        for item in cart["items"]:
            product = products.get(item["product_id"])
            variant = next((v for v in product.variants if v.id == item["variant_id"]), None) if product else None
            if product and variant:
                item_price = product.price + variant.price_modifier
                item_total = item_price * item["quantity"]
                items_html += f"""
                <div class="cart-item">
                    <div class="item-details">
                        <h3>{product.name}</h3>
                        <p>{variant.name}</p>
                        <p class="price">${item_price:.2f} x {item["quantity"]} = ${item_total:.2f}</p>
                    </div>
                </div>
                """
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Cart - MCP-UI + nekuda wallet integration demo</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        /* Force dark theme on all elements */
        *, *::before, *::after {{
            background-color: inherit !important;
        }}
        
        html {{
            background: #0a0a0b;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Inter', 'Segoe UI', system-ui, sans-serif;
            background: #0a0a0b !important;
            color: #ffffff;
            padding: 20px;
            min-height: 100vh;
            font-feature-settings: "cv02", "cv03", "cv04", "cv11";
            letter-spacing: -0.011em;
        }}
        
        .cart-container {{
            max-width: 600px;
            margin: 0 auto;
            background: rgba(17, 17, 19, 0.95);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(30, 30, 32, 0.8);
            border-radius: 24px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
            padding: 32px;
            position: relative;
            overflow: hidden;
        }}
        
        .cart-container::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
        }}
        
        .cart-title {{
            color: #ffffff;
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 24px;
            text-align: center;
            letter-spacing: -0.02em;
        }}
        
        .cart-item {{
            background: rgba(30, 30, 32, 0.6);
            border: 1px solid rgba(42, 42, 45, 0.8);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 16px;
        }}
        
        .cart-item h3 {{
            color: #ffffff;
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        
        .cart-item p {{
            color: rgba(255, 255, 255, 0.8);
            margin-bottom: 4px;
        }}
        
        .price {{
            color: #00D2FF !important;
            font-weight: 600;
        }}
        
        .cart-total {{
            text-align: center;
            margin: 24px 0;
            padding: 20px;
            background: rgba(0, 210, 255, 0.1);
            border: 1px solid rgba(0, 210, 255, 0.3);
            border-radius: 16px;
        }}
        
        .total-amount {{
            color: #00D2FF;
            font-size: 1.5rem;
            font-weight: 700;
        }}
        
        .checkout-button {{
            width: 100%;
            background: linear-gradient(135deg, #00D2FF 0%, #3A7BD5 100%);
            color: white;
            border: none;
            padding: 16px 32px;
            border-radius: 16px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 8px 24px rgba(0, 210, 255, 0.25);
            border: 1px solid rgba(0, 210, 255, 0.3);
            margin-top: 20px;
        }}
        
        .checkout-button:hover {{
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 16px 40px rgba(0, 210, 255, 0.35);
        }}
    </style>
</head>
<body>
    <div class="cart-container">
        <h1 class="cart-title">🛒 Your Cart</h1>
        
        {items_html}
        
        <div class="cart-total">
            <p>Total: <span class="total-amount">${cart["total"]:.2f}</span></p>
        </div>
        
        <button class="checkout-button" onclick="checkout()">
            Proceed to Checkout
        </button>
    </div>

    <script>
        function checkout() {{
            window.parent.postMessage({{
                type: "tool",
                payload: {{
                    toolName: "checkout",
                    params: {{}}
                }}
            }}, '*');
        }}
    </script>
</body>
</html>"""
    
    ui_resource = create_ui_resource(
        content_type="html",
        content=html_content
    )
    
    return MCPResponse(
        id=request_id,
        result={"content": [ui_resource]}
    )

# -----------------------
# Cart snapshot utilities and no-UI cart tools
# -----------------------
def _build_cart_snapshot(session_id: str) -> Dict[str, Any]:
    cart = carts.get(session_id)
    if isinstance(cart, dict):
        items = cart.get("items", [])
        total = float(cart.get("total", 0.0))
    else:
        items = cart or []
        total = 0.0
        for item in items:
            product = products.get(item.get("product_id"))
            if not product:
                continue
            variant = next((v for v in product.variants if v.id == item.get("variant_id")), None)
            if not variant:
                continue
            total += (product.price + variant.price_modifier) * int(item.get("quantity", 1))
    normalized_items = []
    for item in items:
        product = products.get(item.get("product_id"))
        variant = next((v for v in product.variants if v.id == item.get("variant_id")), None) if product else None
        if not product or not variant:
            normalized_items.append({
                "product_id": item.get("product_id"),
                "variant_id": item.get("variant_id"),
                "name": item.get("product_id", "Item"),
                "variant": item.get("variant_id", "Variant"),
                "price": 0.0,
                "quantity": int(item.get("quantity", 1)),
                "image_url": ""
            })
        else:
            normalized_items.append({
                "product_id": product.id,
                "variant_id": variant.id,
                "name": product.name,
                "variant": variant.name,
                "price": product.price + variant.price_modifier,
                "quantity": int(item.get("quantity", 1)),
                "image_url": getattr(variant, 'image_url', None) or product.image_url
            })
    return {"items": normalized_items, "total": round(total, 2)}

async def handle_get_cart_state(request_id: str | int, session_id: str) -> MCPResponse:
    snapshot = _build_cart_snapshot(session_id)
    return MCPResponse(id=request_id, result={"data": {"cart": snapshot}})

async def handle_clear_cart(request_id: str | int, session_id: str) -> MCPResponse:
    if session_id in carts:
        if isinstance(carts[session_id], dict):
            carts[session_id]["items"] = []
            carts[session_id]["total"] = 0.0
        else:
            carts[session_id] = []
    snapshot = _build_cart_snapshot(session_id)
    return MCPResponse(id=request_id, result={"data": {"cart": snapshot}})

async def handle_remove_from_cart(request_id: str | int, arguments: Dict[str, Any], session_id: str) -> MCPResponse:
    product_id = arguments.get("product_id")
    variant_id = arguments.get("variant_id")
    if not product_id or not variant_id:
        return MCPResponse(id=request_id, error={"code": -32602, "message": "Missing required fields: product_id and variant_id"})
    if session_id not in carts:
        carts[session_id] = {"items": [], "total": 0.0}
    if isinstance(carts[session_id], dict):
        items = carts[session_id]["items"]
        carts[session_id]["items"] = [i for i in items if not (i.get("product_id") == product_id and i.get("variant_id") == variant_id)]
        # recalc total
        total = 0.0
        for item in carts[session_id]["items"]:
            p = products.get(item.get("product_id"))
            v = next((vv for vv in p.variants if vv.id == item.get("variant_id")), None) if p else None
            if p and v:
                total += (p.price + v.price_modifier) * int(item.get("quantity", 1))
        carts[session_id]["total"] = total
    else:
        carts[session_id] = [i for i in carts[session_id] if not (i.get("product_id") == product_id and i.get("variant_id") == variant_id)]
    snapshot = _build_cart_snapshot(session_id)
    return MCPResponse(id=request_id, result={"data": {"cart": snapshot}})

async def handle_set_cart_quantity(request_id: str | int, arguments: Dict[str, Any], session_id: str) -> MCPResponse:
    product_id = arguments.get("product_id")
    variant_id = arguments.get("variant_id")
    quantity = int(arguments.get("quantity", 1))
    if not product_id or not variant_id:
        return MCPResponse(id=request_id, error={"code": -32602, "message": "product_id and variant_id are required"})
    if quantity < 0:
        return MCPResponse(id=request_id, error={"code": -32602, "message": "quantity must be >= 0"})
    if session_id not in carts:
        carts[session_id] = {"items": [], "total": 0.0}
    if not isinstance(carts[session_id], dict):
        carts[session_id] = {"items": carts[session_id] or [], "total": 0.0}
    items = carts[session_id]["items"]
    existing = None
    for it in items:
        if it.get("product_id") == product_id and it.get("variant_id") == variant_id:
            existing = it
            break
    if quantity == 0:
        if existing:
            items.remove(existing)
    else:
        if existing:
            existing["quantity"] = quantity
        else:
            items.append({"product_id": product_id, "variant_id": variant_id, "quantity": quantity})
    total = 0.0
    for it in carts[session_id]["items"]:
        p = products.get(it.get("product_id"))
        v = next((vv for vv in p.variants if vv.id == it.get("variant_id")), None) if p else None
        if p and v:
            total += (p.price + v.price_modifier) * int(it.get("quantity", 1))
    carts[session_id]["total"] = total
    snapshot = _build_cart_snapshot(session_id)
    return MCPResponse(id=request_id, result={"data": {"cart": snapshot}})