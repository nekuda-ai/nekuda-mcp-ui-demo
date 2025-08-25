<template>
  <div 
    :key="componentKey" 
    class="ui-resource-wrapper"
  >
    <!-- Error State -->
    <div
      v-if="hasError"
      :key="`error-${componentKey}`"
      class="mcp-ui-container"
    >
      <div class="text-red-500 text-sm p-4 border border-red-200 rounded">
        ❌ Component Error: {{ errorMessage }}
        <button 
          @click="retryRender" 
          class="mt-2 px-3 py-1 bg-red-500 text-white text-xs rounded hover:bg-red-600"
        >
          Retry
        </button>
      </div>
    </div>

    <!-- Official MCP-UI Resource Renderer -->
    <div
      v-else-if="uiResource && uiResource.type === 'resource'"
      :key="`wrapper-${componentKey}`"
      class="relative w-full h-full"
    >
      <!-- Loading overlay -->
      <div
        v-if="isLoading"
        :key="`loading-${componentKey}`"
        class="absolute inset-0 bg-black/20 backdrop-blur-sm rounded-xl flex items-center justify-center z-10"
      >
        <div class="flex items-center gap-2 text-white/80 text-sm">
          <div class="animate-spin w-4 h-4 border-2 border-white/30 border-t-white/80 rounded-full"></div>
          Loading component...
        </div>
      </div>
      
      <div
        ref="mcpUIContainer"
        :key="`container-${componentKey}`"
        class="mcp-ui-container"
        style="min-height: 50px;"
      >
        <!-- This div is now managed by the script, not Vue's template compiler -->
      </div>
    </div>

    <!-- Fallback for unsupported resources -->
    <div 
      v-else 
      :key="`fallback-${componentKey}`"
      class="text-gray-500 text-sm italic"
    >
      {{ uiResource ? 'Unsupported resource type' : 'No UI resource provided' }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed, nextTick } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useCartStore } from '@/stores/cart'
import type { UIResource } from '@/types'

interface Props {
  uiResource: UIResource
  messageId?: string
}

const props = defineProps<Props>()
const chatStore = useChatStore()
const cartStore = useCartStore()
const mcpUIContainer = ref<HTMLElement | null>(null)
const isLoading = ref(false)
const hasError = ref(false)
const errorMessage = ref('')
let currentIframe: HTMLIFrameElement | null = null
let isDestroyed = ref(false)

// Component key for Vue lifecycle management - ensures proper component recreation
const componentKey = computed(() => {
  if (!props.uiResource?.resource?.text) return 'no-resource'
  
  // Create a stable key based on resource content and type
  const resourceText = props.uiResource.resource.text
  const resourceType = props.uiResource.resource.mimeType || 'unknown'
  
  // Create a more stable hash based on content structure rather than timestamp
  const contentHash = resourceText.length + 
    resourceText.slice(0, 50).replace(/\s+/g, '').length + 
    resourceText.slice(-50).replace(/\s+/g, '').length
  
  return `${resourceType}-hash-${contentHash}`
})

// MCP-UI renderer instance and cleanup function
let uiRendererInstance: any = null
let messageListenerCleanup: (() => void) | null = null

// Error handling functions
const setError = (message: string) => {
  hasError.value = true
  errorMessage.value = message
  isLoading.value = false
  console.error('UIResourceRenderer Error:', message)
}

const clearError = () => {
  hasError.value = false
  errorMessage.value = ''
}

const retryRender = () => {
  clearError()
  initializeRenderer()
}

// Defensive DOM operation wrapper
const safeDOMOperation = async (operation: () => Promise<void> | void, errorContext: string) => {
  if (isDestroyed.value) {
    console.warn('Skipping DOM operation - component destroyed:', errorContext)
    return
  }
  
  // Additional check for container availability
  if (!mcpUIContainer.value || !mcpUIContainer.value.parentNode) {
    console.warn('Skipping DOM operation - container not available:', errorContext)
    return
  }
  
  try {
    await operation()
  } catch (error) {
    console.error('DOM operation failed:', errorContext, error)
    setError(`${errorContext}: ${error instanceof Error ? error.message : 'Unknown error'}`)
  }
}

