#!/usr/bin/env python3
"""Remote DOM MCP tool handlers"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List
from models import MCPResponse, products, carts, create_ui_resource
from shared.config import UI_THEME

# Get media server URL from environment
MEDIA_SERVER_URL = os.getenv('MEDIA_SERVER_URL', 'http://localhost:3003')

# Theme & styling utilities

# Use centralized theme from shared config
THEME = UI_THEME

def get_theme_js() -> str:
    """Generate JavaScript theme object for components"""
    return f"const THEME = {json.dumps(THEME)};"

def get_common_styles() -> str:
    """Generate common styling utilities in JavaScript"""
    return f"""
{get_theme_js()}

// Common Style Utilities
const createBaseCard = (customStyles = {{}}) => ({{
    width: '100%',
    maxWidth: '420px',
    background: THEME.colors.background,
    backdropFilter: 'blur(20px)',
    border: `1px solid ${{THEME.colors.border}}`,
    borderRadius: THEME.radius.md,
    boxShadow: THEME.shadows.md,
    padding: `${{THEME.spacing.lg}} ${{THEME.spacing.md}}`,
    margin: '0 auto',
    color: THEME.colors.text_primary,
    fontFamily: THEME.typography.font_family,
    ...customStyles
}});

const createButton = (variant = 'primary', customStyles = {{}}) => {{
    const variants = {{
        primary: {{
            background: THEME.colors.accent,
            color: 'white',
            boxShadow: '0 6px 20px rgba(0, 210, 255, 0.25)'
        }},
        secondary: {{
            background: THEME.colors.surface,
            color: THEME.colors.text_primary,
            border: `1px solid ${{THEME.colors.border}}`
        }},
        danger: {{
            background: THEME.colors.danger,
            color: 'white'
        }}
    }};
    
    return {{
        border: 'none',
        padding: `${{THEME.spacing.md}} ${{THEME.spacing.xl}}`,
        borderRadius: THEME.radius.md,
        fontSize: THEME.typography.sizes.base,
        fontWeight: '600',
        cursor: 'pointer',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        ...variants[variant],
        ...customStyles
    }};
}};

const createIconDisplay = (icon, color, size = '48px') => React.createElement('div', {{
    style: {{
        fontSize: size,
        marginBottom: THEME.spacing.md,
        filter: `hue-rotate(${{color === '#FF6B35' ? '15deg' : color === '#4ECDC4' ? '180deg' : '0deg'}})`,
        textAlign: 'center'
    }}
}}, icon);

const handleToolAction = (toolName, params = {{}}) => {{
    window.parent.postMessage({{
        type: 'tool',
        payload: {{
            toolName,
            params
        }}
    }}, '*');
}};
"""

def create_enhanced_component_script(component_script: str, component_name: str) -> str:
    """Create enhanced component script with common utilities and MCP-UI compliance"""
    return f"""
{get_common_styles()}

{component_script}

// Render the component to root element (MCP-UI compliance)
if (typeof root !== 'undefined' && root) {{
    const reactRoot = ReactDOM.createRoot(root);
    reactRoot.render(React.createElement({component_name}));
}}
"""

def create_remote_dom_resource(script: str) -> Dict[str, Any]:
    """Create a remote-dom UI resource"""
    return {
        "type": "remoteDom",
        "script": script,
        "framework": "react"
    }

async def handle_get_products_remote_dom(request_id: str | int, arguments: Dict[str, Any]) -> MCPResponse:
    """Handle get_products with remote-dom - Interactive product navigator"""
    category = arguments.get("category")
    filter_product_id = arguments.get("filter_product_id")
    
    # Filter products by category or specific product ID
    filtered_products = list(products.values())
    if filter_product_id:
        # Filter to single product (for individual jersey views)
        filtered_products = [p for p in products.values() if p.id == filter_product_id]
    elif category:
        # Filter by category (for NBA jerseys collection)
        filtered_products = [p for p in products.values() if p.category == category]
    
    # Create product data for remote-dom
    products_data = []
    for product in filtered_products:
        first_variant = product.variants[0] if product.variants else None
        display_price = product.price + (first_variant.price_modifier if first_variant else 0)
        
        products_data.append({
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": display_price,
            "category": product.category,
            "icon": product.icon,
            "color": product.color,
            "variant_id": first_variant.id if first_variant else "",
            # 🏀 Add jersey image and NBA fields  
            "image_filename": product.image_url.split('/')[-1] if product.image_url else 'placeholder.jpg',
            "highlight_gif": product.highlight_gif,
            "player_stats": product.player_stats
        })

    # Remote DOM script - React component compliant with MCP-UI spec
    script = f"""
// MCP-UI React Remote DOM Component
const products = {json.dumps(products_data)};

