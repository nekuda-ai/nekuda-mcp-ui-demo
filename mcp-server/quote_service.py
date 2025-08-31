"""
Quote Service for Address-Aware Dynamic Pricing - MCP Server Implementation

This service handles price calculations including:
- Merchandise subtotals
- Shipping calculations based on destination
- Tax calculations based on billing address  
- Quote session management with versioning
- Address validation and normalization
- Coupon and discount management
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import re

# Configure logger for this module
logger = logging.getLogger("mcp-quote-service")

class QuoteStatus(Enum):
    PROVISIONAL = "provisional"  # No address or estimated pricing
    PARTIAL = "partial"         # Incomplete address info
    FINAL = "final"            # Complete address, exact pricing

class AddressConfidence(Enum):
    NONE = "none"           # No address provided
    PARTIAL = "partial"     # Some address fields missing
    VERIFIED = "verified"   # Complete address validation

@dataclass
class ShippingAddress:
    """Shipping address with validation"""
    name: Optional[str] = None
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "US"
    
    def is_complete(self) -> bool:
        """Check if address has all required fields"""
        return all([
            self.name,
            self.address_line1,
            self.city,
            self.state,
            self.postal_code
        ])
    
    def is_partial(self) -> bool:
        """Check if address has some useful fields"""
        return any([
            self.postal_code,
            self.state,
            self.city
        ])
    
    def get_confidence(self) -> AddressConfidence:
        """Determine address confidence level"""
        if self.is_complete():
            return AddressConfidence.VERIFIED
        elif self.is_partial():
            return AddressConfidence.PARTIAL
        else:
            return AddressConfidence.NONE

@dataclass 
class EstimationHints:
    """Fallback hints for provisional quotes"""
    fallback_country: str = "US"
    fallback_postal_code: Optional[str] = None
    fallback_state: Optional[str] = None

@dataclass
class CartItemForQuote:
    """Cart item for quote calculation"""
    sku: str
    quantity: int
    unit_price: float
    name: str
    
    @property
    def subtotal(self) -> float:
        return self.unit_price * self.quantity

@dataclass
class Cart:
    """Cart for quote calculation"""
    currency: str = "USD"
    items: List[CartItemForQuote] = field(default_factory=list)
    
    @property
    def merchandise_total(self) -> float:
        """Total of all items before shipping/tax"""
        return sum(item.subtotal for item in self.items)

@dataclass
class ShippingOption:
    """Available shipping method"""
    id: str
    label: str
    amount: float
    estimated_days: Optional[str] = None
    selected: bool = False

@dataclass
class Discount:
    """Applied discount/promotion"""
    code: str
    amount: float
    description: Optional[str] = None

@dataclass
class Quote:
    """Complete price quote with breakdown"""
    quote_session_id: str
    version: int
    status: QuoteStatus
    address_confidence: AddressConfidence
    
    # Cart breakdown
    line_items: List[CartItemForQuote]
    merchandise_total: float
    
    # Shipping options
    shipping_options: List[ShippingOption]
    selected_shipping: Optional[ShippingOption] = None
    
    # Tax and discounts
    tax: float = 0.0
    discounts: List[Discount] = field(default_factory=list)
    
    # Final totals
    subtotal: float = 0.0  # merchandise + shipping
    total: float = 0.0     # subtotal + tax - discounts
    currency: str = "USD"
    
    # Metadata
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=10))
    requires_address: bool = True
    warnings: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Calculate totals after initialization"""
        self._calculate_totals()
    
    def _calculate_totals(self):
        """Recalculate all totals"""
        self.merchandise_total = sum(item.subtotal for item in self.line_items)
        
        shipping_cost = 0.0
        if self.selected_shipping:
            shipping_cost = self.selected_shipping.amount
        elif self.shipping_options:
            # Use first shipping option as default
            shipping_cost = self.shipping_options[0].amount
        
        discount_total = sum(d.amount for d in self.discounts)
        
        self.subtotal = self.merchandise_total + shipping_cost
        self.total = self.subtotal + self.tax - discount_total
        
        # Update requirements
        self.requires_address = self.status != QuoteStatus.FINAL

    def is_expired(self) -> bool:
        """Check if quote has expired"""
        return datetime.utcnow() > self.expires_at
        
    def update_version(self):
        """Increment version number"""
        self.version += 1
        self.expires_at = datetime.utcnow() + timedelta(minutes=10)