// Handle UI actions according to official MCP-UI format
const handleUIAction = async (actionResult: any) => {
  try {
    if (isDestroyed.value) return
    console.log('MCP-UI Action:', actionResult)
    
    // Handle different action types according to official format
    switch (actionResult.type) {
      case 'tool':
        await chatStore.handleUIAction({
          type: 'tool',
          payload: {
            toolName: actionResult.payload.toolName,
            params: actionResult.payload.params || {}
          },
          messageId: actionResult.messageId || props.messageId
        })
        break
        
      case 'prompt':
        await chatStore.sendMessage(actionResult.payload.prompt)
        break
        
      case 'notify':
        console.log('Notification:', actionResult.payload.message)
        break
        
      case 'link':
        window.open(actionResult.payload.url, '_blank', 'noopener,noreferrer')
        break
        
      case 'intent':
        // Handle intent actions - could be converted to tool calls
        await chatStore.handleUIAction({
          type: 'tool',
          payload: {
            toolName: actionResult.payload.intent,
            params: actionResult.payload.params || {}
          },
          messageId: actionResult.messageId || props.messageId
        })
        break
        
      case 'ui-action':
        // Handle UI-side hints like toggle-cart; ensure cart opens and syncs from server
        if (actionResult.payload?.action === 'toggle-cart') {
          cartStore.openCart()
          await cartStore.syncCart()
        }
        break
      default:
        console.warn('Unknown UI action type:', actionResult.type)
    }
  } catch (error) {
    console.error('Failed to handle UI action:', error)
  }
}

// Cache for React libraries to avoid repeated CDN loads
let reactLibrariesCache: { react: string, reactDOM: string } | null = null

// Preload React libraries for faster initialization
const preloadReactLibraries = async () => {
  if (reactLibrariesCache) return reactLibrariesCache
  
  try {
    console.log('📦 Preloading React libraries from CDN...')
    const [reactResponse, reactDOMResponse] = await Promise.all([
      fetch('https://unpkg.com/react@18/umd/react.development.js'),
      fetch('https://unpkg.com/react-dom@18/umd/react-dom.development.js')
    ])
    
    const [reactCode, reactDOMCode] = await Promise.all([
      reactResponse.text(),
      reactDOMResponse.text()
    ])
    
    reactLibrariesCache = {
      react: reactCode,
      reactDOM: reactDOMCode
    }
    
    console.log('✅ React libraries preloaded and cached')
    return reactLibrariesCache
  } catch (error) {
    console.warn('Failed to preload React libraries, falling back to CDN:', error)
    return null
  }
}