function ProductNavigator() {{
    const [currentIndex, setCurrentIndex] = React.useState(0);
    const [product, setProduct] = React.useState(products[0]);
    const [hoveredProduct, setHoveredProduct] = React.useState(null); // 🏀 POC: Add hover state
    const [addingToCart, setAddingToCart] = React.useState(new Set()); // Track optimistic add-to-cart states

    React.useEffect(() => {{
        setProduct(products[currentIndex]);
    }}, [currentIndex]);

    const handleViewDetails = (productId) => {{
        // Use specific jersey tools for main NBA jerseys, or filtered products for others
        let toolName = 'get_product_details';
        let params = {{ product_id: productId }};
        
        // Check if this is an NBA jersey - if so, use unified carousel component
        const nbaJerseys = ['lebron-lakers-jersey', 'jordan-bulls-jersey', 'curry-warriors-jersey', 
                           'giannis-bucks-jersey', 'luka-mavs-jersey', 'tatum-celtics-jersey'];
        
        if (nbaJerseys.includes(productId)) {{
            // For NBA jerseys, use specific tools or filtered carousel
            if (productId === 'lebron-lakers-jersey') {{
                toolName = 'get_lebron_jersey';
                params = {{}};
            }} else if (productId === 'jordan-bulls-jersey') {{
                toolName = 'get_jordan_jersey';
                params = {{}};
            }} else if (productId === 'curry-warriors-jersey') {{
                toolName = 'get_curry_jersey';
                params = {{}};
            }} else if (productId === 'giannis-bucks-jersey') {{
                toolName = 'get_giannis_jersey';
                params = {{}};
            }} else if (productId === 'luka-mavs-jersey') {{
                toolName = 'get_luka_jersey';
                params = {{}};
            }} else if (productId === 'tatum-celtics-jersey') {{
                toolName = 'get_tatum_jersey';
                params = {{}};
            }} else {{
                // Other NBA jerseys use detailed product view
                toolName = 'get_product_details';
                params = {{ product_id: productId }};
            }}
        }}
        
        window.parent.postMessage({{
            type: 'tool',
            payload: {{
                toolName: toolName,
                params: params
            }}
        }}, '*');
    }};

    const handleAddToCart = (productId, variantId) => {{
        if (!variantId) {{
            alert('Please view details to select a variant first');
            return;
        }}
        
        const itemKey = `${{productId}}-${{variantId}}`;
        
        // Optimistic UI update - show "Adding..." state immediately
        setAddingToCart(prev => new Set(prev.add(itemKey)));
        
        window.parent.postMessage({{
            type: 'tool',
            payload: {{
                toolName: 'add_to_cart',
                params: {{ 
                    product_id: productId, 
                    variant_id: variantId,
                    quantity: 1
                }}
            }}
        }}, '*');
        
        // Auto-clear the adding state after a delay (since we don't have promise feedback in this pattern)
        setTimeout(() => {{
            setAddingToCart(prev => {{
                const newSet = new Set(prev);
                newSet.delete(itemKey);
                return newSet;
            }});
        }}, 2000); // Show "Added!" state for 2 seconds
    }};

    const nextProduct = () => {{
        if (currentIndex < products.length - 1) {{
            setCurrentIndex(currentIndex + 1);
        }}
    }};

    const prevProduct = () => {{
        if (currentIndex > 0) {{
            setCurrentIndex(currentIndex - 1);
        }}
    }};

    const goToProduct = (index) => {{
        if (index >= 0 && index < products.length) {{
            setCurrentIndex(index);
        }}
    }};

    if (!product) return React.createElement('div', null, 'Loading...');

    return React.createElement('div', {{
        style: {{
            width: '100%',
            maxWidth: '420px',
            background: 'rgba(45, 45, 50, 0.95)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(70, 70, 80, 0.8)',
            borderRadius: '12px',
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.4)',
            padding: '24px',
            margin: '10px auto',
            color: '#ffffff',
            fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", "Inter", "Segoe UI", system-ui, sans-serif',
            overflow: 'visible'
        }}
    }}, [
        // Header
        React.createElement('div', {{
            style: {{ textAlign: 'center', marginBottom: '12px' }}
        }}, [
            React.createElement('div', {{
                key: 'counter',
                style: {{
                    color: 'rgba(255, 255, 255, 0.6)',
                    fontSize: '0.85rem',
                    fontWeight: '500',
                    marginBottom: '6px'
                }}
            }}, `${{currentIndex + 1}} of ${{products.length}}`),
            React.createElement('div', {{
                key: 'title',
                style: {{
                    background: 'linear-gradient(135deg, #00D2FF 0%, #3A7BD5 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    fontSize: '1.2rem',
                    fontWeight: '600'
                }}
            }}, '')
        ]),

        // Product Display
        React.createElement('div', {{
            key: 'product',
            style: {{ 
                textAlign: 'center', 
                marginBottom: '16px',
                overflow: 'hidden',
                position: 'relative'
            }},
            // 🏀 Add hover events
            onMouseEnter: () => setHoveredProduct(product.id),
            onMouseLeave: () => setHoveredProduct(null)
        }}, [
            // Product Jersey/GIF Container with Price Tag Overlay
            React.createElement('div', {{
                key: 'visual-container',
                style: {{
                    width: '200px',
                    height: '200px',
                    borderRadius: '12px',
                    margin: '0 auto 12px',
                    position: 'relative',
                    overflow: 'hidden',
                    boxShadow: '0 10px 30px rgba(0, 0, 0, 0.4)',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                }}
            }}, [
                // Default state: Jersey Image
                React.createElement('img', {{
                    key: 'jersey-image',
                    src: '{MEDIA_SERVER_URL}/media/' + product.image_filename,
                    alt: `${{product.name}} jersey`,
                    style: {{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                        borderRadius: '12px',
                        transition: 'opacity 0.3s ease',
                        opacity: hoveredProduct === product.id ? 0.2 : 1,
                        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
                    }},
                    onError: (e) => {{
                        // Fallback to emoji if image fails to load
                        e.target.style.display = 'none';
                        const fallback = e.target.nextSibling;
                        if (fallback) fallback.style.display = 'flex';
                    }}
                }}),
                
                // Fallback emoji (hidden by default)
                React.createElement('div', {{
                    key: 'fallback-icon',
                    style: {{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        height: '100%',
                        display: 'none',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '2.5rem',
                        color: 'white',
                        background: `linear-gradient(135deg, ${{product.color}} 0%, rgba(255,255,255,0.1) 100%)`,
                        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
                        borderRadius: '12px',
                        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                        opacity: hoveredProduct === product.id ? 0.3 : 1
                    }}
                }}, product.icon),
                
                // 🏀 Hover state: Highlight GIF
                product.highlight_gif ? React.createElement('img', {{
                    key: 'highlight-gif',
                    src: '{MEDIA_SERVER_URL}/media/' + product.highlight_gif,
                    alt: `${{product.name}} highlight`,
                    style: {{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                        borderRadius: '12px',
                        opacity: hoveredProduct === product.id ? 0.9 : 0,
                        transition: 'opacity 0.4s ease',
                        pointerEvents: 'none',
                        zIndex: 2
                    }},
                    onError: (e) => {{
                        console.warn('GIF loading failed for:', product.highlight_gif);
                        e.target.style.display = 'none';
                    }}
                }}) : null,
                
                // Price Tag Overlay (top-left corner)
                React.createElement('div', {{
                    key: 'price-tag',
                    style: {{
                        position: 'absolute',
                        top: '8px',
                        left: '8px',
                        background: 'linear-gradient(135deg, #00D2FF 0%, #3A7BD5 100%)',
                        color: 'white',
                        padding: '4px 8px',
                        borderRadius: '6px',
                        fontSize: '0.8rem',
                        fontWeight: '700',
                        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
                        zIndex: 3,
                        letterSpacing: '-0.01em'
                    }}
                }}, `$${{product.price.toFixed(2)}}`)
            ]),
            

            
            // Product Name
            React.createElement('div', {{
                key: 'name',
                style: {{
                    color: '#ffffff',
                    fontSize: '1.1rem',
                    fontWeight: '700',
                    marginBottom: '8px',
                    letterSpacing: '-0.02em'
                }}
            }}, product.name),
            
            // Product Description - Hidden to save space for buttons
            // React.createElement('div', {{
            //     key: 'description',
            //     style: {{
            //         color: 'rgba(255, 255, 255, 0.7)',
            //         fontSize: '0.8rem',
            //         lineHeight: '1.4',
            //         marginBottom: '8px',
            //         padding: '0 12px'
            //     }}
            // }}, product.description.substring(0, 100) + '...'),
            
            // Price and Category removed - Price is now overlay on image
        ]),

        // Action Buttons
        React.createElement('div', {{
            key: 'actions',
            style: {{
                display: 'flex',
                gap: '6px',
                marginBottom: '16px',
                padding: '0 12px'
            }}
        }}, [
            React.createElement('button', {{
                key: 'details',
                onClick: () => handleViewDetails(product.id),
                style: {{
                    flex: '1',
                    padding: '8px 8px',
                    border: '1px solid rgba(100, 100, 105, 0.8)',
                    borderRadius: '8px',
                    background: 'rgba(80, 80, 85, 0.8)',
                    color: 'rgba(255, 255, 255, 0.9)',
                    fontSize: '0.85rem',
                    fontWeight: '600',
                    cursor: 'pointer',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                }},
                onMouseEnter: (e) => {{
                    e.target.style.background = 'rgba(100, 100, 105, 0.9)';
                    e.target.style.borderColor = 'rgba(0, 210, 255, 0.4)';
                }},
                onMouseLeave: (e) => {{
                    e.target.style.background = 'rgba(80, 80, 85, 0.8)';
                    e.target.style.borderColor = 'rgba(100, 100, 105, 0.8)';
                }}
            }}, 'View Details'),
            
            React.createElement('button', {{
                key: 'add',
                onClick: () => handleAddToCart(product.id, product.variant_id),
                style: {{
                    flex: '1',
                    padding: '8px 8px',
                    border: '1px solid rgba(0, 210, 255, 0.3)',
                    borderRadius: '8px',
                    background: 'linear-gradient(135deg, #00D2FF 0%, #3A7BD5 100%)',
                    color: 'white',
                    fontSize: '0.85rem',
                    fontWeight: '600',
                    cursor: 'pointer',
                    boxShadow: '0 4px 12px rgba(0, 210, 255, 0.25)',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                }},
                onMouseEnter: (e) => {{
                    e.target.style.transform = 'translateY(-2px) scale(1.02)';
                    e.target.style.boxShadow = '0 8px 20px rgba(0, 210, 255, 0.35)';
                }},
                onMouseLeave: (e) => {{
                    e.target.style.transform = 'translateY(0) scale(1)';
                    e.target.style.boxShadow = '0 4px 12px rgba(0, 210, 255, 0.25)';
                }}
            }}, addingToCart.has(`${{product.id}}-${{product.variant_id}}`) ? '✓ Added!' : 'Add to Cart')
        ]),

        // Navigation
        React.createElement('div', {{
            key: 'navigation',
            style: {{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px'
            }}
        }}, [
            // Previous Button
            React.createElement('button', {{
                key: 'prev',
                onClick: prevProduct,
                disabled: currentIndex === 0,
                style: {{
                    width: '32px',
                    height: '32px',
                    border: '1px solid rgba(100, 100, 105, 0.8)',
                    borderRadius: '8px',
                    background: currentIndex === 0 ? 'rgba(60, 60, 65, 0.3)' : 'rgba(80, 80, 85, 0.8)',
                    color: currentIndex === 0 ? 'rgba(255, 255, 255, 0.3)' : 'rgba(255, 255, 255, 0.8)',
                    fontSize: '1.2rem',
                    fontWeight: '600',
                    cursor: currentIndex === 0 ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                }}
            }}, '‹'),
            
            // Dots
            React.createElement('div', {{
                key: 'dots',
                style: {{
                    display: 'flex',
                    gap: '4px'
                }}
            }}, products.map((_, index) => 
                React.createElement('div', {{
                    key: `nav-dot-${{index}}`,
                    onClick: () => goToProduct(index),
                    style: {{
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        background: index === currentIndex ? 
                            'linear-gradient(135deg, #00D2FF 0%, #3A7BD5 100%)' : 
                            'rgba(255, 255, 255, 0.3)',
                        cursor: 'pointer',
                        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                        transform: index === currentIndex ? 'scale(1.2)' : 'scale(1)',
                        boxShadow: index === currentIndex ? '0 2px 6px rgba(0, 210, 255, 0.4)' : 'none'
                    }}
                }})
            )),
            
            // Next Button
            React.createElement('button', {{
                key: 'next',
                onClick: nextProduct,
                disabled: currentIndex === products.length - 1,
                style: {{
                    width: '32px',
                    height: '32px',
                    border: '1px solid rgba(100, 100, 105, 0.8)',
                    borderRadius: '8px',
                    background: currentIndex === products.length - 1 ? 'rgba(60, 60, 65, 0.3)' : 'rgba(80, 80, 85, 0.8)',
                    color: currentIndex === products.length - 1 ? 'rgba(255, 255, 255, 0.3)' : 'rgba(255, 255, 255, 0.8)',
                    fontSize: '1.2rem',
                    fontWeight: '600',
                    cursor: currentIndex === products.length - 1 ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                }}
            }}, '›')
        ])
    ]);
}}

// Render the component to root element (MCP-UI compliance)
if (typeof root !== 'undefined' && root) {{
    const reactRoot = ReactDOM.createRoot(root);
    reactRoot.render(React.createElement(ProductNavigator));
}}
"""

    ui_resource = create_ui_resource(
        content_type="remoteDom", 
        content=script
    )
    
    return MCPResponse(
        id=request_id,
        result={"content": [ui_resource]}
    )

async def handle_process_checkout_remote_dom(request_id: str | int, session_id: str, arguments: Dict[str, Any]) -> MCPResponse:
    """Handle process_checkout with remote-dom - Process order and show confirmation"""
    
    # Get cart to process
    cart = carts.get(session_id, {"items": [], "total": 0.0})
    
    if not cart["items"]:
        return MCPResponse(
            id=request_id,
            error={"code": -32602, "message": "Cannot checkout with empty cart"}
        )
    
    # Extract form data
    name = arguments.get("name", "")
    email = arguments.get("email", "")  
    address = arguments.get("address", "")
    payment_method = arguments.get("payment_method", "credit_card")
    
    if not all([name, email, address]):
        return MCPResponse(
            id=request_id,
            error={"code": -32602, "message": "Missing required fields: name, email, address"}
        )
    
    # Generate mock order ID
    import time
    order_id = f"ORD-{int(time.time())}"
    order_total = cart["total"]
    
    # Process the order (in real app, would integrate with payment processor)
    order_summary = []
    for item in cart["items"]:
        product = products.get(item["product_id"])
        variant = next((v for v in product.variants if v.id == item["variant_id"]), None) if product else None
        
        if product and variant:
            item_price = product.price + variant.price_modifier
            total_item_price = item_price * item["quantity"]
            order_summary.append({
                "name": product.name,
                "variant": variant.name,
                "quantity": item["quantity"],
                "price": item_price,
                "total": total_item_price
            })
    
    # Clear the cart after successful order
    carts[session_id] = {"items": [], "total": 0.0}
    
    # Create order confirmation React component
    script = f"""
