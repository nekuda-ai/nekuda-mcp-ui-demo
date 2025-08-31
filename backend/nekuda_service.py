"""
nekuda Wallet Integration Service

This module handles all interactions with the Nekuda SDK including:
- Mandate creation for purchases
- Payment credential retrieval (tokens and PANs)
- User wallet management
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pydantic import BaseModel

# Configure logger for this module
logger = logging.getLogger("nekuda_service")

# Import Nekuda SDK with enhanced error handling
try:
    from nekuda import NekudaClient, MandateData, NekudaError
except ImportError:
    # Mock for development until real keys are provided
    class NekudaError(Exception):
        """Base exception for Nekuda SDK errors"""
        pass
    
    class NekudaClient:
        def __init__(self, secret_key: str):
            self.secret_key = secret_key
            
        @classmethod
        def from_env(cls):
            return cls("mock_secret_key")
        
        def user(self, user_id: str):
            return MockUserContext(user_id)
    
    class MandateData:
        def __init__(self, product: str, price: float, currency: str, 
                     merchant: str = None, merchant_link: str = None, 
                     product_description: str = None):
            self.product = product
            self.price = price
            self.currency = currency
            self.merchant = merchant
            self.merchant_link = merchant_link
            self.product_description = product_description
    
    class MockUserContext:
        def __init__(self, user_id: str):
            self.user_id = user_id
        
        def create_mandate(self, mandate_data):
            return MockMandateResponse("mandate_" + str(uuid.uuid4())[:8])
        
        def request_card_reveal_token(self, mandate_id: str):
            return MockRevealResponse("reveal_token_" + str(uuid.uuid4())[:8])
        
        def reveal_card_details(self, token: str):
            return MockCardDetails()
    
    class MockMandateResponse:
        def __init__(self, mandate_id: str):
            self.mandate_id = mandate_id
            self.status = "created"
    
    class MockRevealResponse:
        def __init__(self, token: str):
            self.token = token
            self.expires_at = datetime.utcnow()
    
    class MockCardDetails:
        def __init__(self):
            self.card_number = "4111111111111111"  # Test card
            self.card_exp = "12/25"  # MM/YY format
            self.card_cvv = "123"
            self.card_holder = "Test User"


@dataclass
class PaymentCredentials:
    """Enhanced payment credentials from Nekuda"""
    token: str
    pan: str
    expiry_month: str
    expiry_year: str
    cvv: str
    cardholder_name: str


@dataclass
class NekudaPaymentData:
    """Payment data retrieved from Nekuda - legacy compatibility"""
    token: str
    pan: str
    expiry_month: str
    expiry_year: str
    cvv: str
    cardholder_name: str


class CheckoutRequest(BaseModel):
    """Request model for checkout with Nekuda payment"""
    user_id: str
    cart_total: float
    cart_items: list
    product: str = "E-commerce Purchase"
    currency: str = "USD"


class NekudaCheckoutRequest(BaseModel):
    """Enhanced request model for new checkout endpoint"""
    user_id: str
    cart_items: List[Dict[str, Any]]
    cart_total: float
    product_summary: str = "Cart Purchase"
    currency: str = "USD"
    shipping_address: Optional[Dict[str, str]] = None
    quote_session_id: Optional[str] = None


class NekudaCheckoutResponse(BaseModel):
    """Response model for checkout endpoint - returns PAN for MCP server to process"""
    success: bool
    mandate_id: str
    payment_credentials: Optional[Dict[str, str]] = None
    currency: str
    timestamp: str
    message: str
    error_details: Optional[str] = None


class NekudaService:
    """Service class for Nekuda wallet operations"""
    
    def __init__(self):
        self.client = NekudaClient.from_env()
        self._user_contexts: Dict[str, Any] = {}
        # Track users who have added payment methods (for demo)
        self._users_with_payment_methods: set = set()
    
    def get_user_context(self, user_id: str):
        """Get or create user context for Nekuda operations"""
        if user_id not in self._user_contexts:
            self._user_contexts[user_id] = self.client.user(user_id)
        return self._user_contexts[user_id]
    
    async def create_mandate_for_purchase(
        self, 
        user_id: str, 
        cart_total: float, 
        product_name: str = "E-commerce Purchase",
        currency: str = "USD"
    ) -> str:
        """
        Create a mandate for a purchase
        Returns mandate_id for subsequent operations
        """
        try:
            user_context = self.get_user_context(user_id)
            
            mandate_data = MandateData(
                product=product_name,
                price=cart_total,
                currency=currency
            )
            
            mandate_response = user_context.create_mandate(mandate_data)
            return mandate_response.mandate_id
        
        except Exception as e:
            raise Exception(f"Failed to create mandate: {str(e)}")

    async def create_checkout_mandate(self, user_id: str, cart_data: Dict) -> str:
        """Create mandate when user clicks checkout - captures purchase intent"""
        try:
            user_context = self.get_user_context(user_id)
            
            # Create detailed mandate for checkout with comprehensive product info
            items_count = len(cart_data.get('items', []))
            
            # Build detailed product description from cart items
            product_names = []
            for item in cart_data.get('items', []):
                if isinstance(item, dict):
                    item_name = item.get('name', item.get('product_name', 'Unknown Product'))
                    quantity = item.get('quantity', 1)
                    if quantity > 1:
                        product_names.append(f"{quantity}x {item_name}")
                    else:
                        product_names.append(item_name)
            
            # Create comprehensive product description
            if product_names:
                if len(product_names) == 1:
                    main_product = product_names[0]
                    product_description = f"Purchase: {main_product}"
                else:
                    main_product = product_names[0]
                    if len(product_names) <= 3:
                        product_description = f"Purchase: {', '.join(product_names)}"
                    else:
                        product_description = f"Purchase: {main_product} and {len(product_names)-1} other items"
            else:
                main_product = "Cart Purchase"
                product_description = f"Cart checkout: {items_count} items"
            
            mandate_data = MandateData(
                product=main_product if len(product_names) == 1 else f"Cart Purchase ({items_count} items)",
                price=cart_data["total"],  # This is the final total including tax and shipping
                currency=cart_data["currency"],
                merchant="Nekuda MCP Demo Store",
                merchant_link="https://app.nekuda.ai/mcp-demo",
                product_description=product_description
            )
            
            logger.info(f"Creating checkout mandate for user {user_id}: ${cart_data['total']} {cart_data['currency']}")
            
            mandate_response = user_context.create_mandate(mandate_data)
            mandate_id = mandate_response.mandate_id
            
            logger.info(f"Successfully created mandate {mandate_id} for checkout")
            return mandate_id
            
        except NekudaError as e:
            logger.error(f"Nekuda API error creating mandate: {e}")
            raise Exception(f"Failed to create mandate: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating mandate: {e}")
            raise Exception(f"Failed to create mandate: {str(e)}")
    
    async def create_mandate_for_checkout(
        self, 
        user_id: str, 
        cart_total: float, 
        product_name: str,
        currency: str,
        checkout_context: str,
        cart_items: list
    ) -> str:
        """
        Legacy method for backward compatibility
        """
        cart_data = {
            "product_summary": product_name,
            "total": cart_total,
            "currency": currency,
            "items": cart_items
        }
        return await self.create_checkout_mandate(user_id, cart_data)
    
    async def get_payment_credentials_for_checkout(self, user_id: str, mandate_id: str) -> PaymentCredentials:
        """Complete token→credentials flow for checkout processing"""
        try:
            user_context = self.get_user_context(user_id)
            
            logger.info(f"Requesting card reveal token for mandate {mandate_id}")
            
            # Request card reveal token
            reveal_response = user_context.request_card_reveal_token(mandate_id=mandate_id)
            
            logger.info(f"Revealing card details with token")
            
            # Use token to reveal card details
            card_details = user_context.reveal_card_details(reveal_response.token)
            
            logger.info(f"Successfully retrieved payment credentials for mandate {mandate_id}")
            
            # Parse expiration date from MM/YY format
            exp_parts = card_details.card_exp.split('/')
            expiry_month = exp_parts[0]
            expiry_year = exp_parts[1]
            
            return PaymentCredentials(
                token=reveal_response.token,
                pan=card_details.card_number,
                expiry_month=expiry_month,
                expiry_year=expiry_year,
                cvv=card_details.card_cvv,
                cardholder_name=card_details.card_holder
            )
            
        except NekudaError as e:
            logger.error(f"Nekuda API error retrieving credentials: {e}")
            raise Exception(f"Failed to retrieve payment credentials: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving credentials: {e}")
            raise Exception(f"Failed to retrieve payment credentials: {str(e)}")
    
    async def get_payment_credentials(self, user_id: str, mandate_id: str) -> NekudaPaymentData:
        """
        Legacy method for backward compatibility
        """
        credentials = await self.get_payment_credentials_for_checkout(user_id, mandate_id)
        return NekudaPaymentData(
            token=credentials.token,
            pan=credentials.pan,
            expiry_month=credentials.expiry_month,
            expiry_year=credentials.expiry_year,
            cvv=credentials.cvv,
            cardholder_name=credentials.cardholder_name
        )
    
    async def validate_user_wallet(self, user_id: str) -> bool:
        """Verify user has valid payment methods before checkout"""
        try:
            user_context = self.get_user_context(user_id)
            
            logger.info(f"Validating wallet for user {user_id}")
            
            # First check session-based tracking (for newly added cards)
            has_session_methods = user_id in self._users_with_payment_methods
            
            if has_session_methods:
                logger.info(f"User {user_id} has payment methods from current session")
                return True
            
            # Check with Nekuda SDK for existing payment methods
            logger.info(f"Checking Nekuda SDK for existing payment methods for user {user_id}")
            
            # The most reliable way to check if a user has payment methods is to attempt 
            # the actual checkout flow they're trying to perform - if they have no payment methods,
            # the create_mandate call will fail with a specific error
            try:
                # Attempt to create a minimal mandate to test wallet validity
                # This is a common pattern for wallet validation in payment systems
                from nekuda import MandateData
                
                test_mandate_data = MandateData(
                    product="Wallet Validation",
                    price=1.00,  # Use a small but realistic amount
                    currency="USD"
                )
                
                # Attempt to create the mandate - this will fail if no payment methods exist
                mandate_response = user_context.create_mandate(test_mandate_data)
                
                if mandate_response and hasattr(mandate_response, 'mandate_id'):
                    logger.info(f"✅ User {user_id} has valid payment methods in Nekuda wallet")
                    return True
                else:
                    logger.info(f"❌ User {user_id} wallet validation failed - no valid response")
                    return False
                    
            except Exception as validation_error:
                # Parse the error to determine if it's specifically about missing payment methods
                error_message = str(validation_error).lower()
                
                # Check for specific Nekuda error messages indicating no payment methods
                no_payment_indicators = [
                    "no payment info found",
                    "no payment method",
                    "payment info not found",
                    "no stored payment",
                    "no cards found"
                ]
                
                if any(indicator in error_message for indicator in no_payment_indicators):
                    logger.info(f"❌ User {user_id} has no payment methods in Nekuda wallet: {validation_error}")
                    return False
                else:
                    # For other errors (network, API issues), log as warning and return False
                    logger.warning(f"⚠️ Wallet validation error for user {user_id} (assuming no payment methods): {validation_error}")
                    return False
            
        except NekudaError as e:
            logger.error(f"Nekuda API error validating wallet: {e}")
            return False
        except Exception as e:
            logger.error(f"Error validating wallet for user {user_id}: {e}")
            return False
    
    async def has_stored_payment_methods(self, user_id: str) -> bool:
        """
        Legacy method for backward compatibility
        """
        return await self.validate_user_wallet(user_id)
    
    def add_payment_method_for_user(self, user_id: str):
        """Mark that user has added a payment method (for demo tracking)"""
        logger.debug(f"Marking user {user_id} as having payment methods")
        self._users_with_payment_methods.add(user_id)
        logger.debug(f"Updated users with payment methods: {list(self._users_with_payment_methods)}")
    
    async def get_billing_details(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get billing details from Nekuda wallet for address prefill
        Returns non-sensitive billing information for shipping/contact purposes
        """
        try:
            user_context = self.get_user_context(user_id)
            
            logger.debug(f"Retrieving billing details for user {user_id}")
            
            # For demo purposes, let's provide mock billing details for any user
            # to demonstrate the address-aware pricing flow
            # In production, check if user has payment methods first
            
            # Mock billing details for demo - show different addresses for different users
            user_demo_data = {
                "user_id": user_id,
                "card_holder": "Demo User",
                "phone_number": "+1-555-0123",
                "billing_address": "123 Main Street",
                "city": "New York", 
                "state": "NY",
                "zip_code": "10001"
            }
            
            # Provide different demo addresses to show pricing variations
            if "california" in user_id.lower() or user_id.endswith("ca"):
                user_demo_data.update({
                    "city": "San Francisco",
                    "state": "CA", 
                    "zip_code": "94102"
                })
            elif "texas" in user_id.lower() or user_id.endswith("tx"):
                user_demo_data.update({
                    "city": "Austin",
                    "state": "TX",
                    "zip_code": "73301"
                })
            
            logger.debug(f"Retrieved mock billing details for user {user_id}: {user_demo_data['city']}, {user_demo_data['state']}")
            return user_demo_data
            
        except Exception as e:
            logger.error(f"Error retrieving billing details for user {user_id}: {e}")
            return None
    
    async def initialize_payment_collection(self, user_id: str) -> Dict[str, Any]:
        """
        Initialize payment collection flow for adding new cards
        Returns configuration for frontend payment form
        """
        try:
            user_context = self.get_user_context(user_id)
            
            logger.debug(f"Initializing payment collection for user {user_id}")
            
            # For now, we'll create a simple success response
            # In a real implementation, you'd start the Nekuda payment collection flow
            # This could involve creating a payment session or collection token
            
            return {
                "success": True,
                "user_id": user_id,
                "message": "Payment collection initialized",
                "redirect_url": f"https://app.nekuda.ai/collect-payment?user={user_id}",
                "environment": "production" if "live" in os.environ.get("NEKUDA_API_KEY", "") else "sandbox"
            }
        except Exception as e:
            logger.error(f"Error in initialize_payment_collection: {e}")
            raise Exception(f"Failed to initialize payment collection: {str(e)}")

    async def complete_checkout_flow(self, checkout_request: CheckoutRequest) -> NekudaPaymentData:
        """
        Complete end-to-end checkout flow:
        1. Create mandate
        2. Get payment credentials
        3. Return payment data for processing
        """
        try:
            # Step 1: Create mandate
            mandate_id = await self.create_mandate_for_purchase(
                user_id=checkout_request.user_id,
                cart_total=checkout_request.cart_total,
                product_name=checkout_request.product,
                currency=checkout_request.currency
            )
            
            # Step 2: Get payment credentials
            payment_data = await self.get_payment_credentials(
                user_id=checkout_request.user_id,
                mandate_id=mandate_id
            )
            
            return payment_data
            
        except Exception as e:
            raise Exception(f"Checkout flow failed: {str(e)}")


# Global service instance - initialize after environment is loaded
nekuda_service = None

def get_nekuda_service() -> NekudaService:
    """Get or create the global Nekuda service instance"""
    global nekuda_service
    if nekuda_service is None:
        nekuda_service = NekudaService()
    return nekuda_service