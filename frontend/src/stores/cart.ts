import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { CartItem } from '@/types'
import { chatApi } from '@/utils/api'
import { cartOperationsQueue } from '@/utils/asyncQueue'
import axios from 'axios'

// Quote management types
interface QuoteShippingAddress {
  name?: string
  phone?: string
  address_line1?: string
  address_line2?: string
  city?: string
  state?: string
  postal_code?: string
  country?: string
}

interface QuoteShippingOption {
  id: string
  label: string
  amount: string
  selected: boolean
}

interface QuoteDiscount {
  code: string
  amount: string
}

interface Quote {
  quote_session_id: string
  version: number
  status: 'provisional' | 'partial' | 'final'
  address_confidence: 'none' | 'partial' | 'verified'
  shipping_options: QuoteShippingOption[]
  tax: string
  discounts: QuoteDiscount[]
  total: string
  currency: string
  expires_at: string
  requires_address: boolean
  warnings: string[]
}

export const useCartStore = defineStore('cart', () => {
  // Product icon and color mapping (NBA jerseys)
  const PRODUCT_META = {
    'lebron-lakers-jersey': { icon: '👑', color: '#552583' },
    'curry-warriors-jersey': { icon: '🏹', color: '#1D428A' },
    'giannis-bucks-jersey': { icon: '🇬🇷', color: '#00471B' },
    'luka-mavs-jersey': { icon: '🏀', color: '#00538C' },
    'tatum-celtics-jersey': { icon: '☘️', color: '#007A33' },
    'jordan-bulls-jersey': { icon: '🐐', color: '#CE1141' }
  } as Record<string, { icon: string; color: string }>

  // State - Server-authoritative, no localStorage
  const items = ref<CartItem[]>([])
  const isOpen = ref(false)
  const isAutoOpening = ref(false)
  
  // Optimistic state management
  const backupItems = ref<CartItem[]>([])
  const pendingOperations = ref<Set<string>>(new Set())
  
  // Quote management state
  const currentQuote = ref<Quote | null>(null)
  const quoteSessionId = ref<string>('')
  const shippingAddress = ref<QuoteShippingAddress | null>(null)
  const isLoadingQuote = ref(false)
  const isCheckingOut = ref(false)
  const quoteError = ref<string | null>(null)
  
  // Simple debounced sync for demo
  let syncTimeout: NodeJS.Timeout | null = null
  const debouncedSync = (sessionId?: string) => {
    if (syncTimeout) clearTimeout(syncTimeout)
    syncTimeout = setTimeout(() => {
      if (pendingOperations.value.size === 0) {
        syncCart(sessionId)
      }
    }, 2000) // Sync every 2 seconds instead of after each operation
  }

  // Computed
  const itemCount = computed(() => {
    return items.value.reduce((total, item) => total + item.quantity, 0)
  })

  const total = computed(() => {
    return items.value.reduce((total, item) => total + (item.price * item.quantity), 0)
  })

  const isEmpty = computed(() => {
    return items.value.length === 0
  })

  // Quote computed properties
  const finalTotal = computed(() => {
    if (currentQuote.value && currentQuote.value.status === 'final') {
      return parseFloat(currentQuote.value.total)
    }
    return total.value // Fallback to cart total
  })

  const displayTotal = computed(() => {
    return currentQuote.value?.total ? parseFloat(currentQuote.value.total) : total.value
  })

  const tax = computed(() => {
    return currentQuote.value?.tax ? parseFloat(currentQuote.value.tax) : 0
  })

  const shipping = computed(() => {
    const selectedShipping = currentQuote.value?.shipping_options.find(opt => opt.selected)
    return selectedShipping ? parseFloat(selectedShipping.amount) : 0
  })

  const isPriceEstimated = computed(() => {
    return !currentQuote.value || currentQuote.value.status !== 'final'
  })

  // Initialize cart from server on store creation
  const initializeCart = async (sessionId?: string) => {
    await syncCart(sessionId)
  }

  // Actions
  const syncCart = async (sessionId?: string | null) => {
    // Skip sync if no session ID available
    if (!sessionId) {
      console.log('🚫 Skipping cart sync - no session ID available')
      return
    }
    
    // Skip sync if there are pending operations to avoid race conditions
    if (pendingOperations.value.size > 0) {
      console.log('⏸️ Skipping cart sync - pending operations in progress')
      return
    }
    
    try {
      const response = await chatApi.mcpAction({
        action_type: 'tool',
        tool_name: 'get_cart_state',
        params: {},
        session_id: sessionId
      })
      const snapshot = response?.result?.data?.cart
      if (snapshot && Array.isArray(snapshot.items)) {
        // Replace items from server snapshot only if no pending operations
        if (pendingOperations.value.size === 0) {
          const mapped: CartItem[] = snapshot.items.map((i: any) => {
            const meta = PRODUCT_META[i.product_id] || { icon: '📦', color: '#3b82f6' }
            console.log(`Cart item mapping: ${i.product_id} -> image: ${i.image_url}, fallback icon: ${meta.icon}`)
            return {
              id: `cart-${i.product_id}-${i.variant_id}`,
              productId: i.product_id,
              variantId: i.variant_id,
              name: i.name,
              variant: i.variant,
              price: i.price,
              quantity: i.quantity,
              imageUrl: i.image_url || '',
              icon: meta.icon,
              color: meta.color
            }
          })
          items.value = mapped
        }
      }
    } catch (e) {
      console.error('Failed to sync cart from server', e)
    }
  }
  const addItem = async (item: Omit<CartItem, 'id'>, sessionId?: string) => {
    const operationId = `add-${item.productId}-${item.variantId}-${Date.now()}`
    
    // Backup current state
    backupItems.value = [...items.value]
    pendingOperations.value.add(operationId)
    
    try {
      // Optimistic update - add item immediately to UI
      const newItem: CartItem = {
        id: `cart-${item.productId}-${item.variantId}`,
        ...item,
        icon: PRODUCT_META[item.productId]?.icon || '📦',
        color: PRODUCT_META[item.productId]?.color || '#3b82f6'
      }
      
      const existingIndex = items.value.findIndex(
        i => i.productId === item.productId && i.variantId === item.variantId
      )
      
      if (existingIndex >= 0) {
        items.value[existingIndex].quantity += item.quantity
      } else {
        items.value.push(newItem)
      }
      
      // Background server sync (don't await - let it happen in background)
      chatApi.mcpAction({
        action_type: 'tool',
        tool_name: 'add_to_cart',
        params: {
          product_id: item.productId,
          variant_id: item.variantId,
          quantity: item.quantity
        },
        session_id: sessionId
      }).catch(e => {
        console.warn('Background server sync failed, but UI remains responsive:', e)
        // Don't rollback for demo - keep optimistic updates
      })
      
      console.log(`✅ Added ${item.productId} to cart (demo mode)`)
      return { status: 'success', item: newItem }
      
    } catch (e) {
      console.error('Failed to add item', e)
      // Rollback optimistic update
      items.value = [...backupItems.value]
      throw e
    } finally {
      pendingOperations.value.delete(operationId)
      // Use debounced sync for demo
      debouncedSync(sessionId)
    }
  }

  const removeItem = async (itemId: string, sessionId?: string) => {
    const item = items.value.find(i => i.id === itemId)
    if (!item) return
    
    const operationId = `remove-${item.productId}-${item.variantId}-${Date.now()}`
    
    // Backup current state
    backupItems.value = [...items.value]
    pendingOperations.value.add(operationId)
    
    try {
      // Optimistic update - remove item immediately from UI
      items.value = items.value.filter(i => i.id !== itemId)
      
      // Background server sync (don't await)
      chatApi.mcpAction({
        action_type: 'tool',
        tool_name: 'remove_from_cart',
        params: { product_id: item.productId, variant_id: item.variantId },
        session_id: sessionId
      }).catch(e => {
        console.warn('Background server sync failed, but UI remains responsive:', e)
      })
      
      console.log(`✅ Removed ${item.productId} from cart (demo mode)`)
      return { status: 'success', removedItem: item }
      
    } finally {
      pendingOperations.value.delete(operationId)
      // Use debounced sync for demo
      debouncedSync(sessionId)
    }
  }

  const updateQuantity = async (itemId: string, quantity: number, sessionId?: string) => {
    const item = items.value.find(i => i.id === itemId)
    if (!item) return
    
    const operationId = `update-${item.productId}-${item.variantId}-${Date.now()}`
    
    // Backup current state
    backupItems.value = [...items.value]
    pendingOperations.value.add(operationId)
    
    try {
      // Optimistic update - update quantity immediately in UI
      if (quantity <= 0) {
        items.value = items.value.filter(i => i.id !== itemId)
      } else {
        const currentItem = items.value.find(i => i.id === itemId)
        if (currentItem) {
          currentItem.quantity = quantity
        }
      }
      
      // Background server sync (don't await)
      chatApi.mcpAction({
        action_type: 'tool',
        tool_name: 'set_cart_quantity',
        params: { product_id: item.productId, variant_id: item.variantId, quantity },
        session_id: sessionId
      }).catch(e => {
        console.warn('Background server sync failed, but UI remains responsive:', e)
      })
      
      console.log(`✅ Updated quantity for ${item.productId} (demo mode)`)
      return { status: 'success', item, quantity }
      
    } finally {
      pendingOperations.value.delete(operationId)
      // Use debounced sync for demo
      debouncedSync(sessionId)
    }
  }

  const clearCart = async (sessionId?: string) => {
    const operationId = `clear-${Date.now()}`
    
    // Backup current state
    const backup = [...items.value]
    backupItems.value = backup
    pendingOperations.value.add(operationId)
    
    try {
      // Optimistic update - clear cart immediately in UI
      items.value = []
      
      // Background server sync (don't await)
      chatApi.mcpAction({
        action_type: 'tool',
        tool_name: 'clear_cart',
        params: {},
        session_id: sessionId
      }).catch(e => {
        console.warn('Background server sync failed, but UI remains responsive:', e)
      })
      
      console.log(`✅ Cleared cart (demo mode)`)
      return { status: 'success', clearedItems: backup.length }
      
    } finally {
      pendingOperations.value.delete(operationId)
      // Use debounced sync for demo
      debouncedSync(sessionId)
    }
  }

  const toggleCart = () => {
    isOpen.value = !isOpen.value
  }

  const openCart = () => {
    isOpen.value = true
  }
  
  const openCartWithAnimation = () => {
    isAutoOpening.value = true
    isOpen.value = true
    // Clear auto-opening flag after animation
    setTimeout(() => {
      isAutoOpening.value = false
    }, 1200)
  }

  const closeCart = () => {
    isOpen.value = false
  }

  // Mock function to simulate adding from MCP actions
  const addFromMCPAction = (productData: {
    productId: string
    variantId: string
    name: string
    variant: string
    price: number
    quantity: number
    imageUrl: string
    icon?: string
    color?: string
  }, sessionId?: string) => {
    addItem(productData, sessionId)
    // Show a brief success animation
    setTimeout(() => {
      openCart()
    }, 500)
  }

  // Quote management methods
  const generateQuoteSessionId = () => {
    if (!quoteSessionId.value) {
      quoteSessionId.value = `quote_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    }
    return quoteSessionId.value
  }

  const loadBillingDetailsFromWallet = async (userId: string) => {
    try {
      console.log(`🔄 Attempting to load billing details for user: ${userId}`)
      const response = await axios.get(`/api/nekuda-billing-details?userId=${userId}`)
      if (response.data.success && response.data.billing_details) {
        const billing = response.data.billing_details
        shippingAddress.value = {
          name: billing.card_holder,
          phone: billing.phone_number,
          address_line1: billing.billing_address,
          city: billing.city,
          state: billing.state,
          postal_code: billing.zip_code,
          country: 'US'
        }
        console.log('🏠 Loaded billing details from wallet:', shippingAddress.value)
        return shippingAddress.value
      }
    } catch (error) {
      console.log('⚠️ Could not load billing details from wallet:', error.response?.status, error.response?.data)
      if (error.response?.status === 404) {
        console.log('💡 No billing details found - this is normal for new users')
      }
    }
    return null
  }

  const updateQuote = async (userId?: string) => {
    if (isEmpty.value) {
      currentQuote.value = null
      return
    }

    try {
      isLoadingQuote.value = true
      quoteError.value = null
      
      const sessionId = generateQuoteSessionId()
      
      // Try to load billing details if we don't have an address and user has wallet
      if (!shippingAddress.value && userId) {
        await loadBillingDetailsFromWallet(userId)
      }
      
      const cartItems = items.value.map(item => ({
        sku: item.productId,
        qty: item.quantity,
        unit_price: item.price.toString(),
        name: item.name
      }))

      const quoteRequest = {
        quote_session_id: sessionId,
        cart: {
          currency: 'USD',
          items: cartItems
        },
        shipping_address: shippingAddress.value,
        estimation_hints: {
          fallback_country: 'US',
          fallback_state: 'CA' // Default to California for demo
        },
        client_context: {
          user_id: userId || 'anonymous',
          wallet_present: !!shippingAddress.value
        }
      }

      console.log('📊 Updating quote:', quoteRequest)
      
      const response = await axios.post('/api/quotes/create-or-update', quoteRequest)
      currentQuote.value = response.data
      
      console.log(`💰 Quote updated: $${currentQuote.value?.total} (${currentQuote.value?.status})`)
      
    } catch (error) {
      console.error('Failed to update quote:', error)
      quoteError.value = 'Failed to calculate pricing'
    } finally {
      isLoadingQuote.value = false
    }
  }

  const updateShippingAddress = async (address: QuoteShippingAddress, userId?: string) => {
    shippingAddress.value = address
    await updateQuote(userId)
  }

  const selectShippingOption = async (shippingOptionId: string, userId?: string) => {
    if (!currentQuote.value) return
    
    try {
      console.log(`Selecting shipping option: ${shippingOptionId}`)
      
      // Optimistic update - immediately update UI for better UX
      const currentOptions = [...currentQuote.value.shipping_options]
      currentOptions.forEach(opt => {
        opt.selected = opt.id === shippingOptionId
      })
      currentQuote.value.shipping_options = currentOptions
      
      // Debounced loading - only show loading after 500ms delay
      let showLoading = false
      const loadingTimeout = setTimeout(() => {
        showLoading = true
        isLoadingQuote.value = true
      }, 500)
      
      const quoteRequest = {
        quote_session_id: currentQuote.value.quote_session_id,
        cart: {
          currency: 'USD',
          items: items.value.map(item => ({
            sku: item.productId,
            qty: item.quantity,
            unit_price: item.price.toString(),
            name: item.name
          }))
        },
        shipping_address: shippingAddress.value,
        selected_shipping_id: shippingOptionId,
        client_context: {
          user_id: userId || 'anonymous',
          wallet_present: !!shippingAddress.value
        }
      }

      console.log('Sending quote request with shipping selection:', quoteRequest)
      const response = await axios.post('/api/quotes/create-or-update', quoteRequest)
      
      // Clear the timeout since request completed
      clearTimeout(loadingTimeout)
      
      // Update with server response
      currentQuote.value = response.data
      console.log('Updated quote after shipping selection:', currentQuote.value)
      
    } catch (error) {
      console.error('Failed to select shipping option:', error)
      // Revert optimistic update on error
      if (currentQuote.value) {
        const response = await axios.post('/api/quotes/create-or-update', {
          quote_session_id: currentQuote.value.quote_session_id,
          cart: {
            currency: 'USD',
            items: items.value.map(item => ({
              sku: item.productId,
              qty: item.quantity,
              unit_price: item.price.toString(),
              name: item.name
            }))
          },
          shipping_address: shippingAddress.value,
          client_context: {
            user_id: userId || 'anonymous',
            wallet_present: !!shippingAddress.value
          }
        })
        currentQuote.value = response.data
      }
    } finally {
      isLoadingQuote.value = false
    }
  }

  // Note: Cart initialization is handled by chat store to ensure proper session management

  return {
    // State
    items,
    isOpen,
    isAutoOpening,
    pendingOperations,
    
    // Quote state
    currentQuote,
    quoteSessionId,
    shippingAddress,
    isLoadingQuote,
    isCheckingOut,
    quoteError,
    
    // Computed
    itemCount,
    total,
    isEmpty,
    finalTotal,
    displayTotal,
    tax,
    shipping,
    isPriceEstimated,
    
    // Actions
    initializeCart,
    syncCart,
    addItem,
    removeItem,
    updateQuantity,
    clearCart,
    toggleCart,
    openCart,
    openCartWithAnimation,
    closeCart,
    addFromMCPAction,
    
    // Quote actions
    updateQuote,
    updateShippingAddress,
    selectShippingOption,
    loadBillingDetailsFromWallet,
    
    // Checkout actions
    setCheckoutLoading: (loading: boolean) => {
      isCheckingOut.value = loading
    }
  }
})