function OrderConfirmation({{ onAction }}) {{
    const orderData = {{
        orderId: '{order_id}',
        customerName: '{name}',
        customerEmail: '{email}',
        customerAddress: '{address}',
        paymentMethod: '{payment_method}',
        items: {json.dumps(order_summary)},
        total: {order_total}
    }};
    
    const handleContinueShopping = () => {{
        onAction({{
            type: 'tool',
            payload: {{
                toolName: 'get_products',
                params: {{}}
            }}
        }});
    }};

    return React.createElement('div', {{
        style: {{
            width: '100%',
            maxWidth: '450px',
            background: 'rgba(45, 45, 50, 0.95)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(70, 70, 80, 0.8)',
            borderRadius: '12px',
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.4)',
            overflow: 'hidden',
            margin: '0 auto',
            color: '#ffffff',
            fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", "Inter", "Segoe UI", system-ui, sans-serif'
        }}
    }}, [
        // Success Header
        React.createElement('div', {{
            key: 'header',
            style: {{
                background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)',
                color: 'white',
                padding: '30px',
                textAlign: 'center'
            }}
        }}, [
            React.createElement('div', {{
                key: 'icon',
                style: {{
                    fontSize: '4rem',
                    marginBottom: '16px'
                }}
            }}, '✅'),
            React.createElement('h1', {{
                key: 'title',
                style: {{
                    fontSize: '2.2rem',
                    fontWeight: '700',
                    marginBottom: '8px'
                }}
            }}, 'Order Confirmed!'),
            React.createElement('p', {{
                key: 'subtitle',
                style: {{
                    fontSize: '1.1rem',
                    opacity: '0.9'
                }}
            }}, `Order #${{orderData.orderId}}`)
        ]),

        // Order Details
        React.createElement('div', {{
            key: 'content',
            style: {{ padding: '30px' }}
        }}, [
            // Customer Info
            React.createElement('div', {{
                key: 'customer-info',
                style: {{
                    background: 'rgba(80, 80, 85, 0.8)',
                    borderRadius: '12px',
                    padding: '20px',
                    marginBottom: '24px'
                }}
            }}, [
                React.createElement('h3', {{
                    key: 'title',
                    style: {{
                        color: '#ffffff',
                        fontSize: '1.2rem',
                        fontWeight: '600',
                        marginBottom: '16px'
                    }}
                }}, 'Shipping Details'),
                React.createElement('div', {{
                    key: 'name',
                    style: {{
                        color: 'rgba(255, 255, 255, 0.9)',
                        marginBottom: '8px'
                    }}
                }}, `📧 ${{orderData.customerName}}`),
                React.createElement('div', {{
                    key: 'email', 
                    style: {{
                        color: 'rgba(255, 255, 255, 0.9)',
                        marginBottom: '8px'
                    }}
                }}, `✉️ ${{orderData.customerEmail}}`),
                React.createElement('div', {{
                    key: 'address',
                    style: {{
                        color: 'rgba(255, 255, 255, 0.9)',
                        marginBottom: '8px'
                    }}
                }}, `📍 ${{orderData.customerAddress}}`),
                React.createElement('div', {{
                    key: 'payment',
                    style: {{
                        color: 'rgba(255, 255, 255, 0.9)'
                    }}
                }}, `💳 ${{orderData.paymentMethod.replace('_', ' ').toUpperCase()}}`)
            ]),
            
            // Order Items
            React.createElement('div', {{
                key: 'order-items',
                style: {{
                    background: 'rgba(80, 80, 85, 0.8)',
                    borderRadius: '12px',
                    padding: '20px',
                    marginBottom: '24px'
                }}
            }}, [
                React.createElement('h3', {{
                    key: 'title',
                    style: {{
                        color: '#ffffff',
                        fontSize: '1.2rem',
                        fontWeight: '600',
                        marginBottom: '16px'
                    }}
                }}, 'Order Summary'),
                
                // Items
                ...orderData.items.map((item, index) =>
                    React.createElement('div', {{
                        key: index,
                        style: {{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            padding: '10px 0',
                            borderBottom: index < orderData.items.length - 1 ? '1px solid rgba(100, 100, 105, 0.6)' : 'none'
                        }}
                    }}, [
                        React.createElement('div', {{
                            key: 'info'
                        }}, [
                            React.createElement('div', {{
                                key: 'name',
                                style: {{
                                    color: '#ffffff',
                                    fontWeight: '600',
                                    marginBottom: '2px'
                                }}
                            }}, item.name),
                            React.createElement('div', {{
                                key: 'details',
                                style: {{
                                    color: 'rgba(255, 255, 255, 0.7)',
                                    fontSize: '0.9rem'
                                }}
                            }}, `${{item.variant}} × ${{item.quantity}}`)
                        ]),
                        React.createElement('div', {{
                            key: 'price',
                            style: {{
                                color: '#ffffff',
                                fontWeight: '600'
                            }}
                        }}, `$${{item.total.toFixed(2)}}`)
                    ])
                ),
                
                // Total
                React.createElement('div', {{
                    key: 'total',
                    style: {{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginTop: '16px',
                        paddingTop: '16px',
                        borderTop: '2px solid rgba(100, 100, 105, 0.6)',
                        fontSize: '1.3rem',
                        fontWeight: '700',
                        color: '#ffffff'
                    }}
                }}, [
                    React.createElement('span', {{ key: 'label' }}, 'Total Paid:'),
                    React.createElement('span', {{ 
                        key: 'amount',
                        style: {{
                            color: '#22c55e'
                        }}
                    }}, `$${{orderData.total.toFixed(2)}}`)
                ])
            ]),
            
            // Next Steps
            React.createElement('div', {{
                key: 'next-steps',
                style: {{
                    background: 'rgba(34, 197, 94, 0.15)',
                    border: '1px solid rgba(34, 197, 94, 0.3)',
                    borderRadius: '12px',
                    padding: '20px',
                    marginBottom: '24px'
                }}
            }}, [
                React.createElement('h3', {{
                    key: 'title',
                    style: {{
                        color: '#22c55e',
                        fontSize: '1.1rem',
                        fontWeight: '600',
                        marginBottom: '12px'
                    }}
                }}, 'What happens next?'),
                React.createElement('ul', {{
                    key: 'steps',
                    style: {{
                        color: 'rgba(255, 255, 255, 0.9)',
                        paddingLeft: '20px',
                        lineHeight: '1.6'
                    }}
                }}, [
                    React.createElement('li', {{ key: '1' }}, 'Order confirmation email sent to your inbox'),
                    React.createElement('li', {{ key: '2' }}, 'Items will be packed and shipped within 24 hours'),
                    React.createElement('li', {{ key: '3' }}, 'You\\'ll receive tracking information once shipped')
                ])
            ]),
            
            // Continue Shopping Button
            React.createElement('div', {{
                key: 'actions',
                style: {{ textAlign: 'center' }}
            }}, React.createElement('button', {{
                onClick: handleContinueShopping,
                style: {{
                    background: 'linear-gradient(135deg, #00D2FF 0%, #3A7BD5 100%)',
                    color: 'white',
                    border: 'none',
                    padding: '16px 32px',
                    borderRadius: '12px',
                    fontSize: '1rem',
                    fontWeight: '600',
                    cursor: 'pointer',
                    boxShadow: '0 6px 20px rgba(0, 210, 255, 0.25)',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                }},
                onMouseEnter: (e) => {{
                    e.target.style.transform = 'translateY(-2px) scale(1.02)';
                    e.target.style.boxShadow = '0 12px 32px rgba(0, 210, 255, 0.35)';
                }},
                onMouseLeave: (e) => {{
                    e.target.style.transform = 'translateY(0) scale(1)';
                    e.target.style.boxShadow = '0 6px 20px rgba(0, 210, 255, 0.25)';
                }}
            }}, 'Continue Shopping'))
        ])
    ]);
}}
"""

    ui_resource = create_ui_resource(
        content_type="remoteDom",
        content=script
    )
    
    return MCPResponse(
        id=request_id,
        result={"content": [ui_resource]}
    )

async def handle_get_product_details_remote_dom(request_id: str | int, arguments: Dict[str, Any]) -> MCPResponse:
    """Handle get_product_details with remote-dom"""
    product_id = arguments.get("product_id")
    product = products.get(product_id)
    if not product:
        return MCPResponse(
            id=request_id,
            error={"code": -32602, "message": f"Product not found: {product_id}"}
        )
    
    # Extract data for remote-dom including NBA jersey fields
    product_data = {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "icon": product.icon,
        "color": product.color,
        "variant_id": product.variants[0].id if product.variants else "",
        "image_url": product.image_url,
        "category": product.category,
        "highlight_gif": product.highlight_gif,
        "player_stats": product.player_stats
    }

    script = f"""
