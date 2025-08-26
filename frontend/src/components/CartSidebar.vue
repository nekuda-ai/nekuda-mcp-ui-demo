<template>
  <div>
    <!-- Overlay -->
    <div 
      v-show="cartStore.isOpen"
      @click="cartStore.closeCart()"
      class="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 transition-all duration-500"
      :class="{ 'opacity-100': cartStore.isOpen, 'opacity-0': !cartStore.isOpen }"
    ></div>

    <!-- Cart Sidebar -->
    <div 
      class="cart-sidebar"
      :class="{ 
        'open': cartStore.isOpen, 
        'closed': !cartStore.isOpen,
        'animate-cart-auto-open': cartStore.isAutoOpening
      }"
    >
      <!-- Header -->
      <div class="flex items-center justify-between p-4 sm:p-6 border-b border-[#1e1e20]">
        <h2 class="text-lg font-semibold text-white tracking-tight">
          <span class="hidden sm:inline">Shopping Cart</span>
          <span class="sm:hidden">Cart</span>
        </h2>
        <button 
          @click="cartStore.closeCart()"
          class="text-white/60 hover:text-white transition-all duration-300 hover:rotate-90 p-2 min-w-touch min-h-touch flex items-center justify-center rounded-lg hover:bg-[#1e1e20]"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Cart Content -->
      <div class="flex-1 flex flex-col">
        <!-- Empty State -->
        <div v-if="cartStore.isEmpty" class="flex-1 flex items-center justify-center p-8">
          <div class="text-center">
            <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-[#1e1e20] flex items-center justify-center">
              <svg class="w-8 h-8 text-white/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 3h2l.4 2M7 13h10l4-8H5.4m0 0L7 13m0 0l-1.5 6M7 13l-1.5-6m0 0h15.5M7 13v6a1 1 0 001 1h7a1 1 0 001-1v-6M7 13H5.4" />
              </svg>
            </div>
            <h3 class="text-base font-medium text-white mb-2">Your cart is empty</h3>
            <p class="text-sm text-white/60 mb-6">Start adding items to see them here!</p>
            <button 
              @click="startShopping"
              class="bg-gradient-to-r from-[#00D2FF] to-[#3A7BD5] hover:shadow-[0_0_20px_rgba(0,210,255,0.4)] text-white px-6 py-3 rounded-2xl transition-all duration-300 font-medium hover:scale-105 active:scale-95 min-h-touch"
            >
              Start Shopping
            </button>
          </div>
        </div>

        <!-- Cart Items -->
        <div v-else class="flex-1 overflow-y-auto scrollbar-thin">
          <div class="p-4 sm:p-6 space-y-4">
            <CartItem 
              v-for="item in cartStore.items"
              :key="item.id"
              :item="item"
              @update-quantity="updateQuantity"
              @remove="removeItem"
            />
          </div>
        </div>

        <!-- Cart Summary (when items exist) -->
        <div v-if="!cartStore.isEmpty" class="border-t border-[#1e1e20] p-4 sm:p-6 space-y-4">
          <!-- Totals -->
          <div class="space-y-3">
            <div class="flex justify-between text-sm text-white/60">
              <span>Subtotal ({{ cartStore.itemCount }} items)</span>
              <span class="font-medium text-white">${{ cartStore.total.toFixed(2) }}</span>
            </div>
            <div class="flex justify-between text-sm text-white/60">
              <span>Shipping</span>
              <span class="font-medium text-[#00D2FF]">Free</span>
            </div>
            <div class="flex justify-between text-sm text-white/60">
              <span>Tax</span>
              <span class="font-medium text-white">${{ (cartStore.total * 0.08).toFixed(2) }}</span>
            </div>
            <div class="border-t border-[#2a2a2d] pt-3">
              <div class="flex justify-between text-lg font-semibold text-white">
                <span>Total</span>
                <span class="text-gradient-primary">${{ (cartStore.total * 1.08).toFixed(2) }}</span>
              </div>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="space-y-3 pt-2">
            <button 
              @click="proceedToCheckout"
              class="w-full bg-gradient-to-r from-[#00D2FF] to-[#3A7BD5] hover:shadow-[0_0_20px_rgba(0,210,255,0.4)] text-white py-4 px-6 rounded-2xl font-semibold transition-all duration-300 hover:scale-105 active:scale-95 min-h-touch"
            >
              Proceed to Checkout
            </button>
            <button 
              @click="continueShopping"
              class="w-full bg-[#1e1e20] hover:bg-[#2a2a2d] border border-[#2a2a2d] hover:border-[#00D2FF]/30 text-white py-3 px-6 rounded-2xl font-medium transition-all duration-300 hover:shadow-[0_0_20px_rgba(0,210,255,0.1)] min-h-touch"
            >
              Continue Shopping
            </button>
          </div>

          <!-- Clear Cart -->
          <div class="pt-3">
            <button 
              @click="clearCart"
              class="w-full text-sm text-white/40 hover:text-red-400 transition-colors duration-300 py-2"
            >
              Clear all items
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useCartStore } from '@/stores/cart'
import { useChatStore } from '@/stores/chat'
import CartItem from './CartItem.vue'
import { atomicNekudaCheckout, hasStoredPaymentMethods } from '@/utils/nekuda'
import { getUserId } from '@/utils/userId'
import { onMounted, watch } from 'vue'

