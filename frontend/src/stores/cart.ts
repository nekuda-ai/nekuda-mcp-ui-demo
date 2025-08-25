import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { CartItem } from '@/types'
import { chatApi } from '@/utils/api'
import { cartOperationsQueue } from '@/utils/asyncQueue'

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
    
    return cartOperationsQueue.enqueue(async () => {
      console.log(`🛒 Queue: Starting add item operation for ${item.productId}`)
      
      // Backup current state
      const backup = [...items.value]
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
        
        // Background server sync
        await chatApi.mcpAction({
          action_type: 'tool',
          tool_name: 'add_to_cart',
          params: {
            product_id: item.productId,
            variant_id: item.variantId,
            quantity: item.quantity
          },
          session_id: sessionId
        })
        
        console.log(`✅ Queue: Successfully added ${item.productId} to cart`)
        return { status: 'success', item: newItem }
        
      } catch (e) {
        console.error('Failed to add item via MCP', e)
        // Rollback optimistic update
        items.value = backup
        throw e
      } finally {
        pendingOperations.value.delete(operationId)
        // Always sync after operation completes
        await syncCart(sessionId)
      }
    }, operationId)
  }

  const removeItem = async (itemId: string, sessionId?: string) => {
    const item = items.value.find(i => i.id === itemId)
    if (!item) return
    
    const operationId = `remove-${item.productId}-${item.variantId}-${Date.now()}`
    
    return cartOperationsQueue.enqueue(async () => {
      console.log(`🛒 Queue: Starting remove item operation for ${item.productId}`)
      
      // Backup current state
      const backup = [...items.value]
      pendingOperations.value.add(operationId)
      
      try {
        // Optimistic update - remove item immediately from UI
        items.value = items.value.filter(i => i.id !== itemId)
        
        // Background server sync
        await chatApi.mcpAction({
          action_type: 'tool',
          tool_name: 'remove_from_cart',
          params: { product_id: item.productId, variant_id: item.variantId },
          session_id: sessionId
        })
        
        console.log(`✅ Queue: Successfully removed ${item.productId} from cart`)
        return { status: 'success', removedItem: item }
        
      } catch (e) {
        console.error('Failed to remove item via MCP', e)
        // Rollback optimistic update
        items.value = backup
        throw e
      } finally {
        pendingOperations.value.delete(operationId)
        // Always sync after operation completes
        await syncCart(sessionId)
      }
    }, operationId)
  }

  const updateQuantity = async (itemId: string, quantity: number, sessionId?: string) => {
    const item = items.value.find(i => i.id === itemId)
    if (!item) return
    
    const operationId = `update-${item.productId}-${item.variantId}-${Date.now()}`
    
    return cartOperationsQueue.enqueue(async () => {
      console.log(`🛒 Queue: Starting update quantity operation for ${item.productId} (${quantity})`)
      
      // Backup current state
      const backup = [...items.value]
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
        
        // Background server sync
        await chatApi.mcpAction({
          action_type: 'tool',
          tool_name: 'set_cart_quantity',
          params: { product_id: item.productId, variant_id: item.variantId, quantity },
          session_id: sessionId
        })
        
        console.log(`✅ Queue: Successfully updated quantity for ${item.productId}`)
        return { status: 'success', item, quantity }
        
      } catch (e) {
        console.error('Failed to update quantity via MCP', e)
        // Rollback optimistic update
        items.value = backup
        throw e
      } finally {
        pendingOperations.value.delete(operationId)
        // Always sync after operation completes
        await syncCart(sessionId)
      }
    }, operationId)
  }

  const clearCart = async (sessionId?: string) => {
    const operationId = `clear-${Date.now()}`
    
    return cartOperationsQueue.enqueue(async () => {
      console.log(`🛒 Queue: Starting clear cart operation`)
      
      // Backup current state
      const backup = [...items.value]
      pendingOperations.value.add(operationId)
      
      try {
        // Optimistic update - clear cart immediately in UI
        items.value = []
        
        // Background server sync
        await chatApi.mcpAction({
          action_type: 'tool',
          tool_name: 'clear_cart',
          params: {},
          session_id: sessionId
        })
        
        console.log(`✅ Queue: Successfully cleared cart`)
        return { status: 'success', clearedItems: backup.length }
        
      } catch (e) {
        console.error('Failed to clear cart via MCP', e)
        // Rollback optimistic update
        items.value = backup
        throw e
      } finally {
        pendingOperations.value.delete(operationId)
        // Always sync after operation completes
        await syncCart(sessionId)
      }
    }, operationId)
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

  // Note: Cart initialization is handled by chat store to ensure proper session management

  return {
    // State
    items,
    isOpen,
    isAutoOpening,
    pendingOperations,
    // Computed
    itemCount,
    total,
    isEmpty,
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
    addFromMCPAction
  }
})