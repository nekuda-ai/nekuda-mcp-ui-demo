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
      <div class="flex-1 overflow-y-auto scrollbar-thin">
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

        <!-- Cart Items and Summary (when items exist) -->
        <div v-else>
          <!-- Cart Items -->
          <div class="p-4 sm:p-6 space-y-4">
            <CartItem 
              v-for="item in cartStore.items"
              :key="item.id"
              :item="item"
              @update-quantity="updateQuantity"
              @remove="removeItem"
            />
          </div>

          <!-- Cart Summary -->
          <div class="border-t border-[#1e1e20] p-4 sm:p-6 space-y-4 bg-[#111113]">
          
          <!-- Quote Loading State -->
          <div v-if="cartStore.isLoadingQuote" class="flex items-center justify-center py-4">
            <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
            <span class="ml-3 text-sm text-white/60">Calculating pricing...</span>
          </div>
          
          <!-- Quote Error State -->
          <div v-else-if="cartStore.quoteError" class="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
            <div class="flex items-center">
              <svg class="w-4 h-4 text-red-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span class="text-sm text-red-400">{{ cartStore.quoteError }}</span>
            </div>
          </div>
          
          <!-- Pricing Breakdown -->
          <div v-else class="space-y-3">
            <!-- Status Badge -->
            <div v-if="cartStore.currentQuote" class="flex items-center justify-between mb-3">
              <div class="flex items-center space-x-2">
                <div 
                  class="px-2 py-1 rounded-full text-xs font-medium"
                  :class="{
                    'bg-green-500/20 text-green-400': cartStore.currentQuote.status === 'final',
                    'bg-yellow-500/20 text-yellow-400': cartStore.currentQuote.status === 'partial',
                    'bg-blue-500/20 text-blue-400': cartStore.currentQuote.status === 'provisional'
                  }"
                >
                  {{ cartStore.isPriceEstimated ? 'Estimated' : 'Final' }} Pricing
                </div>
                <div 
                  v-if="cartStore.currentQuote.address_confidence === 'verified'"
                  class="text-green-400"
                  title="Address verified"
                >
                  <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                  </svg>
                </div>
              </div>
            </div>
            
            <!-- Line Items -->
            <div class="flex justify-between text-sm text-white/60">
              <span>Subtotal ({{ cartStore.itemCount }} items)</span>
              <span class="font-medium text-white">${{ cartStore.total.toFixed(2) }}</span>
            </div>
            
            <!-- Shipping Options -->
            <div class="text-sm text-white/60">
              <div class="flex justify-between">
                <span>Shipping</span>
                <div class="text-right">
                  <div v-if="cartStore.shipping > 0" class="font-medium text-white">
                    ${{ cartStore.shipping.toFixed(2) }}
                  </div>
                  <div v-else class="font-medium text-[#00D2FF]">
                    Free
                  </div>
                </div>
              </div>
              <div v-if="cartStore.currentQuote?.shipping_options" class="mt-2 ml-0">
                <div class="relative">
                  <select 
                    v-if="cartStore.currentQuote.shipping_options.length > 1"
                    @change="selectShippingOption"
                    :value="cartStore.currentQuote.shipping_options.find(opt => opt.selected)?.id || cartStore.currentQuote.shipping_options[0]?.id"
                    :disabled="cartStore.isLoadingQuote"
                    class="bg-[#1e1e20] border border-[#2a2a2d] rounded text-xs text-white px-2 py-1 w-full focus:border-[#00D2FF] focus:outline-none transition-opacity duration-200"
                    :class="{ 'opacity-60': cartStore.isLoadingQuote }"
                  >
                    <option 
                      v-for="option in cartStore.currentQuote.shipping_options"
                      :key="option.id"
                      :value="option.id"
                    >
                      {{ option.label }} - ${{ option.amount }}
                    </option>
                  </select>
                  <!-- Subtle loading indicator -->
                  <div 
                    v-if="cartStore.isLoadingQuote" 
                    class="absolute right-2 top-1/2 transform -translate-y-1/2"
                  >
                    <div class="w-3 h-3 border-2 border-[#00D2FF] border-t-transparent rounded-full animate-spin"></div>
                  </div>
                </div>
                <div v-if="!cartStore.currentQuote.shipping_options.length > 1 && cartStore.currentQuote.shipping_options[0]" class="text-xs text-white/40 mt-1">
                  {{ cartStore.currentQuote.shipping_options[0].label }}
                </div>
              </div>
            </div>
            
            <!-- Tax -->
            <div class="flex justify-between text-sm text-white/60">
              <span>Tax</span>
              <span class="font-medium text-white">${{ cartStore.tax.toFixed(2) }}</span>
            </div>
            
            <!-- Discounts -->
            <div v-if="cartStore.currentQuote?.discounts?.length" class="space-y-1">
              <div 
                v-for="discount in cartStore.currentQuote.discounts" 
                :key="discount.code"
                class="flex justify-between text-sm text-green-400"
              >
                <span>{{ discount.code }}</span>
                <span>-${{ discount.amount }}</span>
              </div>
            </div>
            
            <!-- Total -->
            <div class="border-t border-[#2a2a2d] pt-3">
              <div class="flex justify-between text-lg font-semibold text-white">
                <span>Total</span>
                <span class="text-gradient-primary">${{ cartStore.displayTotal.toFixed(2) }}</span>
              </div>
            </div>
            
            <!-- Warnings -->
            <div v-if="cartStore.currentQuote?.warnings?.length" class="mt-2">
              <div 
                v-for="warning in cartStore.currentQuote.warnings"
                :key="warning"
                class="text-xs text-yellow-400 bg-yellow-500/10 border border-yellow-500/20 rounded px-2 py-1 mb-1"
              >
                ⚠️ {{ warning }}
              </div>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="space-y-3 pt-2">
            <button 
              @click="proceedToCheckout"
              :disabled="cartStore.isCheckingOut"
              :class="{ 'opacity-60 cursor-not-allowed': cartStore.isCheckingOut }"
              class="w-full bg-gradient-to-r from-[#00D2FF] to-[#3A7BD5] hover:shadow-[0_0_20px_rgba(0,210,255,0.4)] text-white py-4 px-6 rounded-2xl font-semibold transition-all duration-300 hover:scale-105 active:scale-95 min-h-touch flex items-center justify-center gap-2"
            >
              <div 
                v-if="cartStore.isCheckingOut"
                class="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"
              ></div>
              <span>{{ cartStore.isCheckingOut ? 'Processing...' : 'Place Order' }}</span>
            </button>
            <button 
              @click="continueShopping"
              :disabled="cartStore.isCheckingOut"
              :class="{ 'opacity-60 cursor-not-allowed': cartStore.isCheckingOut }"
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
    // Update quote when cart opens
    if (!cartStore.isEmpty) {
      await cartStore.updateQuote(getUserId())
    }
  }
})