class CouponService:
    """Service for managing coupon codes and validation"""
    
    def __init__(self):
        # In-memory coupon storage for demo
        self._available_coupons = {
            "WELCOME10": {
                "code": "WELCOME10",
                "type": "fixed_amount",
                "amount": 10.0,
                "minimum_order": 75.0,
                "description": "Welcome discount for orders over $75",
                "active": True,
                "usage_limit": None,
                "used_count": 0
            },
            "SHIP50": {
                "code": "SHIP50",
                "type": "percentage",
                "amount": 0.5,  # 50% off shipping
                "minimum_order": 50.0,
                "description": "50% off shipping for orders over $50",
                "active": True,
                "applies_to": "shipping",
                "usage_limit": 100,
                "used_count": 12
            },
            "SAVE15": {
                "code": "SAVE15",
                "type": "percentage",
                "amount": 0.15,  # 15% off total
                "minimum_order": 100.0,
                "description": "15% off orders over $100",
                "active": True,
                "usage_limit": None,
                "used_count": 0
            }
        }
    
    def validate_coupon(self, code: str, cart_total: float) -> tuple[bool, Optional[str], Optional[Dict]]:
        """Validate a coupon code"""
        code = code.strip().upper()
        
        if code not in self._available_coupons:
            return False, "Invalid coupon code", None
        
        coupon = self._available_coupons[code]
        
        if not coupon["active"]:
            return False, "This coupon is no longer active", None
        
        if coupon.get("usage_limit") and coupon["used_count"] >= coupon["usage_limit"]:
            return False, "This coupon has reached its usage limit", None
        
        if cart_total < coupon["minimum_order"]:
            return False, f"Minimum order amount is ${coupon['minimum_order']:.2f}", None
        
        return True, None, coupon
    
    def calculate_coupon_discount(self, coupon: Dict, cart_total: float, shipping_cost: float) -> float:
        """Calculate discount amount for a valid coupon"""
        if coupon["type"] == "fixed_amount":
            return min(coupon["amount"], cart_total)  # Don't exceed cart total
        elif coupon["type"] == "percentage":
            if coupon.get("applies_to") == "shipping":
                return shipping_cost * coupon["amount"]
            else:
                return cart_total * coupon["amount"]
        return 0.0
    
    def get_available_coupons(self, cart_total: float) -> List[Dict]:
        """Get list of available coupons for current cart"""
        available = []
        for code, coupon in self._available_coupons.items():
            if (coupon["active"] and 
                cart_total >= coupon["minimum_order"] and
                (not coupon.get("usage_limit") or coupon["used_count"] < coupon["usage_limit"])):
                available.append({
                    "code": code,
                    "description": coupon["description"],
                    "minimum_order": coupon["minimum_order"]
                })
        return available