function ProductDetails() {{
    const product = {json.dumps(product_data)};
    const [isHovered, setIsHovered] = React.useState(false);
    const [addingToCart, setAddingToCart] = React.useState(false); // Track optimistic add-to-cart state

    const handleAddToCart = () => {{
        // Optimistic UI update - show "Adding..." state immediately
        setAddingToCart(true);
        
        window.parent.postMessage({{
            type: 'tool',
            payload: {{
                toolName: 'add_to_cart',
                params: {{ 
                    product_id: product.id,
                    variant_id: product.variant_id,
                    quantity: 1
                }}
            }}
        }}, '*');
        
        // Auto-clear the adding state after a delay
        setTimeout(() => {{
            setAddingToCart(false);
        }}, 2000); // Show "Added!" state for 2 seconds
    }};

    const handleGoBack = () => {{
        window.parent.postMessage({{
            type: 'tool',
            payload: {{
                toolName: 'get_products',
                params: {{}}
            }}
        }}, '*');
    }};

    return React.createElement('div', {{
        style: {{
            width: '100%',
            maxWidth: '360px',
            maxHeight: '90vh',
            overflow: 'auto',
            background: 'rgba(45, 45, 50, 0.95)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(70, 70, 80, 0.8)',
            borderRadius: '12px',
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.4)',
            padding: '24px 20px',
            margin: '0 auto',
            color: '#ffffff',
            fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", "Inter", "Segoe UI", system-ui, sans-serif',
            textAlign: 'center'
        }}
    }}, [
        // Jersey Image Container with hover effects
        React.createElement('div', {{
            key: 'image-container',
            style: {{
                width: '200px',
                height: '200px',
                borderRadius: '12px',
                margin: '0 auto 16px',
                position: 'relative',
                overflow: 'hidden',
                boxShadow: '0 10px 30px rgba(0, 0, 0, 0.4)',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
            }},
            onMouseEnter: () => setIsHovered(true),
            onMouseLeave: () => setIsHovered(false)
        }}, [
            // Default state: Jersey Image
            React.createElement('img', {{
                key: 'jersey-image',
                src: product.image_url,
                alt: `${{product.name}} jersey`,
                style: {{
                    width: '100%',
                    height: '100%',
                    objectFit: 'contain',
                    borderRadius: '12px',
                    transition: 'opacity 0.3s ease',
                    opacity: isHovered ? 0.2 : 1,
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
                }},
                onError: (e) => {{
                    // Fallback to emoji if image fails to load
                    e.target.style.display = 'none';
                    const fallback = e.target.nextSibling;
                    if (fallback) fallback.style.display = 'flex';
                }}
            }}),
            
            // Fallback emoji (hidden by default)
            React.createElement('div', {{
                key: 'fallback-icon',
                style: {{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    display: 'none',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '2.5rem',
                    color: 'white',
                    background: `linear-gradient(135deg, ${{product.color}} 0%, rgba(255,255,255,0.1) 100%)`,
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
                    borderRadius: '12px',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    opacity: isHovered ? 0.3 : 1
                }}
            }}, product.icon),
            
            // Hover state: Highlight GIF (NBA jerseys only)
            product.category === 'nba-jerseys' && product.highlight_gif ? React.createElement('img', {{
                key: 'highlight-gif',
                src: '{MEDIA_SERVER_URL}/media/' + product.highlight_gif,
                alt: `${{product.name}} highlight`,
                style: {{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    objectFit: 'contain',
                    borderRadius: '12px',
                    opacity: isHovered ? 0.9 : 0,
                    transition: 'opacity 0.4s ease',
                    pointerEvents: 'none',
                    zIndex: 2
                }},
                onError: (e) => {{
                    console.warn('GIF loading failed for:', product.highlight_gif);
                    e.target.style.display = 'none';
                }}
            }}) : null
        ]),
        
        // Product Name
        React.createElement('h2', {{
            key: 'name',
            style: {{
                color: '#ffffff',
                fontSize: '1.25rem',
                fontWeight: '700',
                marginBottom: '8px',
                letterSpacing: '-0.02em'
            }}
        }}, product.name),
        
        // Product Description
        React.createElement('p', {{
            key: 'description',
            style: {{
                color: 'rgba(255, 255, 255, 0.7)',
                fontSize: '0.875rem',
                lineHeight: '1.4',
                marginBottom: '16px',
                maxWidth: '300px',
                margin: '0 auto 16px'
            }}
        }}, product.description.length > 150 ? product.description.substring(0, 150) + '...' : product.description),
        
        // Player Stats (NBA Jerseys only)
        product.category === 'nba-jerseys' && product.player_stats ? React.createElement('div', {{
            key: 'player-stats',
            style: {{
                background: 'rgba(255, 215, 0, 0.1)',
                border: '1px solid rgba(255, 215, 0, 0.3)',
                borderRadius: '8px',
                padding: '8px 12px',
                margin: '0 auto 16px',
                maxWidth: '300px'
            }}
        }}, [
            React.createElement('div', {{
                key: 'stats-icon',
                style: {{
                    fontSize: '0.75rem',
                    color: '#FFD700',
                    fontWeight: '600',
                    marginBottom: '4px'
                }}
            }}, '🏆 ACHIEVEMENTS'),
            React.createElement('div', {{
                key: 'stats-text',
                style: {{
                    color: '#FFD700',
                    fontSize: '0.8rem',
                    fontWeight: '500'
                }}
            }}, product.player_stats)
        ]) : null,
        
        // Product Price
        React.createElement('div', {{
            key: 'price',
            style: {{
                background: 'linear-gradient(135deg, #00D2FF 0%, #3A7BD5 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                fontSize: '1.5rem',
                fontWeight: '800',
                marginBottom: '20px',
                letterSpacing: '-0.02em'
            }}
        }}, `$${{product.price.toFixed(2)}}`),
        
        // Action Buttons
        React.createElement('div', {{
            key: 'actions',
            style: {{
                display: 'flex',
                gap: '12px',
                justifyContent: 'center'
            }}
        }}, [
            React.createElement('button', {{
                key: 'back',
                onClick: handleGoBack,
                style: {{
                    padding: '12px 16px',
                    border: '1px solid rgba(100, 100, 105, 0.8)',
                    borderRadius: '8px',
                    background: 'rgba(80, 80, 85, 0.8)',
                    color: 'rgba(255, 255, 255, 0.9)',
                    fontSize: '0.9rem',
                    fontWeight: '600',
                    cursor: 'pointer',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                }},
                onMouseEnter: (e) => {{
                    e.target.style.background = 'rgba(100, 100, 105, 0.9)';
                    e.target.style.borderColor = 'rgba(0, 210, 255, 0.4)';
                }},
                onMouseLeave: (e) => {{
                    e.target.style.background = 'rgba(80, 80, 85, 0.8)';
                    e.target.style.borderColor = 'rgba(100, 100, 105, 0.8)';
                }}
            }}, '← Back'),
            
            React.createElement('button', {{
                key: 'add',
                onClick: handleAddToCart,
                style: {{
                    padding: '12px 20px',
                    border: '1px solid rgba(0, 210, 255, 0.3)',
                    borderRadius: '8px',
                    background: 'linear-gradient(135deg, #00D2FF 0%, #3A7BD5 100%)',
                    color: 'white',
                    fontSize: '0.9rem',
                    fontWeight: '600',
                    cursor: 'pointer',
                    boxShadow: '0 6px 16px rgba(0, 210, 255, 0.25)',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                }},
                onMouseEnter: (e) => {{
                    e.target.style.transform = 'translateY(-2px) scale(1.02)';
                    e.target.style.boxShadow = '0 10px 24px rgba(0, 210, 255, 0.35)';
                }},
                onMouseLeave: (e) => {{
                    e.target.style.transform = 'translateY(0) scale(1)';
                    e.target.style.boxShadow = '0 6px 16px rgba(0, 210, 255, 0.25)';
                }}
            }}, addingToCart ? '✓ Added!' : 'Add to Cart')
        ])
    ]);
}}

// Render the component to root element (MCP-UI compliance)
if (typeof root !== 'undefined' && root) {{
    const reactRoot = ReactDOM.createRoot(root);
    reactRoot.render(React.createElement(ProductDetails));
}}
"""

    ui_resource = create_ui_resource(
        content_type="remoteDom",
        content=script
    )
    
    return MCPResponse(
        id=request_id,
        result={"content": [ui_resource]}
    )

async def handle_add_to_cart_remote_dom(request_id: str | int, arguments: Dict[str, Any], session_id: str) -> MCPResponse:
    """Handle add_to_cart with remote-dom - adds item AND returns success UI"""
    product_id = arguments.get("product_id")
    variant_id = arguments.get("variant_id") 
    quantity = arguments.get("quantity", 1)
    
    # Add to server-side cart (same logic as HTML version)
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
            "added_at": "2024-01-01T00:00:00Z"
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

    # Build cart snapshot for clients to mirror state
    snapshot = _build_cart_snapshot(session_id)

    # Create success remote-dom component
    script = """
function AddToCartSuccess({ onAction }) {
    const handleContinueShopping = () => {
        onAction({
            type: 'tool',
            payload: {
                toolName: 'get_products',
                params: {}
            }
        });
    };

    const handleViewCart = () => {
        onAction({
            type: 'ui-action',
            payload: {
                action: 'toggle-cart'
            }
        });
    };

    return React.createElement('div', {
        style: {
            width: '100%',
            maxWidth: '380px',
            background: 'rgba(45, 45, 50, 0.95)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(70, 70, 80, 0.8)',
            borderRadius: '12px',
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.4)',
            padding: '24px 20px',
            margin: '0 auto',
            color: '#ffffff',
            fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", "Inter", "Segoe UI", system-ui, sans-serif',
            textAlign: 'center'
        }
    }, [
        // Success Icon
        React.createElement('div', {
            key: 'icon',
            style: {
                width: '60px',
                height: '60px',
                margin: '0 auto 16px',
                background: 'linear-gradient(135deg, #22C55E 0%, #16A34A 100%)',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.5rem',
                boxShadow: '0 6px 20px rgba(34, 197, 94, 0.3)',
                animation: 'successBounce 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55)'
            }
        }, '✅'),
        
        // Success Title
        React.createElement('h1', {
            key: 'title',
            style: {
                color: '#ffffff',
                fontSize: '1.5rem',
                fontWeight: '700',
                marginBottom: '12px',
                letterSpacing: '-0.02em'
            }
        }, 'Added to Cart!'),
        
        // Success Message
        React.createElement('p', {
            key: 'message',
            style: {
                color: 'rgba(255, 255, 255, 0.8)',
                fontSize: '1rem',
                lineHeight: '1.5',
                marginBottom: '20px'
            }
        }, 'Item has been added to your cart successfully.'),
        
        // Cart Indicator
        React.createElement('div', {
            key: 'indicator',
            style: {
                background: 'rgba(34, 197, 94, 0.15)',
                border: '1px solid rgba(34, 197, 94, 0.3)',
                borderRadius: '12px',
                padding: '12px 16px',
                marginBottom: '24px',
                fontSize: '0.875rem',
                color: '#22C55E',
                fontWeight: '500'
            }
        }, '🛒 Item is now in your cart'),
        
        // Action Buttons
        React.createElement('div', {
            key: 'actions',
            style: {
                display: 'flex',
                flexDirection: 'column',
                gap: '12px'
            }
        }, [
            React.createElement('button', {
                key: 'continue',
                onClick: handleContinueShopping,
                style: {
                    background: 'linear-gradient(135deg, #00D2FF 0%, #3A7BD5 100%)',
                    color: 'white',
                    border: '1px solid rgba(0, 210, 255, 0.3)',
                    padding: '14px 28px',
                    borderRadius: '12px',
                    fontSize: '0.9375rem',
                    fontWeight: '600',
                    cursor: 'pointer',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    boxShadow: '0 6px 20px rgba(0, 210, 255, 0.25)',
                    letterSpacing: '-0.01em'
                },
                onMouseEnter: (e) => {
                    e.target.style.transform = 'translateY(-2px) scale(1.02)';
                    e.target.style.boxShadow = '0 12px 32px rgba(0, 210, 255, 0.35)';
                },
                onMouseLeave: (e) => {
                    e.target.style.transform = 'translateY(0) scale(1)';
                    e.target.style.boxShadow = '0 6px 20px rgba(0, 210, 255, 0.25)';
                }
            }, 'Continue Shopping'),
            
            React.createElement('button', {
                key: 'view-cart',
                onClick: handleViewCart,
                style: {
                    background: 'rgba(80, 80, 85, 0.8)',
                    color: 'rgba(255, 255, 255, 0.9)',
                    border: '1px solid rgba(100, 100, 105, 0.8)',
                    padding: '12px 28px',
                    borderRadius: '12px',
                    fontSize: '0.9375rem',
                    fontWeight: '600',
                    cursor: 'pointer',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    letterSpacing: '-0.01em'
                },
                onMouseEnter: (e) => {
                    e.target.style.background = 'rgba(100, 100, 105, 0.9)';
                    e.target.style.borderColor = 'rgba(0, 210, 255, 0.3)';
                    e.target.style.transform = 'translateY(-1px)';
                },
                onMouseLeave: (e) => {
                    e.target.style.background = 'rgba(80, 80, 85, 0.8)';
                    e.target.style.borderColor = 'rgba(100, 100, 105, 0.8)';
                    e.target.style.transform = 'translateY(0)';
                }
            }, 'View Cart')
        ])
    ]);
}

// Render the component to root element (MCP-UI compliance)
if (typeof root !== 'undefined' && root) {
    const reactRoot = ReactDOM.createRoot(root);
    reactRoot.render(React.createElement(AddToCartSuccess));
}
"""

    ui_resource = create_ui_resource(
        content_type="remoteDom",
        content=script
    )
    
    return MCPResponse(
        id=request_id,
        result={
            "content": [ui_resource],
            "data": {"cart": snapshot}
        }
    )

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
    normalized_items: List[Dict[str, Any]] = []
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

async def handle_get_cart_remote_dom(request_id: str | int, session_id: str) -> MCPResponse:
    """Handle get_cart with remote-dom - Interactive cart display"""
    
    # Get cart or create empty one
    cart = carts.get(session_id, {"items": [], "total": 0.0})
    
    if not cart["items"]:
        # Empty cart React component
        script = """