// Update quote when cart items change
watch(() => cartStore.items, async () => {
  if (!cartStore.isEmpty && cartStore.isOpen) {
    await cartStore.updateQuote(getUserId())
  }
}, { deep: true })

// Handle shipping option selection
const selectShippingOption = async (event: Event) => {
  const target = event.target as HTMLSelectElement
  const selectedOptionId = target.value
  console.log('Selected shipping option:', selectedOptionId)
  await cartStore.selectShippingOption(selectedOptionId, getUserId())
}

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
    cartStore.setCheckoutLoading(true)
    console.log('Starting atomic Nekuda checkout...')
    
    // Step 1: Check if user has payment methods
    const userId = getUserId() // Unique user ID per session
    const userHasPaymentMethods = await hasStoredPaymentMethods(userId)
    
    if (!userHasPaymentMethods) {
      alert('Please add a payment method to your Nekuda wallet before checkout.\n\nClick the Wallet button in the header to add a payment method.')
      cartStore.setCheckoutLoading(false)
      return
    }

    // Step 2: Ensure we have a final quote for checkout
    if (!cartStore.currentQuote || cartStore.currentQuote.status !== 'final') {
      console.log('Quote not final, updating quote before checkout...')
      await cartStore.updateQuote(userId)
      
      // Check again after update
      if (!cartStore.currentQuote || cartStore.currentQuote.status !== 'final') {
        alert('Unable to finalize pricing. Please add a complete shipping address.')
        cartStore.setCheckoutLoading(false)
        return
      }
    }
    
    // Step 3: Atomic checkout - create mandate and get payment credentials when user clicks checkout
    console.log('Creating mandate and retrieving payment credentials...')
    const atomicCheckoutData = await atomicNekudaCheckout(
      userId,
      cartStore.finalTotal, // Use final total from quote
      cartStore.items,
      cartStore.currentQuote?.quote_session_id,
      cartStore.currentQuote?.version
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
          checkoutContext: atomicCheckoutData.checkout_context,
          quoteSessionId: cartStore.currentQuote?.quote_session_id,
          quoteVersion: cartStore.currentQuote?.version
        }
      }
    })
    
    // Clear the frontend cart and close cart after successful checkout
    cartStore.clearCart(chatStore.sessionId)
    setTimeout(() => {
      cartStore.closeCart()
      cartStore.setCheckoutLoading(false)
    }, 1000) // Small delay to let user see success message
    
  } catch (error) {
    console.error('Atomic Nekuda checkout failed:', error)
    const errorMessage = error.response?.data?.detail || error.message || 'Unknown error'
    alert(`Checkout failed: ${errorMessage}\n\nPlease check your Nekuda wallet configuration.`)
    cartStore.setCheckoutLoading(false)
  }
}
</script>

<style scoped>
/* Additional cart-specific animations */
.cart-sidebar {
  transition: transform 0.3s ease-in-out;
}

/* Enhanced scrollbar styles for dark theme */
.scrollbar-thin {
  scrollbar-width: thin;
  scrollbar-color: #2a2a2d #111113;
}

.scrollbar-thin::-webkit-scrollbar {
  width: 6px;
}

.scrollbar-thin::-webkit-scrollbar-track {
  background: #111113;
}

.scrollbar-thin::-webkit-scrollbar-thumb {
  background-color: #2a2a2d;
  border-radius: 3px;
}

.scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background-color: #00D2FF;
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