// Remote-DOM renderer using iframe sandbox (official mcp-ui approach)
const initializeRemoteDomRenderer = async () => {
  await safeDOMOperation(async () => {
    // Enhanced container validation
    if (!mcpUIContainer.value) {
      throw new Error('Container ref not available')
    }
    
    if (!props.uiResource?.resource?.text) {
      throw new Error('Resource text not available')
    }

    // Check if container is still in DOM
    if (!mcpUIContainer.value.parentNode) {
      throw new Error('Container not connected to DOM')
    }

    console.log('🔄 Initializing Remote-DOM renderer with iframe sandbox')
    clearError()
    isLoading.value = true
    
    let iframe: HTMLIFrameElement | null = null
    let reusingIframe = false
    
    // Simplified iframe management - always create fresh iframe to avoid security issues
    console.log('🔄 IFRAME DEBUG: Starting iframe initialization')
    console.log('🔄 IFRAME DEBUG: Current iframe exists:', !!currentIframe)
    console.log('🔄 IFRAME DEBUG: Container contains current iframe:', currentIframe && mcpUIContainer.value.contains(currentIframe))
    
    // Always clean up existing iframe to avoid cross-origin security issues
    if (currentIframe) {
      console.log('🧹 IFRAME DEBUG: Cleaning up existing iframe')
      try {
        if (currentIframe.parentNode) {
          currentIframe.parentNode.removeChild(currentIframe)
          console.log('✅ IFRAME DEBUG: Successfully removed old iframe from DOM')
        }
      } catch (cleanupError) {
        console.log('🔒 IFRAME DEBUG: Iframe cleanup failed (expected for security restrictions):', cleanupError)
      }
      currentIframe = null
    }
    
    // Always create fresh iframe - no reuse to avoid security complications
    reusingIframe = false
    console.log('🚀 IFRAME DEBUG: Creating fresh iframe (no reuse for security)')
    
    if (!reusingIframe) {
      // Create new iframe with enhanced validation
      iframe = document.createElement('iframe')
      iframe.style.width = '100%'
      iframe.style.height = '480px'
      iframe.style.border = 'none'
      iframe.style.borderRadius = '1rem'
      iframe.style.overflow = 'hidden'
      iframe.style.background = 'transparent'
      iframe.sandbox.value = 'allow-scripts'
      
      // Enhanced container validation before DOM manipulation
      if (!mcpUIContainer.value) {
        throw new Error('Container element lost during initialization')
      }
      
      if (!mcpUIContainer.value.parentNode) {
        throw new Error('Container parent lost during initialization')
      }
      
      // Safe container clearing with validation
      try {
        mcpUIContainer.value.innerHTML = ''
      } catch (e) {
        throw new Error(`Failed to clear container: ${e}`)
      }
      
      // Final validation before adding iframe
      if (!mcpUIContainer.value.parentNode) {
        throw new Error('Container parent lost after clearing')
      }
      
      try {
        mcpUIContainer.value.appendChild(iframe)
        currentIframe = iframe
        console.log('✅ New iframe created and added to container')
      } catch (e) {
        throw new Error(`Failed to add iframe to container: ${e}`)
      }
    }
    
    // Get the raw React component function script
    const componentScript = props.uiResource.resource.text
    
    // Extract component name from the script (handle leading newlines and function parameters)
    const componentNameMatch = componentScript.trim().match(/^function\s+(\w+)\s*\(/);
    const componentName = componentNameMatch ? componentNameMatch[1] : 'ProductNavigator'
    
    console.log('🔍 Component script preview:', componentScript.trim().substring(0, 100))
    console.log('🎯 Extracted component name:', componentName)
    console.log('🔍 Component name regex match result:', componentNameMatch)
    
    // Debug component detection
    console.log('🔍 COMPONENT DEBUG: Detected component name:', componentName)
    console.log('🔍 COMPONENT DEBUG: Is ProductDetails?', componentName === 'ProductDetails')
    
    // Removed ProductDetails special handling that was causing iframe issues
    // All components now follow the same iframe lifecycle
    
    // Since we always create fresh iframes, proceed directly to iframe creation
    // Preload React libraries for faster initialization
    const cachedLibraries = await preloadReactLibraries()
    
    // Build HTML content for new iframe using string manipulation to avoid Vue template parsing
    let htmlContent = '<!DOCTYPE html>\n'
      htmlContent += '<html>\n'
      htmlContent += '<head>\n'
      
      // Use cached React libraries if available, otherwise fall back to CDN
      if (cachedLibraries) {
        console.log('🚀 Using cached React libraries for faster loading')
        htmlContent += '    <script>\n' + cachedLibraries.react + '\n<' + '/script>\n'
        htmlContent += '    <script>\n' + cachedLibraries.reactDOM + '\n<' + '/script>\n'
      } else {
        console.log('📡 Falling back to CDN for React libraries')
        htmlContent += '    <script crossorigin src="https://unpkg.com/react@18/umd/react.development.js"><' + '/script>\n'
        htmlContent += '    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"><' + '/script>\n'
      }
      htmlContent += '    <style>\n'
      htmlContent += '        body { margin: 0; padding: 0; background: transparent; font-family: system-ui; height: 480px; overflow: visible; }\n'
      htmlContent += '        * { box-sizing: border-box; }\n'
      htmlContent += '        #root { width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; padding: 15px 0; overflow: visible; }\n'
      htmlContent += '        \n'
      htmlContent += '        /* Responsive scaling and layout optimization */\n'
      htmlContent += '        .product-container, .product-grid { \n'
      htmlContent += '          max-height: 440px; \n'
      htmlContent += '          display: flex; \n'
      htmlContent += '          flex-direction: column; \n'
      htmlContent += '          justify-content: flex-start;\n'
      htmlContent += '          overflow: visible;\n'
      htmlContent += '        }\n'
      htmlContent += '        \n'
      htmlContent += '        /* Optimize product card layout */\n'
      htmlContent += '        .product-item, .product-card { \n'
      htmlContent += '          max-height: 440px;\n'
      htmlContent += '          display: flex;\n'
      htmlContent += '          flex-direction: column;\n'
      htmlContent += '          justify-content: flex-start;\n'
      htmlContent += '        }\n'
      htmlContent += '        \n'
      htmlContent += '        /* Optimize image sizing - smaller for more button space */\n'
      htmlContent += '        img, .product-image { \n'
      htmlContent += '          max-height: 200px !important;\n'
      htmlContent += '          width: 100% !important;\n'
      htmlContent += '          object-fit: cover;\n'
      htmlContent += '          flex-shrink: 0;\n'
      htmlContent += '        }\n'
      htmlContent += '        \n'
      htmlContent += '        /* Buttons with ultra-minimal spacing */\n'
      htmlContent += '        .button, button, .btn, [role="button"] {\n'
      htmlContent += '          flex-shrink: 0 !important;\n'
      htmlContent += '          min-height: 36px !important;\n'
      htmlContent += '          height: 36px !important;\n'
      htmlContent += '          margin-bottom: 4px !important;\n'
      htmlContent += '          margin-top: 4px !important;\n'
      htmlContent += '          padding: 6px 12px !important;\n'
      htmlContent += '          font-size: 0.8em !important;\n'
      htmlContent += '          font-weight: 600 !important;\n'
      htmlContent += '        }\n'
      htmlContent += '        \n'
      htmlContent += '        /* Button container with ultra-minimal padding */\n'
      htmlContent += '        .button-container, .actions, .product-actions {\n'
      htmlContent += '          margin-top: auto !important;\n'
      htmlContent += '          padding-top: 4px !important;\n'
      htmlContent += '          padding-bottom: 4px !important;\n'
      htmlContent += '          flex-shrink: 0 !important;\n'
      htmlContent += '        }\n'
      htmlContent += '        \n'
      htmlContent += '        /* Compact text and spacing */\n'
      htmlContent += '        .product-title, h1, h2, h3 { \n'
      htmlContent += '          font-size: 1.1em !important;\n'
      htmlContent += '          line-height: 1.2 !important;\n'
      htmlContent += '          margin: 6px 0 4px 0 !important;\n'
      htmlContent += '          text-align: center;\n'
      htmlContent += '        }\n'
      htmlContent += '        \n'
      htmlContent += '        /* Description text removed from source - no need to hide */\n'
      htmlContent += '        \n'
      htmlContent += '        /* Price styling */\n'
      htmlContent += '        .price, .product-price {\n'
      htmlContent += '          font-size: 1.3em !important;\n'
      htmlContent += '          font-weight: bold;\n'
      htmlContent += '          margin: 4px 0 8px 0 !important;\n'
      htmlContent += '          flex-shrink: 0;\n'
      htmlContent += '          text-align: center;\n'
      htmlContent += '          color: #00D2FF !important;\n'
      htmlContent += '        }\n'
      htmlContent += '        \n'
      htmlContent += '        /* Category/tag styling */\n'
      htmlContent += '        .category, .tag, .product-category {\n'
      htmlContent += '          font-size: 0.8em !important;\n'
      htmlContent += '          margin: 4px 0 !important;\n'
      htmlContent += '          text-align: center;\n'
      htmlContent += '        }\n'
      htmlContent += '    <' + '/style>\n'
      htmlContent += '<' + '/head>\n'
      htmlContent += '<body>\n'
      htmlContent += '    <div id="root"><' + '/div>\n'
      htmlContent += '    <script>\n'
      htmlContent += '        try {\n'
      htmlContent += '            // Make React available globally\n'
      htmlContent += '            const { useState, useEffect, createElement } = React;\n'
      htmlContent += '            \n'
      htmlContent += '            // Set up root element for MCP-UI compliance\n'
      htmlContent += '            const root = document.getElementById("root");\n'
      htmlContent += '            \n'
      htmlContent += '            // Set up action handler for communication with parent\n'
      htmlContent += '            const onAction = (actionData) => {\n'
      htmlContent += '                console.log("📤 Sending action to parent:", actionData);\n'
      htmlContent += '                window.parent.postMessage(actionData, "*");\n'
      htmlContent += '            };\n'
      htmlContent += '            \n'
      htmlContent += '            // Execute the component function\n'
      htmlContent += '            ' + componentScript + '\n'
      htmlContent += '            \n'
      htmlContent += '            // Manual rendering if MCP component did not auto-render\n'
      htmlContent += '            console.log("🔧 Checking if manual rendering needed. Root innerHTML:", root.innerHTML.substring(0, 100));\n'
      htmlContent += '            console.log("🎯 Using component name:", "' + componentName + '");\n'
      htmlContent += '            console.log("🔍 Available functions:", typeof ' + componentName + ');\n'
      htmlContent += '            if (root && root.innerHTML === "") {\n'
      htmlContent += '                console.log("🚀 Creating component element with onAction prop");\n'
      htmlContent += '                try {\n'
      htmlContent += '                    const componentElement = React.createElement(' + componentName + ', { onAction });\n'
      htmlContent += '                    const reactRoot = ReactDOM.createRoot(root);\n'
      htmlContent += '                    reactRoot.render(componentElement);\n'
      htmlContent += '                    console.log("✅ Component rendered manually");\n'
      htmlContent += '                } catch (renderError) {\n'
      htmlContent += '                    console.error("❌ Component render error:", renderError);\n'
      htmlContent += '                    root.innerHTML = "<div style=\\"padding: 20px; color: red; text-align: center;\\">❌ Component Render Error: " + renderError.message + "</div>";\n'
      htmlContent += '                }\n'
      htmlContent += '            } else {\n'
      htmlContent += '                console.log("ℹ️ Component already rendered, skipping manual render");\n'
      htmlContent += '            }\n'
      htmlContent += '            \n'
      htmlContent += '            console.log("✅ Remote-DOM component rendered successfully");\n'
      htmlContent += '            \n'
      htmlContent += '        } catch (error) {\n'
      htmlContent += '            console.error("❌ Error rendering component:", error);\n'
      htmlContent += '            document.getElementById("root").innerHTML = \n'
      htmlContent += '                "<div style=\\"padding: 20px; color: red; text-align: center;\\">❌ Component Error: " + error.message + "<' + '/div>";\n'
      htmlContent += '        }\n'
      htmlContent += '    <' + '/script>\n'
      htmlContent += '<' + '/body>\n'
      htmlContent += '<' + '/html>'
      
    // Set iframe content
    iframe.srcdoc = htmlContent

    // Add message listener for iframe communication with enhanced security checking
    console.log('📡 MESSAGE DEBUG: Setting up iframe message listener')
    const handleIframeMessage = (event: MessageEvent) => {
      // Component destruction check - prevent processing messages from destroyed components
      if (isDestroyed.value) {
        console.log('🛑 MESSAGE DEBUG: Component destroyed, ignoring message')
        return
      }
      
      console.log('📨 MESSAGE DEBUG: Received message from:', event.origin, 'Data:', event.data)
      
      if (!iframe) {
        console.log('❌ MESSAGE DEBUG: No iframe reference, ignoring message')
        return
      }
      
      // Enhanced security check with better logging
      if (event.source !== iframe.contentWindow) {
        console.log('⚠️ MESSAGE DEBUG: Message source does not match iframe contentWindow')
        console.log('🔍 MESSAGE DEBUG: Expected source:', iframe.contentWindow)
        console.log('🔍 MESSAGE DEBUG: Actual source:', event.source)
        return
      }
      
      if (!event.data || !event.data.type) {
        console.log('⚠️ MESSAGE DEBUG: Invalid message data structure')
        return
      }
      
      console.log('✅ MESSAGE DEBUG: Valid iframe message received:', event.data)
      handleUIAction(event.data)
    }
    
    window.addEventListener('message', handleIframeMessage)
    console.log('✅ MESSAGE DEBUG: Message listener attached')
    
    // Store cleanup function
    const cleanupFn = () => {
      console.log('🧹 MESSAGE DEBUG: Removing remote-dom message listener')
      window.removeEventListener('message', handleIframeMessage)
    }
    uiRendererInstance = cleanupFn
    messageListenerCleanup = cleanupFn
    
    if (iframe) {
      iframe.onload = () => {
        if (isDestroyed.value) return
        console.log('✅ Remote-DOM iframe loaded successfully')
        // Add small delay to ensure React rendering is complete
        setTimeout(() => {
          if (!isDestroyed.value && isLoading.value) {
            isLoading.value = false
            // Auto-scroll chat to bottom when iframe loads
            scrollChatToBottom()
          }
        }, 100)
      }
      
      // Add timeout to prevent stuck loading state
      setTimeout(() => {
        if (!isDestroyed.value && isLoading.value) {
          console.log('⏰ Iframe loading timeout, forcing completion')
          isLoading.value = false
        }
      }, 3000)
      
      iframe.onerror = (error) => {
        if (isDestroyed.value) return
        console.error('❌ Remote-DOM iframe error:', error)
        setError(`Iframe failed to load: ${error}`)
      }
    }

  }, 'Remote-DOM renderer initialization')
}

// Initialize renderer - supports remote-dom resources only
const initializeRenderer = async () => {
  await nextTick()
  
  if (!mcpUIContainer.value || !props.uiResource) {
    console.warn('Container or resource not available for initialization')
    return
  }
  
  console.log('🔄 Initializing remote-dom renderer')
  console.log('📄 Resource mimeType:', props.uiResource.resource?.mimeType)
  
  // Handle remote-dom resources (only supported format)
  if (props.uiResource.resource.mimeType?.includes('application/vnd.mcp-ui.remote-dom+javascript') && props.uiResource.resource.text) {
    await initializeRemoteDomRenderer()
  } else {
    console.error('❌ Unsupported resource format:', props.uiResource.resource.mimeType)
    mcpUIContainer.value!.innerHTML = `
      <div class="text-red-500 text-sm p-4 border border-red-200 rounded">
        ❌ Unsupported resource format: ${props.uiResource.resource.mimeType}
        <br>Only remote-dom resources are supported.
      </div>
    `
  }
}

// Auto-scroll chat to bottom function
const scrollChatToBottom = () => {
  // Find the chat messages container in the parent
  const messagesContainer = document.querySelector('.chat-messages')
  if (messagesContainer) {
    setTimeout(() => {
      messagesContainer.scrollTop = messagesContainer.scrollHeight
    }, 150) // Small delay to ensure iframe has rendered
  }
}

// Enhanced cleanup function with better container management
const cleanup = () => {
  console.log('🧹 Starting enhanced cleanup for component transition')
  
  // Clear loading and error states
  isLoading.value = false
  clearError()
  
  // Clean up message listener
  try {
    if (messageListenerCleanup) {
      messageListenerCleanup()
      console.log('🧹 Message listener cleaned up successfully')
    }
  } catch (error) {
    console.warn('Error during listener cleanup:', error)
  }
  
  uiRendererInstance = null
  messageListenerCleanup = null
  
  // Enhanced iframe cleanup with container validation and SecurityError handling
  if (currentIframe) {
    try {
      // Try to clear iframe content if accessible (may fail with SecurityError)
      try {
        if (currentIframe.contentWindow) {
          const root = currentIframe.contentWindow.document.getElementById('root')
          if (root) {
            root.innerHTML = ''
          }
        }
      } catch (securityError) {
        // Skip SecurityError - this is expected with cross-origin iframe restrictions
        console.log('🔒 Skipping iframe content cleanup due to security restrictions (expected)')
      }
      
      // Remove iframe from DOM if still attached
      if (currentIframe.parentNode) {
        currentIframe.parentNode.removeChild(currentIframe)
        console.log('🗑️ Iframe removed from DOM successfully')
      }
    } catch (e) {
      console.warn('Error during iframe cleanup:', e)
    }
    
    currentIframe = null
  }
  
  // Clear container content safely with validation
  if (mcpUIContainer.value && !isDestroyed.value) {
    try {
      // Only clear if container is still in DOM
      if (mcpUIContainer.value.parentNode) {
        mcpUIContainer.value.innerHTML = ''
      }
    } catch (e) {
      console.warn('Error clearing container:', e)
    }
  }
  
  // Clear loading state
  if (isLoading.value) {
    isLoading.value = false
  }
}

// Watch for prop changes and re-initialize renderer
watch(
  () => props.uiResource,
  async (newResource, oldResource) => {
    console.log('🔄 UIResource prop changed, re-initializing renderer')
    console.log('📊 Old resource:', {
      type: oldResource?.type,
      mimeType: oldResource?.resource?.mimeType,
      textLength: oldResource?.resource?.text?.length || 0
    })
    console.log('📊 New resource:', {
      type: newResource?.type,
      mimeType: newResource?.resource?.mimeType,
      textLength: newResource?.resource?.text?.length || 0
    })
    
    if (newResource && newResource.resource?.text !== oldResource?.resource?.text) {
      // Add visual indicator for component transition
      isLoading.value = true
      
      // Clean up existing renderer
      console.log('🧹 Cleaning up old renderer for component transition')
      cleanup()
      await nextTick()
      
      // Re-initialize with new resource
      console.log('🚀 Initializing new renderer')
      await initializeRenderer()
    }
  },
  { immediate: false, deep: true }
)

onMounted(async () => {
  console.log('🏁 UIResourceRenderer mounted, props:', props)
  
  // Start preloading React libraries in the background for faster future initializations
  preloadReactLibraries().catch(e => console.warn('Background React preload failed:', e))
  
  initializeRenderer()
})

onUnmounted(() => {
  console.log('🧹 UIResourceRenderer unmounting, marking as destroyed')
  isDestroyed.value = true
  
  // Ensure message listener is cleaned up before component destruction
  if (messageListenerCleanup) {
    console.log('🧹 UNMOUNT: Found message listener to clean up')
  }
  
  cleanup()
  
  // Final safety check to ensure listener is removed
  if (messageListenerCleanup) {
    console.warn('🚨 MEMORY LEAK WARNING: Message listener may not have been cleaned up properly')
  }
})
</script>

<style scoped>
.ui-resource-wrapper {
  /* Ensure proper containment and styling for MCP-UI content */
  max-width: 100%;
  overflow: visible;
  margin: 16px 0;
  background: transparent !important;
  border: none !important;
}

.mcp-ui-container {
  width: 100%;
  height: 440px;
  background: transparent !important;
  border: none !important;
  border-radius: 12px;
  position: relative;
  overflow: visible;
}

/* Global styles for MCP-UI content */
:deep(.mcp-ui-content) {
  /* Reset and base styles */
  font-family: inherit;
  line-height: 1.5;
  color: inherit;
}

/* Button styling for MCP-UI components */
:deep(.mcp-ui-content button) {
  @apply inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors duration-200;
}

:deep(.mcp-ui-content button:not([class*="bg-"])) {
  @apply bg-primary-500 hover:bg-primary-600 text-white focus:ring-primary-500;
}

:deep(.mcp-ui-content button:disabled) {
  @apply opacity-50 cursor-not-allowed;
}

/* Form styling for MCP-UI components */
:deep(.mcp-ui-content input[type="text"]),
:deep(.mcp-ui-content input[type="email"]),
:deep(.mcp-ui-content input[type="tel"]),
:deep(.mcp-ui-content select),
:deep(.mcp-ui-content textarea) {
  @apply block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500;
}

/* Product grid and card styling */
:deep(.mcp-ui-content .product-grid) {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1rem;
  padding: 1rem 0;
}

:deep(.mcp-ui-content .product-card) {
  @apply bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200;
  overflow: hidden;
}

:deep(.mcp-ui-content .product-card img) {
  width: 100%;
  height: 200px;
  object-fit: cover;
}

/* Cart item styling */
:deep(.mcp-ui-content .cart-item) {
  @apply flex items-center justify-between p-4 border-b border-gray-200;
}

/* Responsive design */
@media (max-width: 640px) {
  :deep(.mcp-ui-content .product-grid) {
    grid-template-columns: 1fr;
  }
}
</style>