const cartStore = useCartStore()
const chatStore = useChatStore()

// Ensure cart is synced when sidebar opens
watch(() => cartStore.isOpen, async (open) => {
  if (open) {
    await cartStore.syncCart(chatStore.sessionId)
  }
})

onMounted(async () => {
  await cartStore.syncCart(chatStore.sessionId)
})



const updateQuantity = (itemId: string, quantity: number) => {
  cartStore.updateQuantity(itemId, quantity, chatStore.sessionId)
}

const removeItem = (itemId: string) => {
  cartStore.removeItem(itemId, chatStore.sessionId)
}

const clearCart = async () => {
  if (confirm('Are you sure you want to clear all items from your cart?')) {
    await cartStore.clearCart(chatStore.sessionId)
  }
}

const startShopping = () => {
  cartStore.closeCart()
  chatStore.sendMessage('Show me products')
}

const continueShopping = () => {
  cartStore.closeCart()
}

const proceedToCheckout = async () => {
  try {
    console.log('Starting atomic Nekuda checkout...')
    
    // Step 1: Check if user has payment methods
    const userId = getUserId() // Unique user ID per session
    const userHasPaymentMethods = await hasStoredPaymentMethods(userId)
    
    if (!userHasPaymentMethods) {
      alert('Please add a payment method to your Nekuda wallet before checkout.\n\nClick the Wallet button in the header to add a payment method.')
      return
    }
    
    // Step 2: Atomic checkout - create mandate and get payment credentials when user clicks checkout
    console.log('Creating mandate and retrieving payment credentials...')
    const atomicCheckoutData = await atomicNekudaCheckout(
      userId,
      cartStore.total,
      cartStore.items
    )
    
    console.log('Atomic checkout completed:', {
      mandateId: atomicCheckoutData.mandate_id,
      token: atomicCheckoutData.token,
      pan: atomicCheckoutData.pan.slice(0, 4) + '****', // Log only first 4 digits for security
      checkoutContext: atomicCheckoutData.checkout_context
    })
    
    // Step 3: Trigger checkout through MCP action with payment data
    await chatStore.handleUIAction({
      type: 'tool',
      payload: {
        toolName: 'checkout',
        params: {
          paymentMethod: 'nekuda',
          nekudaToken: atomicCheckoutData.token,
          nekudaPan: atomicCheckoutData.pan,
          expiryMonth: atomicCheckoutData.expiryMonth,
          expiryYear: atomicCheckoutData.expiryYear,
          cvv: atomicCheckoutData.cvv,
          cardholderName: atomicCheckoutData.cardholderName,
          mandateId: atomicCheckoutData.mandate_id,
          checkoutContext: atomicCheckoutData.checkout_context
        }
      }
    })
    
    // Clear the frontend cart and close cart after successful checkout
    cartStore.clearCart(chatStore.sessionId)
    setTimeout(() => {
      cartStore.closeCart()
    }, 1000) // Small delay to let user see success message
    
  } catch (error) {
    console.error('Atomic Nekuda checkout failed:', error)
    const errorMessage = error.response?.data?.detail || error.message || 'Unknown error'
    alert(`Checkout failed: ${errorMessage}\n\nPlease check your Nekuda wallet configuration.`)
  }
}
</script>

<style scoped>
/* Additional cart-specific animations */
.cart-sidebar {
  transition: transform 0.3s ease-in-out;
}

/* Ensure proper scrolling for cart items */
.cart-items-container {
  scrollbar-width: thin;
  scrollbar-color: rgb(203 213 225) transparent;
}

.cart-items-container::-webkit-scrollbar {
  width: 6px;
}

.cart-items-container::-webkit-scrollbar-track {
  background: transparent;
}

.cart-items-container::-webkit-scrollbar-thumb {
  background-color: rgb(203 213 225);
  border-radius: 3px;
}

.cart-items-container::-webkit-scrollbar-thumb:hover {
  background-color: rgb(156 163 175);
}
</style>