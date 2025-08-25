import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatMessage, ChatRequest, ChatResponse, UIActionResult } from '@/types'
import { chatApi } from '@/utils/api'
import { useCartStore } from './cart'

export const useChatStore = defineStore('chat', () => {
  // Get cart store instance
  const cartStore = useCartStore()
  
  // State
  const messages = ref<ChatMessage[]>([])
  const isLoading = ref(false)
  const sessionId = ref<string | null>(null)
  const error = ref<string | null>(null)

  // Computed
  const lastMessage = computed(() => {
    return messages.value[messages.value.length - 1] || null
  })

  const hasMessages = computed(() => {
    return messages.value.length > 0
  })

  // Actions
  const addMessage = (message: ChatMessage) => {
    messages.value.push({
      ...message,
      id: message.id || `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: message.timestamp || new Date()
    })
  }

  const sendMessage = async (content: string) => {
    error.value = null
    
    // Add user message immediately
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date()
    }
    addMessage(userMessage)

    // Set loading state
    isLoading.value = true

    try {
      const request: ChatRequest = {
        message: content,
        session_id: sessionId.value || undefined
      }

      const response = await chatApi.sendMessage(request)
      
      // Update session ID
      sessionId.value = response.session_id

      // Add assistant message
      const assistantMessage: ChatMessage = {
        id: response.message.id || `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.message.content,
        timestamp: new Date(response.message.timestamp),
        uiResource: response.message.ui_resource
      }
      addMessage(assistantMessage)

    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to send message'
      
      // Add error message to chat
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'I apologize, but I encountered an error while processing your message. Please try again.',
        timestamp: new Date()
      }
      addMessage(errorMessage)
    } finally {
      isLoading.value = false
    }
  }

  // Enhanced throttle and mutex mechanism to prevent race conditions
  let lastActionTime = 0
  let lastActionData: string | null = null
  const ACTION_THROTTLE_MS = 100 // Reduced to 100ms for better responsiveness
  const CART_ACTION_THROTTLE_MS = 50 // Even faster for cart operations
  const processingActions = new Set<string>() // Track currently processing actions
  const recentActions = new Map<string, number>() // Track recent action timestamps for smart throttling

  const handleUIAction = async (action: UIActionResult) => {
    console.log('🎯 Chat store handling UI action:', action)
    
    const now = Date.now()
    const actionKey = `${action.type}-${action.payload.toolName}-${JSON.stringify(action.payload.params || {})}`
    const processingKey = `${action.type}-${action.payload.toolName}`
    const isCartAction = action.payload.toolName?.includes('cart') || action.payload.toolName === 'add_to_cart'
    
    // Check if identical action is already processing (mutex)
    if (processingActions.has(actionKey)) {
      console.log('🔒 Action blocked - identical action already processing')
      return { status: 'blocked', message: 'Identical action in progress' }
    }
    
    // Smart throttling based on action type
    const throttleMs = isCartAction ? CART_ACTION_THROTTLE_MS : ACTION_THROTTLE_MS
    const lastActionTime = recentActions.get(actionKey) || 0
    
    if (now - lastActionTime < throttleMs) {
      console.log(`⏸️ Action throttled - ${actionKey} within ${throttleMs}ms window`)
      return { status: 'throttled' }
    }
    
    // Clean up old recent actions (older than 1 second)
    for (const [key, timestamp] of recentActions.entries()) {
      if (now - timestamp > 1000) {
        recentActions.delete(key)
      }
    }
    
    // For cart operations, provide better UX by allowing queue processing
    if (isCartAction) {
      console.log('🛒 Cart action accepted - will be queued for sequential processing')
    }
    
    // Mark action as processing and record timestamp
    processingActions.add(actionKey)
    recentActions.set(actionKey, now)
    lastActionData = actionKey
    
    try {
      if (action.type === 'tool' && action.payload.toolName && action.payload.params) {
        try {
          const response = await chatApi.mcpAction({
            action_type: action.type,
            tool_name: action.payload.toolName,
            params: action.payload.params,
            session_id: sessionId.value || undefined
          })

          if (response.result && response.result.content) {
            // Transform to proper MCP-UI resource format
            let uiResource = null
            const content = response.result.content[0]
            
            if (content && content.type === 'html') {
              // Legacy HTML format
              uiResource = {
                type: 'resource',
                resource: {
                  uri: `ui://${action.payload.toolName}/${Date.now()}`,
                  mimeType: 'text/html',
                  text: content.content
                }
              }
            } else if (content && content.type === 'resource') {
              // New MCP-UI resource format (remote-dom and HTML)
              uiResource = content
            }
            
            // If a target messageId is provided, update that message in place
            if (uiResource && action.messageId) {
              const idx = messages.value.findIndex(m => m.id === action.messageId)
              if (idx !== -1) {
                messages.value[idx] = {
                  ...messages.value[idx],
                  content: getContextualMessage(action.payload.toolName),
                  uiResource
                }
                // After in-place update, return success - no delays needed with optimistic updates
                if (action.payload.toolName === 'add_to_cart') {
                  // Auto-open cart sidebar immediately after adding items
                  cartStore.openCartWithAnimation()
                }
                return { status: 'success' }
              }
            }

            // Fallback: append a new assistant message
            const uiMessage: ChatMessage = {
              id: `ui-${Date.now()}`,
              role: 'assistant',
              content: getContextualMessage(action.payload.toolName),
              timestamp: new Date(),
              uiResource: uiResource
            }
            addMessage(uiMessage)
            
            // Handle cart-related actions - no delays needed with optimistic updates
            if (action.payload.toolName === 'add_to_cart') {
              // Auto-open cart sidebar immediately after adding items
              cartStore.openCartWithAnimation()
            }
          }

          return { status: 'success' }
        } catch (err) {
          error.value = err instanceof Error ? err.message : 'Failed to process action'
          return { status: 'error', message: error.value }
        }
      }

      if (action.type === 'prompt' && action.payload.prompt) {
        // Handle prompt by sending as new message
        await sendMessage(action.payload.prompt)
        return { status: 'success' }
      }

      if (action.type === 'notify' && action.payload.message) {
        // Handle notification (could show toast, etc.)
        console.log('Notification:', action.payload.message)
        return { status: 'success' }
      }

      if (action.type === 'link' && action.payload.url) {
        // Handle link opening
        window.open(action.payload.url, '_blank', 'noopener,noreferrer')
        return { status: 'success' }
      }

      return { status: 'unhandled' }
    } finally {
      // Always cleanup processing state
      processingActions.delete(actionKey)
      console.log(`🧹 Action cleanup: Removed ${actionKey} from processing set`)
    }
  }

  const getContextualMessage = (toolName?: string): string => {
    const messages: Record<string, string> = {
      'get_products': 'Here are our available products! Click on any item to view details or add to cart.',
      'get_product_details': 'Here are the details for that product. You can select variants and add to cart.',
      'add_to_cart': 'Great! I\'ve added that item to your cart.',
      'get_cart': 'Here\'s your current cart. You can modify quantities or proceed to checkout.',
      'checkout': 'Let\'s complete your order! Please fill in your details below.'
    }
    return messages[toolName || ''] || 'Here\'s what I found for you!'
  }

  // Removed mock product helpers now that cart mirrors server state

  const clearMessages = () => {
    messages.value = []
    error.value = null
  }

  const clearError = () => {
    error.value = null
  }

  // Initialize with welcome message and sync cart from server
  const initializeChat = async () => {
    if (messages.value.length === 0) {
      const welcomeMessage: ChatMessage = {
        id: 'welcome',
        role: 'assistant',
        content: '🏀 Welcome to our NBA Jersey Store! Browse legendary jerseys from superstars like LeBron, Curry, Jordan, and more. Each jersey features interactive highlight GIFs on hover! Try "show me NBA jerseys" or "show me all products".',
        timestamp: new Date()
      }
      addMessage(welcomeMessage)
    }
    
    // Ensure cart is synced from server on chat initialization
    if (sessionId.value) {
      await cartStore.syncCart(sessionId.value)
    }
  }

  return {
    // State
    messages,
    isLoading,
    sessionId,
    error,
    // Computed
    lastMessage,
    hasMessages,
    // Actions
    addMessage,
    sendMessage,
    handleUIAction,
    clearMessages,
    clearError,
    initializeChat
  }
})