function EmptyCart({ onAction }) {
    const handleStartShopping = () => {
        onAction({
            type: 'tool',
            payload: {
                toolName: 'get_products',
                params: {}
            }
        });
    };

    return React.createElement('div', {
        style: {
            width: '100%',
            maxWidth: '500px',
            background: 'rgba(45, 45, 50, 0.95)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(70, 70, 80, 0.8)',
            borderRadius: '12px',
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.4)',
            padding: '40px 20px',
            margin: '0 auto',
            color: '#ffffff',
            fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", "Inter", "Segoe UI", system-ui, sans-serif',
            textAlign: 'center'
        }
    }, [
        // Empty Cart Icon
        React.createElement('div', {
            key: 'icon',
            style: {
                fontSize: '5rem',
                marginBottom: '20px',
                opacity: '0.5'
            }
        }, '🛒'),
        
        // Empty Title
        React.createElement('h1', {
            key: 'title',
            style: {
                color: '#ffffff',
                fontSize: '1.8rem',
                fontWeight: '700',
                marginBottom: '12px'
            }
        }, 'Your Cart is Empty'),
        
        // Empty Message
        React.createElement('p', {
            key: 'message',
            style: {
                color: 'rgba(255, 255, 255, 0.8)',
                fontSize: '1.1rem',
                marginBottom: '30px'
            }
        }, 'Start shopping to add items to your cart!'),
        
        // Start Shopping Button
        React.createElement('button', {
            key: 'button',
            onClick: handleStartShopping,
            style: {
                background: 'linear-gradient(135deg, #00D2FF 0%, #3A7BD5 100%)',
                color: 'white',
                padding: '12px 24px',
                border: 'none',
                borderRadius: '8px',
                fontWeight: '600',
                fontSize: '1rem',
                cursor: 'pointer',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                boxShadow: '0 4px 12px rgba(0, 210, 255, 0.4)'
            },
            onMouseEnter: (e) => {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 6px 16px rgba(0, 210, 255, 0.5)';
            },
            onMouseLeave: (e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 4px 12px rgba(0, 210, 255, 0.4)';
            }
        }, 'Browse Products')
    ]);
}
"""
    else:
        # Cart with items - prepare data for React
        cart_items_data = []
        for item in cart["items"]:
            product = products.get(item["product_id"])
            variant = next((v for v in product.variants if v.id == item["variant_id"]), None) if product else None
            
            if product and variant:
                item_price = product.price + variant.price_modifier
                total_item_price = item_price * item["quantity"]
                
                cart_items_data.append({
                    "product_id": product.id,
                    "variant_id": variant.id,
                    "name": product.name,
                    "variant": variant.name,
                    "price": item_price,
                    "quantity": item["quantity"],
                    "total": total_item_price,
                    "image_url": getattr(variant, 'image_url', None) or product.image_url
                })

        # Cart with items React component
        script = f"""
function CartDisplay({{ onAction }}) {{
    const cartItems = {json.dumps(cart_items_data)};
    const cartTotal = {cart["total"]};
    
    const updateQuantity = (productId, variantId, change) => {{
        const item = cartItems.find(i => i.product_id === productId && i.variant_id === variantId);
        if (item) {{
            const newQuantity = Math.max(0, item.quantity + change);
            onAction({{
                type: 'tool',
                payload: {{
                    toolName: 'set_cart_quantity',
                    params: {{ 
                        product_id: productId,
                        variant_id: variantId,
                        quantity: newQuantity,
                        session_id: '{session_id}'
                    }}
                }}
            }});
        }}
    }};
    
    const removeItem = (productId, variantId) => {{
        onAction({{
            type: 'tool',
            payload: {{
                toolName: 'remove_from_cart',
                params: {{ 
                    product_id: productId,
                    variant_id: variantId,
                    session_id: 'default'
                }}
            }}
        }});
    }};

    const handleCheckout = () => {{
        onAction({{
            type: 'tool',
            payload: {{
                toolName: 'checkout',
                params: {{
                    session_id: 'default'
                }}
            }}
        }});
    }};

    const handleContinueShopping = () => {{
        onAction({{
            type: 'tool',
            payload: {{
                toolName: 'get_products',
                params: {{}}
            }}
        }});
    }};

    return React.createElement('div', {{
        style: {{
            width: '100%',
            maxWidth: '800px',
            background: 'rgba(45, 45, 50, 0.95)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(70, 70, 80, 0.8)',
            borderRadius: '12px',
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.4)',
            overflow: 'hidden',
            margin: '0 auto',
            color: '#ffffff',
            fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", "Inter", "Segoe UI", system-ui, sans-serif'
        }}
    }}, [
        // Cart Header
        React.createElement('div', {{
            key: 'header',
            style: {{
                background: 'linear-gradient(135deg, #00D2FF 0%, #3A7BD5 100%)',
                color: 'white',
                padding: '24px 30px',
                textAlign: 'center'
            }}
        }}, [
            React.createElement('h1', {{
                key: 'title',
                style: {{
                    fontSize: '2rem',
                    fontWeight: '700',
                    marginBottom: '8px'
                }}
            }}, 'Your Cart'),
            React.createElement('p', {{
                key: 'subtitle',
                style: {{
                    fontSize: '1rem',
                    opacity: '0.9'
                }}
            }}, `${{cartItems.length}} item${{cartItems.length !== 1 ? 's' : ''}} in cart`)
        ]),

        // Cart Items
        React.createElement('div', {{
            key: 'items',
            style: {{ padding: '0' }}
        }}, cartItems.map((item, index) =>
            React.createElement('div', {{
                key: `${{item.product_id}}-${{item.variant_id}}`,
                style: {{
                    display: 'grid',
                    gridTemplateColumns: '80px 1fr auto auto auto',
                    gap: '16px',
                    alignItems: 'center',
                    padding: '20px 30px',
                    borderBottom: index < cartItems.length - 1 ? '1px solid rgba(80, 80, 85, 0.6)' : 'none'
                }}
            }}, [
                // Item Image
                React.createElement('div', {{
                    key: 'image',
                    style: {{
                        width: '80px',
                        height: '80px',
                        borderRadius: '8px',
                        background: 'rgba(100, 100, 105, 0.8)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '2rem',
                        color: 'rgba(255, 255, 255, 0.8)'
                    }}
                }}, '📦'),
                
                // Item Details
                React.createElement('div', {{
                    key: 'details'
                }}, [
                    React.createElement('h3', {{
                        key: 'name',
                        style: {{
                            color: '#ffffff',
                            fontSize: '1.1rem',
                            fontWeight: '600',
                            marginBottom: '4px'
                        }}
                    }}, item.name),
                    React.createElement('div', {{
                        key: 'variant',
                        style: {{
                            color: 'rgba(255, 255, 255, 0.7)',
                            fontSize: '0.9rem',
                            marginBottom: '4px'
                        }}
                    }}, item.variant),
                    React.createElement('div', {{
                        key: 'price',
                        style: {{
                            color: 'rgba(255, 255, 255, 0.8)',
                            fontSize: '0.9rem'
                        }}
                    }}, `$${{item.price.toFixed(2)}} each`)
                ]),
                
                // Quantity Controls
                React.createElement('div', {{
                    key: 'quantity',
                    style: {{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                    }}
                }}, [
                    React.createElement('button', {{
                        key: 'minus',
                        onClick: () => updateQuantity(item.product_id, item.variant_id, -1),
                        style: {{
                            width: '32px',
                            height: '32px',
                            border: '1px solid rgba(100, 100, 105, 0.8)',
                            borderRadius: '6px',
                            background: 'rgba(80, 80, 85, 0.8)',
                            color: 'rgba(255, 255, 255, 0.9)',
                            fontSize: '1.2rem',
                            fontWeight: '600',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            transition: 'all 0.2s ease'
                        }}
                    }}, '-'),
                    React.createElement('span', {{
                        key: 'count',
                        style: {{
                            minWidth: '20px',
                            textAlign: 'center',
                            color: '#ffffff',
                            fontWeight: '600'
                        }}
                    }}, item.quantity),
                    React.createElement('button', {{
                        key: 'plus',
                        onClick: () => updateQuantity(item.product_id, item.variant_id, 1),
                        style: {{
                            width: '32px',
                            height: '32px',
                            border: '1px solid rgba(100, 100, 105, 0.8)',
                            borderRadius: '6px',
                            background: 'rgba(80, 80, 85, 0.8)',
                            color: 'rgba(255, 255, 255, 0.9)',
                            fontSize: '1.2rem',
                            fontWeight: '600',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            transition: 'all 0.2s ease'
                        }}
                    }}, '+')
                ]),
                
                // Item Total
                React.createElement('div', {{
                    key: 'total',
                    style: {{
                        color: '#ffffff',
                        fontSize: '1.1rem',
                        fontWeight: '700',
                        minWidth: '80px',
                        textAlign: 'right'
                    }}
                }}, `$${{item.total.toFixed(2)}}`),
                
                // Remove Button
                React.createElement('button', {{
                    key: 'remove',
                    onClick: () => removeItem(item.product_id, item.variant_id),
                    style: {{
                        width: '32px',
                        height: '32px',
                        border: '1px solid rgba(239, 68, 68, 0.5)',
                        borderRadius: '6px',
                        background: 'rgba(239, 68, 68, 0.2)',
                        color: '#ef4444',
                        fontSize: '1.2rem',
                        fontWeight: '600',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        transition: 'all 0.2s ease'
                    }},
                    onMouseEnter: (e) => {{
                        e.target.style.background = 'rgba(239, 68, 68, 0.3)';
                        e.target.style.borderColor = 'rgba(239, 68, 68, 0.7)';
                    }},
                    onMouseLeave: (e) => {{
                        e.target.style.background = 'rgba(239, 68, 68, 0.2)';
                        e.target.style.borderColor = 'rgba(239, 68, 68, 0.5)';
                    }}
                }}, '×')
            ])
        )),

        // Cart Footer
        React.createElement('div', {{
            key: 'footer',
            style: {{
                background: 'rgba(80, 80, 85, 0.8)',
                padding: '24px 30px'
            }}
        }}, [
            // Total
            React.createElement('div', {{
                key: 'total',
                style: {{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '20px',
                    fontSize: '1.5rem',
                    fontWeight: '700',
                    color: '#ffffff'
                }}
            }}, [
                React.createElement('span', {{ key: 'label' }}, 'Total:'),
                React.createElement('span', {{ key: 'amount' }}, `$${{cartTotal.toFixed(2)}}`)
            ]),
            
            // Action Buttons
            React.createElement('div', {{
                key: 'actions',
                style: {{
                    display: 'flex',
                    gap: '12px'
                }}
            }}, [
                React.createElement('button', {{
                    key: 'continue',
                    onClick: handleContinueShopping,
                    style: {{
                        flex: '1',
                        padding: '14px 20px',
                        border: '1px solid rgba(100, 100, 105, 0.8)',
                        borderRadius: '8px',
                        background: 'rgba(100, 100, 105, 0.8)',
                        color: 'rgba(255, 255, 255, 0.9)',
                        fontSize: '0.9rem',
                        fontWeight: '600',
                        cursor: 'pointer',
                        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                    }}
                }}, 'Continue Shopping'),
                
                React.createElement('button', {{
                    key: 'checkout',
                    onClick: handleCheckout,
                    style: {{
                        flex: '1',
                        padding: '14px 20px',
                        border: '1px solid rgba(0, 210, 255, 0.3)',
                        borderRadius: '8px',
                        background: 'linear-gradient(135deg, #00D2FF 0%, #3A7BD5 100%)',
                        color: 'white',
                        fontSize: '0.9rem',
                        fontWeight: '600',
                        cursor: 'pointer',
                        boxShadow: '0 4px 12px rgba(0, 210, 255, 0.25)',
                        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                    }},
                    onMouseEnter: (e) => {{
                        e.target.style.transform = 'translateY(-2px) scale(1.02)';
                        e.target.style.boxShadow = '0 8px 20px rgba(0, 210, 255, 0.35)';
                    }},
                    onMouseLeave: (e) => {{
                        e.target.style.transform = 'translateY(0) scale(1)';
                        e.target.style.boxShadow = '0 4px 12px rgba(0, 210, 255, 0.25)';
                    }}
                }}, 'Checkout')
            ])
        ])
    ]);
}}
"""

    ui_resource = create_ui_resource(
        content_type="remoteDom",
        content=script
    )
    
    return MCPResponse(
        id=request_id,
        result={"content": [ui_resource]}
    )

async def handle_process_checkout_remote_dom(request_id: str | int, session_id: str, arguments: Dict[str, Any]) -> MCPResponse:
    """Handle process_checkout with remote-dom - Process order and show confirmation"""
    
    # Get cart to process
    cart = carts.get(session_id, {"items": [], "total": 0.0})
    
    if not cart["items"]:
        return MCPResponse(
            id=request_id,
            error={"code": -32602, "message": "Cannot checkout with empty cart"}
        )
    
    # Extract form data
    name = arguments.get("name", "")
    email = arguments.get("email", "")  
    address = arguments.get("address", "")
    payment_method = arguments.get("payment_method", "credit_card")
    
    if not all([name, email, address]):
        return MCPResponse(
            id=request_id,
            error={"code": -32602, "message": "Missing required fields: name, email, address"}
        )
    
    # Generate mock order ID
    import time
    order_id = f"ORD-{int(time.time())}"
    order_total = cart["total"]
    
    # Process the order (in real app, would integrate with payment processor)
    order_summary = []
    for item in cart["items"]:
        product = products.get(item["product_id"])
        variant = next((v for v in product.variants if v.id == item["variant_id"]), None) if product else None
        
        if product and variant:
            item_price = product.price + variant.price_modifier
            total_item_price = item_price * item["quantity"]
            order_summary.append({
                "name": product.name,
                "variant": variant.name,
                "quantity": item["quantity"],
                "price": item_price,
                "total": total_item_price
            })
    
    # Clear the cart after successful order
    carts[session_id] = {"items": [], "total": 0.0}
    
    # Create order confirmation React component
    script = f"""