class MerchantQuoteService:
    """Merchant service for managing price quotes with shipping, tax, and coupons"""
    
    def __init__(self):
        self._quote_cache: Dict[str, Quote] = {}
        self._shipping_rates = self._initialize_shipping_rates()
        self._tax_rates = self._initialize_tax_rates()
        self._coupon_service = CouponService()
    
    def _initialize_shipping_rates(self) -> Dict[str, Dict[str, float]]:
        """Initialize shipping cost lookup by state"""
        return {
            # West Coast - higher shipping from distribution center
            "CA": {"standard": 8.99, "express": 24.99}, 
            "WA": {"standard": 9.99, "express": 26.99},
            "OR": {"standard": 9.99, "express": 26.99},
            
            # East Coast - moderate shipping 
            "NY": {"standard": 6.99, "express": 19.99},
            "FL": {"standard": 7.99, "express": 21.99},
            "MA": {"standard": 6.99, "express": 19.99},
            
            # Central - lowest shipping (close to warehouse)
            "TX": {"standard": 4.99, "express": 16.99},
            "IL": {"standard": 5.99, "express": 17.99},
            "OH": {"standard": 5.99, "express": 17.99},
            
            # Default fallback
            "_default": {"standard": 7.99, "express": 21.99}
        }
    
    def _initialize_tax_rates(self) -> Dict[str, float]:
        """Initialize sales tax rates by state (simplified)"""
        return {
            "CA": 0.0875,  # California
            "NY": 0.08,    # New York
            "TX": 0.0625,  # Texas
            "FL": 0.06,    # Florida
            "WA": 0.065,   # Washington
            "IL": 0.0625,  # Illinois
            "MA": 0.0625,  # Massachusetts
            "OR": 0.0,     # Oregon - no sales tax
            "_default": 0.07  # 7% default
        }
    
    def _calculate_shipping_options(
        self, 
        cart: Cart, 
        address: Optional[ShippingAddress], 
        hints: Optional[EstimationHints]
    ) -> List[ShippingOption]:
        """Calculate available shipping options"""
        
        # Determine shipping state
        shipping_state = None
        if address and address.state:
            shipping_state = address.state.upper()
        elif hints and hints.fallback_state:
            shipping_state = hints.fallback_state.upper()
        
        # Get shipping rates for state or use default
        rates = self._shipping_rates.get(shipping_state, self._shipping_rates["_default"])
        
        options = [
            ShippingOption(
                id="standard",
                label="Standard Shipping (5-7 business days)",
                amount=rates["standard"],
                estimated_days="5-7 business days",
                selected=True
            ),
            ShippingOption(
                id="express", 
                label="Express Shipping (2-3 business days)",
                amount=rates["express"],
                estimated_days="2-3 business days"
            )
        ]
        
        # Free shipping promotion for orders over $100
        if cart.merchandise_total >= 100.0:
            options[0].amount = 0.0
            options[0].label = "FREE Standard Shipping (5-7 business days)"
        
        return options
    
    def _calculate_tax(
        self, 
        cart: Cart, 
        shipping_cost: float,
        address: Optional[ShippingAddress],
        hints: Optional[EstimationHints]
    ) -> float:
        """Calculate sales tax based on billing address"""
        
        # Determine tax state from address
        tax_state = None
        if address and address.state:
            tax_state = address.state.upper()
        elif hints and hints.fallback_state:
            tax_state = hints.fallback_state.upper()
        
        # Get tax rate for state
        tax_rate = self._tax_rates.get(tax_state, self._tax_rates["_default"])
        
        # Calculate tax on merchandise only (not shipping in most states)
        taxable_amount = cart.merchandise_total
        
        return round(taxable_amount * tax_rate, 2)
    
    def _determine_quote_status(
        self, 
        address: Optional[ShippingAddress],
        hints: Optional[EstimationHints]
    ) -> tuple[QuoteStatus, AddressConfidence]:
        """Determine quote status and address confidence"""
        
        if not address:
            return QuoteStatus.PROVISIONAL, AddressConfidence.NONE
        
        confidence = address.get_confidence()
        
        if confidence == AddressConfidence.VERIFIED:
            return QuoteStatus.FINAL, confidence
        elif confidence == AddressConfidence.PARTIAL:
            return QuoteStatus.PARTIAL, confidence
        else:
            return QuoteStatus.PROVISIONAL, confidence
    
    def _apply_automatic_discounts(self, cart: Cart) -> List[Discount]:
        """Apply automatic discounts based on cart conditions"""
        discounts = []
        
        # Automatic welcome discount for orders over $75
        if cart.merchandise_total >= 75.0:
            discounts.append(Discount(
                code="WELCOME10",
                amount=10.0,
                description="Welcome discount for orders over $75"
            ))
        
        return discounts
    
    def apply_coupon(self, quote_session_id: str, coupon_code: str) -> tuple[bool, str, Optional[Quote]]:
        """Apply a coupon code to an existing quote"""
        quote = self.get_quote(quote_session_id)
        if not quote:
            return False, "Quote not found or expired", None
        
        # Validate coupon
        is_valid, error_msg, coupon_data = self._coupon_service.validate_coupon(
            coupon_code, quote.merchandise_total
        )
        
        if not is_valid:
            return False, error_msg, quote
        
        # Calculate discount
        shipping_cost = quote.selected_shipping.amount if quote.selected_shipping else 0.0
        discount_amount = self._coupon_service.calculate_coupon_discount(
            coupon_data, quote.merchandise_total, shipping_cost
        )
        
        # Check if coupon already applied
        existing_codes = {d.code for d in quote.discounts}
        if coupon_code.upper() in existing_codes:
            return False, "Coupon already applied", quote
        
        # Add discount
        quote.discounts.append(Discount(
            code=coupon_code.upper(),
            amount=discount_amount,
            description=coupon_data["description"]
        ))
        
        # Update quote version and recalculate
        quote.update_version()
        quote._calculate_totals()
        
        return True, f"Coupon applied! You saved ${discount_amount:.2f}", quote
    
    def remove_coupon(self, quote_session_id: str, coupon_code: str) -> tuple[bool, str, Optional[Quote]]:
        """Remove a coupon from an existing quote"""
        quote = self.get_quote(quote_session_id)
        if not quote:
            return False, "Quote not found or expired", None
        
        # Find and remove the coupon
        coupon_code = coupon_code.upper()
        original_count = len(quote.discounts)
        quote.discounts = [d for d in quote.discounts if d.code != coupon_code]
        
        if len(quote.discounts) == original_count:
            return False, "Coupon not found in this quote", quote
        
        # Update quote version and recalculate
        quote.update_version()
        quote._calculate_totals()
        
        return True, "Coupon removed successfully", quote
    
    def create_or_update_quote(
        self,
        quote_session_id: str,
        cart: Cart,
        shipping_address: Optional[ShippingAddress] = None,
        estimation_hints: Optional[EstimationHints] = None,
        selected_shipping_id: Optional[str] = None
    ) -> Quote:
        """Create or update a price quote"""
        
        logger.debug(f"Creating quote for session {quote_session_id}")
        logger.debug(f"Selected shipping ID: {selected_shipping_id}")
        
        # Check for existing quote
        existing_quote = self._quote_cache.get(quote_session_id)
        version = (existing_quote.version + 1) if existing_quote else 1
        
        # Preserve existing discounts from manual coupon applications
        existing_manual_discounts = []
        if existing_quote:
            # Keep manually applied coupons (not automatic ones)
            existing_manual_discounts = [
                d for d in existing_quote.discounts 
                if d.code != "WELCOME10"  # Don't preserve automatic discounts
            ]
        
        # Determine quote status
        status, confidence = self._determine_quote_status(shipping_address, estimation_hints)
        
        # Calculate shipping options
        shipping_options = self._calculate_shipping_options(cart, shipping_address, estimation_hints)
        
        # Select shipping method
        selected_shipping = None
        if selected_shipping_id:
            # Find and select the requested shipping option
            for opt in shipping_options:
                if opt.id == selected_shipping_id:
                    opt.selected = True
                    selected_shipping = opt
                else:
                    opt.selected = False
        
        # Default to first option if none selected
        if not selected_shipping and shipping_options:
            shipping_options[0].selected = True
            selected_shipping = shipping_options[0]
        
        # Calculate shipping cost for tax calculation
        shipping_cost = selected_shipping.amount if selected_shipping else 0.0
        
        # Calculate tax
        tax = self._calculate_tax(cart, shipping_cost, shipping_address, estimation_hints)
        
        # Apply automatic discounts
        automatic_discounts = self._apply_automatic_discounts(cart)
        
        # Combine automatic and manual discounts
        all_discounts = automatic_discounts + existing_manual_discounts
        
        # Convert cart items
        line_items = [
            CartItemForQuote(
                sku=f"item_{i}",  # In real system, would come from cart item
                quantity=item.quantity,
                unit_price=item.unit_price,
                name=item.name
            ) for i, item in enumerate(cart.items)
        ]
        
        # Create quote
        quote = Quote(
            quote_session_id=quote_session_id,
            version=version,
            status=status,
            address_confidence=confidence,
            line_items=line_items,
            merchandise_total=cart.merchandise_total,
            shipping_options=shipping_options,
            selected_shipping=selected_shipping,
            tax=tax,
            discounts=all_discounts,
            currency=cart.currency
        )
        
        # Add warnings for provisional quotes
        if status == QuoteStatus.PROVISIONAL:
            quote.warnings.append("Prices are estimated. Add shipping address for exact pricing.")
        elif status == QuoteStatus.PARTIAL:
            quote.warnings.append("Some address information missing. Complete address for final pricing.")
        
        # Cache the quote
        self._quote_cache[quote_session_id] = quote
        
        logger.debug(f"Created quote {quote_session_id} v{version}: ${quote.total:.2f} ({status.value})")
        logger.debug(f"Selected shipping option: {selected_shipping.id if selected_shipping else 'None'} - ${selected_shipping.amount if selected_shipping else 0:.2f}")
        logger.debug(f"Shipping options: {[(opt.id, opt.selected, opt.amount) for opt in shipping_options]}")
        
        return quote
    
    def get_quote(self, quote_session_id: str) -> Optional[Quote]:
        """Retrieve existing quote"""
        quote = self._quote_cache.get(quote_session_id)
        
        if quote and quote.is_expired():
            logger.debug(f"Quote {quote_session_id} has expired, removing from cache")
            del self._quote_cache[quote_session_id]
            return None
            
        return quote
    
    def get_available_coupons(self, quote_session_id: str) -> List[Dict]:
        """Get available coupons for a quote"""
        quote = self.get_quote(quote_session_id)
        if not quote:
            return []
        
        return self._coupon_service.get_available_coupons(quote.merchandise_total)
    
    def cleanup_expired_quotes(self):
        """Remove expired quotes from cache"""
        expired_sessions = [
            session_id for session_id, quote in self._quote_cache.items()
            if quote.is_expired()
        ]
        
        for session_id in expired_sessions:
            del self._quote_cache[session_id]
        
        if expired_sessions:
            logger.debug(f"Cleaned up {len(expired_sessions)} expired quotes")
    
    def validate_quote_for_payment(self, quote_session_id: str, version: int) -> tuple[bool, str]:
        """Validate quote before payment processing"""
        quote = self.get_quote(quote_session_id)
        
        if not quote:
            return False, "Quote not found or expired"
        
        if quote.version != version:
            return False, f"Quote version mismatch. Current: {quote.version}, provided: {version}"
        
        if quote.status != QuoteStatus.FINAL:
            return False, f"Quote not finalized. Current status: {quote.status.value}"
        
        if quote.is_expired():
            return False, "Quote has expired"
        
        return True, "Quote is valid for payment"

# Global service instance
merchant_quote_service = MerchantQuoteService()