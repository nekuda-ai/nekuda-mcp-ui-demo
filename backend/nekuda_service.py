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
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pydantic import BaseModel

# Configure logger for this module
logger = logging.getLogger("nekuda_service")

# Import Nekuda SDK (will be available after pip install)
try:
    from nekuda import NekudaClient, MandateData
except ImportError:
    # Mock for development until real keys are provided
    class NekudaClient:
        def __init__(self, secret_key: str):
            self.secret_key = secret_key
            
        @classmethod
        def from_env(cls):
            return cls("mock_secret_key")
        
        def user(self, user_id: str):
            return MockUserContext(user_id)
    
    class MandateData:
        def __init__(self, product: str, price: float, currency: str):
            self.product = product
            self.price = price
            self.currency = currency
    
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
            self.pan = "4111111111111111"  # Test card
            self.expiry_month = "12"
            self.expiry_year = "25"
            self.cvv = "123"
            self.cardholder_name = "Test User"


@dataclass
class NekudaPaymentData:
    """Payment data retrieved from Nekuda"""
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
        Create a mandate specifically for checkout button click
        This captures the user's explicit intent to purchase when they click checkout
        """
        try:
            user_context = self.get_user_context(user_id)
            
            # Create detailed product description that reflects checkout action
            detailed_product = f"{product_name} (Checkout Action: {checkout_context})"
            if cart_items:
                item_summary = f" - {len(cart_items)} items"
                detailed_product += item_summary
            
            logger.debug(f"Creating checkout mandate for user {user_id}")
            logger.debug(f"Product: {detailed_product}")
            logger.debug(f"Amount: ${cart_total} {currency}")
            
            mandate_data = MandateData(
                product=detailed_product,
                price=cart_total,
                currency=currency
            )
            
            mandate_response = user_context.create_mandate(mandate_data)
            mandate_id = mandate_response.mandate_id
            
            logger.debug(f"Successfully created mandate {mandate_id} for checkout")
            return mandate_id
        
        except Exception as e:
            logger.error(f"Error creating checkout mandate: {e}")
            raise Exception(f"Failed to create checkout mandate: {str(e)}")
    
    async def get_payment_credentials(self, user_id: str, mandate_id: str) -> NekudaPaymentData:
        """
        Retrieve payment credentials (token and PAN) for a mandate
        This is the main method called during checkout
        """
        try:
            user_context = self.get_user_context(user_id)
            
            # Request card reveal token
            reveal_response = user_context.request_card_reveal_token(mandate_id=mandate_id)
            
            # Use token to reveal card details
            card_details = user_context.reveal_card_details(reveal_response.token)
            
            return NekudaPaymentData(
                token=reveal_response.token,
                pan=card_details.pan,
                expiry_month=card_details.expiry_month,
                expiry_year=card_details.expiry_year,
                cvv=card_details.cvv,
                cardholder_name=getattr(card_details, 'cardholder_name', 'Cardholder')
            )
        
        except Exception as e:
            raise Exception(f"Failed to retrieve payment credentials: {str(e)}")
    
    async def has_stored_payment_methods(self, user_id: str) -> bool:
        """
        Check if user has stored payment methods in their Nekuda wallet
        """
        try:
            user_context = self.get_user_context(user_id)
            
            logger.debug(f"Checking payment methods for user {user_id}")
            
            # Check if user has added payment methods (demo tracking)
            has_methods = user_id in self._users_with_payment_methods
            
            logger.debug(f"User {user_id} has payment methods: {has_methods}")
            logger.debug(f"Users with payment methods: {list(self._users_with_payment_methods)}")
            
            return has_methods
            
        except Exception as e:
            logger.error(f"Error checking payment methods for user {user_id}: {e}")
            return False
    
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


# Global service instance
nekuda_service = NekudaService()