function OrderConfirmation({{ onAction }}) {{
    const orderData = {{
        orderId: '{order_id}',
        customerName: '{name}',
        customerEmail: '{email}',
        customerAddress: '{address}',
        paymentMethod: '{payment_method}',
        items: {json.dumps(order_summary)},
        total: {order_total}
    }};
    
    const handleContinueShopping = () => {{
        onAction({{
            type: 'tool',
            payload: {{
                toolName: 'get_products',
                params: {{}}
            }}
        }});
    }};

    return React.createElement('div', {{
        style: {{
            width: '100%',
            maxWidth: '450px',
            background: 'rgba(45, 45, 50, 0.95)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(70, 70, 80, 0.8)',
            borderRadius: '12px',
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.4)',
            overflow: 'hidden',
            margin: '0 auto',
            color: '#ffffff',
            fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", "Inter", "Segoe UI", system-ui, sans-serif'
        }}
    }}, [
        // Success Header
        React.createElement('div', {{
            key: 'header',
            style: {{
                background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)',
                color: 'white',
                padding: '30px',
                textAlign: 'center'
            }}
        }}, [
            React.createElement('div', {{
                key: 'icon',
                style: {{
                    fontSize: '4rem',
                    marginBottom: '16px'
                }}
            }}, '✅'),
            React.createElement('h1', {{
                key: 'title',
                style: {{
                    fontSize: '2.2rem',
                    fontWeight: '700',
                    marginBottom: '8px'
                }}
            }}, 'Order Confirmed!'),
            React.createElement('p', {{
                key: 'subtitle',
                style: {{
                    fontSize: '1.1rem',
                    opacity: '0.9'
                }}
            }}, `Order #${{orderData.orderId}}`)
        ]),

        // Order Details
        React.createElement('div', {{
            key: 'content',
            style: {{ padding: '30px' }}
        }}, [
            // Customer Info
            React.createElement('div', {{
                key: 'customer-info',
                style: {{
                    background: 'rgba(80, 80, 85, 0.8)',
                    borderRadius: '12px',
                    padding: '20px',
                    marginBottom: '24px'
                }}
            }}, [
                React.createElement('h3', {{
                    key: 'title',
                    style: {{
                        color: '#ffffff',
                        fontSize: '1.2rem',
                        fontWeight: '600',
                        marginBottom: '16px'
                    }}
                }}, 'Shipping Details'),
                React.createElement('div', {{
                    key: 'name',
                    style: {{
                        color: 'rgba(255, 255, 255, 0.9)',
                        marginBottom: '8px'
                    }}
                }}, `📧 ${{orderData.customerName}}`),
                React.createElement('div', {{
                    key: 'email', 
                    style: {{
                        color: 'rgba(255, 255, 255, 0.9)',
                        marginBottom: '8px'
                    }}
                }}, `✉️ ${{orderData.customerEmail}}`),
                React.createElement('div', {{
                    key: 'address',
                    style: {{
                        color: 'rgba(255, 255, 255, 0.9)',
                        marginBottom: '8px'
                    }}
                }}, `📍 ${{orderData.customerAddress}}`),
                React.createElement('div', {{
                    key: 'payment',
                    style: {{
                        color: 'rgba(255, 255, 255, 0.9)'
                    }}
                }}, `💳 ${{orderData.paymentMethod.replace('_', ' ').toUpperCase()}}`)
            ]),
            
            // Order Items
            React.createElement('div', {{
                key: 'order-items',
                style: {{
                    background: 'rgba(80, 80, 85, 0.8)',
                    borderRadius: '12px',
                    padding: '20px',
                    marginBottom: '24px'
                }}
            }}, [
                React.createElement('h3', {{
                    key: 'title',
                    style: {{
                        color: '#ffffff',
                        fontSize: '1.2rem',
                        fontWeight: '600',
                        marginBottom: '16px'
                    }}
                }}, 'Order Summary'),
                
                // Items
                ...orderData.items.map((item, index) =>
                    React.createElement('div', {{
                        key: index,
                        style: {{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            padding: '10px 0',
                            borderBottom: index < orderData.items.length - 1 ? '1px solid rgba(100, 100, 105, 0.6)' : 'none'
                        }}
                    }}, [
                        React.createElement('div', {{
                            key: 'info'
                        }}, [
                            React.createElement('div', {{
                                key: 'name',
                                style: {{
                                    color: '#ffffff',
                                    fontWeight: '600',
                                    marginBottom: '2px'
                                }}
                            }}, item.name),
                            React.createElement('div', {{
                                key: 'details',
                                style: {{
                                    color: 'rgba(255, 255, 255, 0.7)',
                                    fontSize: '0.9rem'
                                }}
                            }}, `${{item.variant}} × ${{item.quantity}}`)
                        ]),
                        React.createElement('div', {{
                            key: 'price',
                            style: {{
                                color: '#ffffff',
                                fontWeight: '600'
                            }}
                        }}, `$${{item.total.toFixed(2)}}`)
                    ])
                ),
                
                // Total
                React.createElement('div', {{
                    key: 'total',
                    style: {{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginTop: '16px',
                        paddingTop: '16px',
                        borderTop: '2px solid rgba(100, 100, 105, 0.6)',
                        fontSize: '1.3rem',
                        fontWeight: '700',
                        color: '#ffffff'
                    }}
                }}, [
                    React.createElement('span', {{ key: 'label' }}, 'Total Paid:'),
                    React.createElement('span', {{ 
                        key: 'amount',
                        style: {{
                            color: '#22c55e'
                        }}
                    }}, `$${{orderData.total.toFixed(2)}}`)
                ])
            ]),
            
            // Next Steps
            React.createElement('div', {{
                key: 'next-steps',
                style: {{
                    background: 'rgba(34, 197, 94, 0.15)',
                    border: '1px solid rgba(34, 197, 94, 0.3)',
                    borderRadius: '12px',
                    padding: '20px',
                    marginBottom: '24px'
                }}
            }}, [
                React.createElement('h3', {{
                    key: 'title',
                    style: {{
                        color: '#22c55e',
                        fontSize: '1.1rem',
                        fontWeight: '600',
                        marginBottom: '12px'
                    }}
                }}, 'What happens next?'),
                React.createElement('ul', {{
                    key: 'steps',
                    style: {{
                        color: 'rgba(255, 255, 255, 0.9)',
                        paddingLeft: '20px',
                        lineHeight: '1.6'
                    }}
                }}, [
                    React.createElement('li', {{ key: '1' }}, 'Order confirmation email sent to your inbox'),
                    React.createElement('li', {{ key: '2' }}, 'Items will be packed and shipped within 24 hours'),
                    React.createElement('li', {{ key: '3' }}, 'You\\'ll receive tracking information once shipped')
                ])
            ]),
            
            // Continue Shopping Button
            React.createElement('div', {{
                key: 'actions',
                style: {{ textAlign: 'center' }}
            }}, React.createElement('button', {{
                onClick: handleContinueShopping,
                style: {{
                    background: 'linear-gradient(135deg, #00D2FF 0%, #3A7BD5 100%)',
                    color: 'white',
                    border: 'none',
                    padding: '16px 32px',
                    borderRadius: '12px',
                    fontSize: '1rem',
                    fontWeight: '600',
                    cursor: 'pointer',
                    boxShadow: '0 6px 20px rgba(0, 210, 255, 0.25)',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                }},
                onMouseEnter: (e) => {{
                    e.target.style.transform = 'translateY(-2px) scale(1.02)';
                    e.target.style.boxShadow = '0 12px 32px rgba(0, 210, 255, 0.35)';
                }},
                onMouseLeave: (e) => {{
                    e.target.style.transform = 'translateY(0) scale(1)';
                    e.target.style.boxShadow = '0 6px 20px rgba(0, 210, 255, 0.25)';
                }}
            }}, 'Continue Shopping'))
        ])
    ]);
}}
"""

    ui_resource = create_ui_resource(
        content_type="remoteDom",
        content=script
    )
    
    return MCPResponse(
        id=request_id,
        result={"content": [ui_resource]}
    )

async def handle_checkout_remote_dom(request_id: str | int, session_id: str, arguments: Dict[str, Any] = None) -> MCPResponse:
    """Handle checkout with remote-dom - Interactive checkout form"""
    
    # Get cart
    cart = carts.get(session_id, {"items": [], "total": 0.0})
    
    if not cart["items"]:
        return MCPResponse(
            id=request_id,
            error={"code": -32602, "message": "Cannot checkout with empty cart"}
        )
    
    # Prepare order summary data
    order_items = []
    for item in cart["items"]:
        product = products.get(item["product_id"])
        variant = next((v for v in product.variants if v.id == item["variant_id"]), None) if product else None
        
        if product and variant:
            item_price = product.price + variant.price_modifier
            total_item_price = item_price * item["quantity"]
            order_items.append({
                "name": product.name,
                "variant": variant.name,
                "quantity": item["quantity"],
                "total": total_item_price
            })

    # Checkout form React component
    script = f"""
function CheckoutForm({{ onAction }}) {{
    const orderItems = {json.dumps(order_items)};
    const cartTotal = {cart["total"]};
    const [formData, setFormData] = useState({{
        name: '',
        email: '',
        address: '',
        payment_method: 'credit_card'
    }});
    
    const handleInputChange = (field, value) => {{
        setFormData(prev => ({{ ...prev, [field]: value }}));
    }};
    
    const handleSubmit = () => {{
        if (!formData.name || !formData.email || !formData.address) {{
            alert('Please fill in all required fields');
            return;
        }}
        
        onAction({{
            type: 'tool',
            payload: {{
                toolName: 'process_checkout',
                params: {{
                    session_id: 'default',
                    ...formData
                }}
            }}
        }});
    }};
    
    const handleBackToCart = () => {{
        onAction({{
            type: 'tool',
            payload: {{
                toolName: 'get_cart',
                params: {{ session_id: '{session_id}' }}
            }}
        }});
    }};

    return React.createElement('div', {{
        style: {{
            width: '100%',
            maxWidth: '700px',
            background: 'rgba(45, 45, 50, 0.95)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(70, 70, 80, 0.8)',
            borderRadius: '12px',
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.4)',
            overflow: 'hidden',
            margin: '0 auto',
            color: '#ffffff',
            fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", "Inter", "Segoe UI", system-ui, sans-serif'
        }}
    }}, [
        // Checkout Header
        React.createElement('div', {{
            key: 'header',
            style: {{
                background: 'linear-gradient(135deg, #16a34a 0%, #15803d 100%)',
                color: 'white',
                padding: '24px 30px',
                textAlign: 'center'
            }}
        }}, [
            React.createElement('h1', {{
                key: 'title',
                style: {{
                    fontSize: '2rem',
                    fontWeight: '700',
                    marginBottom: '8px'
                }}
            }}, 'Checkout'),
            React.createElement('p', {{
                key: 'subtitle',
                style: {{
                    fontSize: '1rem',
                    opacity: '0.9'
                }}
            }}, 'Complete your order')
        ]),

        // Checkout Content
        React.createElement('div', {{
            key: 'content',
            style: {{ padding: '30px' }}
        }}, [
            // Order Summary
            React.createElement('div', {{
                key: 'summary',
                style: {{
                    background: 'rgba(80, 80, 85, 0.8)',
                    borderRadius: '12px',
                    padding: '20px',
                    marginBottom: '30px'
                }}
            }}, [
                React.createElement('h3', {{
                    key: 'title',
                    style: {{
                        color: '#ffffff',
                        fontSize: '1.3rem',
                        fontWeight: '600',
                        marginBottom: '16px'
                    }}
                }}, 'Order Summary'),
                
                // Order Items
                ...orderItems.map((item, index) =>
                    React.createElement('div', {{
                        key: index,
                        style: {{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            padding: '8px 0',
                            borderBottom: index < orderItems.length - 1 ? '1px solid rgba(100, 100, 105, 0.6)' : 'none'
                        }}
                    }}, [
                        React.createElement('span', {{
                            key: 'info',
                            style: {{
                                color: 'rgba(255, 255, 255, 0.9)',
                                fontSize: '0.9rem'
                            }}
                        }}, `${{item.name}} (${{item.variant}}) × ${{item.quantity}}`),
                        React.createElement('span', {{
                            key: 'price',
                            style: {{
                                color: '#ffffff',
                                fontWeight: '600'
                            }}
                        }}, `$${{item.total.toFixed(2)}}`)
                    ])
                ),
                
                // Total
                React.createElement('div', {{
                    key: 'total',
                    style: {{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginTop: '16px',
                        paddingTop: '16px',
                        borderTop: '2px solid rgba(100, 100, 105, 0.6)',
                        fontSize: '1.2rem',
                        fontWeight: '700',
                        color: '#ffffff'
                    }}
                }}, [
                    React.createElement('span', {{ key: 'label' }}, 'Total:'),
                    React.createElement('span', {{ key: 'amount' }}, `$${{cartTotal.toFixed(2)}}`)
                ])
            ]),

            // Shipping Form
            React.createElement('div', {{
                key: 'form',
                style: {{ marginBottom: '30px' }}
            }}, [
                React.createElement('h3', {{
                    key: 'title',
                    style: {{
                        color: '#ffffff',
                        fontSize: '1.3rem',
                        fontWeight: '600',
                        marginBottom: '20px'
                    }}
                }}, 'Shipping Information'),
                
                // Name Input
                React.createElement('div', {{
                    key: 'name-field',
                    style: {{ marginBottom: '16px' }}
                }}, [
                    React.createElement('label', {{
                        key: 'label',
                        style: {{
                            display: 'block',
                            color: 'rgba(255, 255, 255, 0.9)',
                            fontSize: '0.9rem',
                            fontWeight: '500',
                            marginBottom: '6px'
                        }}
                    }}, 'Full Name *'),
                    React.createElement('input', {{
                        key: 'input',
                        type: 'text',
                        value: formData.name,
                        onChange: (e) => handleInputChange('name', e.target.value),
                        placeholder: 'Enter your full name',
                        style: {{
                            width: '100%',
                            padding: '12px 16px',
                            border: '1px solid rgba(100, 100, 105, 0.6)',
                            borderRadius: '8px',
                            background: 'rgba(80, 80, 85, 0.8)',
                            color: '#ffffff',
                            fontSize: '1rem',
                            fontFamily: 'inherit'
                        }}
                    }})
                ]),
                
                // Email Input
                React.createElement('div', {{
                    key: 'email-field',
                    style: {{ marginBottom: '16px' }}
                }}, [
                    React.createElement('label', {{
                        key: 'label',
                        style: {{
                            display: 'block',
                            color: 'rgba(255, 255, 255, 0.9)',
                            fontSize: '0.9rem',
                            fontWeight: '500',
                            marginBottom: '6px'
                        }}
                    }}, 'Email Address *'),
                    React.createElement('input', {{
                        key: 'input',
                        type: 'email',
                        value: formData.email,
                        onChange: (e) => handleInputChange('email', e.target.value),
                        placeholder: 'Enter your email address',
                        style: {{
                            width: '100%',
                            padding: '12px 16px',
                            border: '1px solid rgba(100, 100, 105, 0.6)',
                            borderRadius: '8px',
                            background: 'rgba(80, 80, 85, 0.8)',
                            color: '#ffffff',
                            fontSize: '1rem',
                            fontFamily: 'inherit'
                        }}
                    }})
                ]),
                
                // Address Input
                React.createElement('div', {{
                    key: 'address-field',
                    style: {{ marginBottom: '16px' }}
                }}, [
                    React.createElement('label', {{
                        key: 'label',
                        style: {{
                            display: 'block',
                            color: 'rgba(255, 255, 255, 0.9)',
                            fontSize: '0.9rem',
                            fontWeight: '500',
                            marginBottom: '6px'
                        }}
                    }}, 'Shipping Address *'),
                    React.createElement('textarea', {{
                        key: 'input',
                        value: formData.address,
                        onChange: (e) => handleInputChange('address', e.target.value),
                        placeholder: 'Enter your shipping address',
                        style: {{
                            width: '100%',
                            padding: '12px 16px',
                            border: '1px solid rgba(100, 100, 105, 0.6)',
                            borderRadius: '8px',
                            background: 'rgba(80, 80, 85, 0.8)',
                            color: '#ffffff',
                            fontSize: '1rem',
                            fontFamily: 'inherit',
                            minHeight: '80px',
                            resize: 'vertical'
                        }}
                    }})
                ]),
                
                // Payment Method
                React.createElement('div', {{
                    key: 'payment-field',
                    style: {{ marginBottom: '20px' }}
                }}, [
                    React.createElement('label', {{
                        key: 'label',
                        style: {{
                            display: 'block',
                            color: 'rgba(255, 255, 255, 0.9)',
                            fontSize: '0.9rem',
                            fontWeight: '500',
                            marginBottom: '6px'
                        }}
                    }}, 'Payment Method'),
                    React.createElement('select', {{
                        key: 'input',
                        value: formData.payment_method,
                        onChange: (e) => handleInputChange('payment_method', e.target.value),
                        style: {{
                            width: '100%',
                            padding: '12px 16px',
                            border: '1px solid rgba(100, 100, 105, 0.6)',
                            borderRadius: '8px',
                            background: 'rgba(80, 80, 85, 0.8)',
                            color: '#ffffff',
                            fontSize: '1rem',
                            fontFamily: 'inherit'
                        }}
                    }}, [
                        React.createElement('option', {{ key: 'cc', value: 'credit_card' }}, 'Credit Card'),
                        React.createElement('option', {{ key: 'debit', value: 'debit_card' }}, 'Debit Card'),
                        React.createElement('option', {{ key: 'paypal', value: 'paypal' }}, 'PayPal')
                    ])
                ])
            ]),

            // Action Buttons
            React.createElement('div', {{
                key: 'actions',
                style: {{
                    display: 'flex',
                    gap: '12px'
                }}
            }}, [
                React.createElement('button', {{
                    key: 'back',
                    onClick: handleBackToCart,
                    style: {{
                        flex: '1',
                        padding: '14px 20px',
                        border: '1px solid rgba(100, 100, 105, 0.8)',
                        borderRadius: '8px',
                        background: 'rgba(100, 100, 105, 0.8)',
                        color: 'rgba(255, 255, 255, 0.9)',
                        fontSize: '0.9rem',
                        fontWeight: '600',
                        cursor: 'pointer',
                        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                    }}
                }}, '← Back to Cart'),
                
                React.createElement('button', {{
                    key: 'submit',
                    onClick: handleSubmit,
                    style: {{
                        flex: '1',
                        padding: '14px 20px',
                        border: '1px solid rgba(22, 163, 74, 0.3)',
                        borderRadius: '8px',
                        background: 'linear-gradient(135deg, #16a34a 0%, #15803d 100%)',
                        color: 'white',
                        fontSize: '0.9rem',
                        fontWeight: '600',
                        cursor: 'pointer',
                        boxShadow: '0 4px 12px rgba(22, 163, 74, 0.25)',
                        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                    }},
                    onMouseEnter: (e) => {{
                        e.target.style.transform = 'translateY(-2px) scale(1.02)';
                        e.target.style.boxShadow = '0 8px 20px rgba(22, 163, 74, 0.35)';
                    }},
                    onMouseLeave: (e) => {{
                        e.target.style.transform = 'translateY(0) scale(1)';
                        e.target.style.boxShadow = '0 4px 12px rgba(22, 163, 74, 0.25)';
                    }}
                }}, 'Place Order')
            ])
        ])
    ]);
}}
"""

    ui_resource = create_ui_resource(
        content_type="remoteDom",
        content=script
    )
    
    return MCPResponse(
        id=request_id,
        result={"content": [ui_resource]}
    )

async def handle_process_checkout_remote_dom(request_id: str | int, session_id: str, arguments: Dict[str, Any]) -> MCPResponse:
    """Handle process_checkout with remote-dom - Process order and show confirmation"""
    
    # Get cart to process
    cart = carts.get(session_id, {"items": [], "total": 0.0})
    
    if not cart["items"]:
        return MCPResponse(
            id=request_id,
            error={"code": -32602, "message": "Cannot checkout with empty cart"}
        )
    
    # Extract form data
    name = arguments.get("name", "")
    email = arguments.get("email", "")  
    address = arguments.get("address", "")
    payment_method = arguments.get("payment_method", "credit_card")
    
    if not all([name, email, address]):
        return MCPResponse(
            id=request_id,
            error={"code": -32602, "message": "Missing required fields: name, email, address"}
        )
    
    # Generate mock order ID
    import time
    order_id = f"ORD-{int(time.time())}"
    order_total = cart["total"]
    
    # Process the order (in real app, would integrate with payment processor)
    order_summary = []
    for item in cart["items"]:
        product = products.get(item["product_id"])
        variant = next((v for v in product.variants if v.id == item["variant_id"]), None) if product else None
        
        if product and variant:
            item_price = product.price + variant.price_modifier
            total_item_price = item_price * item["quantity"]
            order_summary.append({
                "name": product.name,
                "variant": variant.name,
                "quantity": item["quantity"],
                "price": item_price,
                "total": total_item_price
            })
    
    # Clear the cart after successful order
    carts[session_id] = {"items": [], "total": 0.0}
    
    # Create order confirmation React component
    script = f"""
function OrderConfirmation({{ onAction }}) {{
    const orderData = {{
        orderId: '{order_id}',
        customerName: '{name}',
        customerEmail: '{email}',
        customerAddress: '{address}',
        paymentMethod: '{payment_method}',
        items: {json.dumps(order_summary)},
        total: {order_total}
    }};
    
    const handleContinueShopping = () => {{
        onAction({{
            type: 'tool',
            payload: {{
                toolName: 'get_products',
                params: {{}}
            }}
        }});
    }};

    return React.createElement('div', {{
        style: {{
            width: '100%',
            maxWidth: '450px',
            background: 'rgba(45, 45, 50, 0.95)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(70, 70, 80, 0.8)',
            borderRadius: '12px',
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.4)',
            overflow: 'hidden',
            margin: '0 auto',
            color: '#ffffff',
            fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", "Inter", "Segoe UI", system-ui, sans-serif'
        }}
    }}, [
        // Success Header
        React.createElement('div', {{
            key: 'header',
            style: {{
                background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)',
                color: 'white',
                padding: '30px',
                textAlign: 'center'
            }}
        }}, [
            React.createElement('div', {{
                key: 'icon',
                style: {{
                    fontSize: '4rem',
                    marginBottom: '16px'
                }}
            }}, '✅'),
            React.createElement('h1', {{
                key: 'title',
                style: {{
                    fontSize: '2.2rem',
                    fontWeight: '700',
                    marginBottom: '8px'
                }}
            }}, 'Order Confirmed!'),
            React.createElement('p', {{
                key: 'subtitle',
                style: {{
                    fontSize: '1.1rem',
                    opacity: '0.9'
                }}
            }}, `Order #${{orderData.orderId}}`)
        ]),

        // Order Details
        React.createElement('div', {{
            key: 'content',
            style: {{ padding: '30px' }}
        }}, [
            // Customer Info
            React.createElement('div', {{
                key: 'customer-info',
                style: {{
                    background: 'rgba(80, 80, 85, 0.8)',
                    borderRadius: '12px',
                    padding: '20px',
                    marginBottom: '24px'
                }}
            }}, [
                React.createElement('h3', {{
                    key: 'title',
                    style: {{
                        color: '#ffffff',
                        fontSize: '1.2rem',
                        fontWeight: '600',
                        marginBottom: '16px'
                    }}
                }}, 'Shipping Details'),
                React.createElement('div', {{
                    key: 'name',
                    style: {{
                        color: 'rgba(255, 255, 255, 0.9)',
                        marginBottom: '8px'
                    }}
                }}, `📧 ${{orderData.customerName}}`),
                React.createElement('div', {{
                    key: 'email', 
                    style: {{
                        color: 'rgba(255, 255, 255, 0.9)',
                        marginBottom: '8px'
                    }}
                }}, `✉️ ${{orderData.customerEmail}}`),
                React.createElement('div', {{
                    key: 'address',
                    style: {{
                        color: 'rgba(255, 255, 255, 0.9)',
                        marginBottom: '8px'
                    }}
                }}, `📍 ${{orderData.customerAddress}}`),
                React.createElement('div', {{
                    key: 'payment',
                    style: {{
                        color: 'rgba(255, 255, 255, 0.9)'
                    }}
                }}, `💳 ${{orderData.paymentMethod.replace('_', ' ').toUpperCase()}}`)
            ]),
            
            // Order Items
            React.createElement('div', {{
                key: 'order-items',
                style: {{
                    background: 'rgba(80, 80, 85, 0.8)',
                    borderRadius: '12px',
                    padding: '20px',
                    marginBottom: '24px'
                }}
            }}, [
                React.createElement('h3', {{
                    key: 'title',
                    style: {{
                        color: '#ffffff',
                        fontSize: '1.2rem',
                        fontWeight: '600',
                        marginBottom: '16px'
                    }}
                }}, 'Order Summary'),
                
                // Items
                ...orderData.items.map((item, index) =>
                    React.createElement('div', {{
                        key: index,
                        style: {{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            padding: '10px 0',
                            borderBottom: index < orderData.items.length - 1 ? '1px solid rgba(100, 100, 105, 0.6)' : 'none'
                        }}
                    }}, [
                        React.createElement('div', {{
                            key: 'info'
                        }}, [
                            React.createElement('div', {{
                                key: 'name',
                                style: {{
                                    color: '#ffffff',
                                    fontWeight: '600',
                                    marginBottom: '2px'
                                }}
                            }}, item.name),
                            React.createElement('div', {{
                                key: 'details',
                                style: {{
                                    color: 'rgba(255, 255, 255, 0.7)',
                                    fontSize: '0.9rem'
                                }}
                            }}, `${{item.variant}} × ${{item.quantity}}`)
                        ]),
                        React.createElement('div', {{
                            key: 'price',
                            style: {{
                                color: '#ffffff',
                                fontWeight: '600'
                            }}
                        }}, `$${{item.total.toFixed(2)}}`)
                    ])
                ),
                
                // Total
                React.createElement('div', {{
                    key: 'total',
                    style: {{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginTop: '16px',
                        paddingTop: '16px',
                        borderTop: '2px solid rgba(100, 100, 105, 0.6)',
                        fontSize: '1.3rem',
                        fontWeight: '700',
                        color: '#ffffff'
                    }}
                }}, [
                    React.createElement('span', {{ key: 'label' }}, 'Total Paid:'),
                    React.createElement('span', {{ 
                        key: 'amount',
                        style: {{
                            color: '#22c55e'
                        }}
                    }}, `$${{orderData.total.toFixed(2)}}`)
                ])
            ]),
            
            // Next Steps
            React.createElement('div', {{
                key: 'next-steps',
                style: {{
                    background: 'rgba(34, 197, 94, 0.15)',
                    border: '1px solid rgba(34, 197, 94, 0.3)',
                    borderRadius: '12px',
                    padding: '20px',
                    marginBottom: '24px'
                }}
            }}, [
                React.createElement('h3', {{
                    key: 'title',
                    style: {{
                        color: '#22c55e',
                        fontSize: '1.1rem',
                        fontWeight: '600',
                        marginBottom: '12px'
                    }}
                }}, 'What happens next?'),
                React.createElement('ul', {{
                    key: 'steps',
                    style: {{
                        color: 'rgba(255, 255, 255, 0.9)',
                        paddingLeft: '20px',
                        lineHeight: '1.6'
                    }}
                }}, [
                    React.createElement('li', {{ key: '1' }}, 'Order confirmation email sent to your inbox'),
                    React.createElement('li', {{ key: '2' }}, 'Items will be packed and shipped within 24 hours'),
                    React.createElement('li', {{ key: '3' }}, 'You\\'ll receive tracking information once shipped')
                ])
            ]),
            
            // Continue Shopping Button
            React.createElement('div', {{
                key: 'actions',
                style: {{ textAlign: 'center' }}
            }}, React.createElement('button', {{
                onClick: handleContinueShopping,
                style: {{
                    background: 'linear-gradient(135deg, #00D2FF 0%, #3A7BD5 100%)',
                    color: 'white',
                    border: 'none',
                    padding: '16px 32px',
                    borderRadius: '12px',
                    fontSize: '1rem',
                    fontWeight: '600',
                    cursor: 'pointer',
                    boxShadow: '0 6px 20px rgba(0, 210, 255, 0.25)',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                }},
                onMouseEnter: (e) => {{
                    e.target.style.transform = 'translateY(-2px) scale(1.02)';
                    e.target.style.boxShadow = '0 12px 32px rgba(0, 210, 255, 0.35)';
                }},
                onMouseLeave: (e) => {{
                    e.target.style.transform = 'translateY(0) scale(1)';
                    e.target.style.boxShadow = '0 6px 20px rgba(0, 210, 255, 0.25)';
                }}
            }}, 'Continue Shopping'))
        ])
    ]);
}}
"""

    ui_resource = create_ui_resource(
        content_type="remoteDom",
        content=script
    )
    
    return MCPResponse(
        id=request_id,
        result={"content": [ui_resource]}
    )