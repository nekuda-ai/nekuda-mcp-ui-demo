<template>
  <button 
    @click="toggleWallet"
    class="relative group bg-[#1e1e20] hover:bg-[#2a2a2d] text-white px-5 py-2.5 rounded-2xl transition-all duration-300 flex items-center space-x-2.5 border border-[#2a2a2d] hover:border-[#00D2FF]/30 hover:shadow-[0_0_20px_rgba(0,210,255,0.15)]"
  >
    <!-- Nekuda Wallet Icon -->
    <svg class="w-4 h-4 transition-transform group-hover:scale-110" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
    </svg>
    <span class="text-sm font-medium">Wallet</span>
    
    <!-- Status indicator if wallet has cards -->
    <div 
      v-if="hasStoredCards"
      class="absolute -top-1 -right-1 bg-gradient-to-r from-[#00D2FF] to-[#3A7BD5] text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-semibold shadow-lg"
    >
      ✓
    </div>
  </button>

  <!-- Wallet Modal -->
  <Teleport to="body">
    <div 
      v-if="isWalletOpen"
      class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[10000] flex items-center justify-center"
      @click="closeWallet"
    >
      <div 
        @click.stop
        class="bg-[#111113] border border-[#1e1e20] rounded-2xl p-8 max-w-lg w-full mx-4 shadow-2xl"
      >
        <!-- Header -->
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center space-x-3">
            <div class="w-10 h-10 bg-gradient-to-r from-[#00D2FF] to-[#3A7BD5] rounded-2xl flex items-center justify-center">
              <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
              </svg>
            </div>
            <h2 class="text-xl font-semibold text-white">nekuda wallet</h2>
          </div>
          <button 
            @click="closeWallet"
            class="text-white/60 hover:text-white transition-colors p-1 hover:rotate-90 transition-transform duration-300"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Wallet Content -->
        <div ref="walletContainer" class="nekuda-wallet-content min-h-[300px]">
          <div v-if="loading" class="flex items-center justify-center py-8">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            <span class="ml-3 text-white/60">Loading wallet...</span>
          </div>
          
          <div v-else-if="error" class="text-center py-8">
            <p class="text-red-400 mb-4">{{ error }}</p>
            <button @click="initializeWallet" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors">
              Retry
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { createRoot } from 'react-dom/client'
import React from 'react'
import { getUserId } from '../utils/userId'

// Reactive state
const isWalletOpen = ref(false)
const hasStoredCards = ref(false)
const loading = ref(false)
const error = ref<string | null>(null)
const walletContainer = ref<HTMLDivElement>()

let reactRoot: any = null

// Configuration
const userId = getUserId() // Unique user ID per session
const NEKUDA_PUBLIC_KEY = 'ak_mCL7GZh_ou1m1LDaU7jQkXrc5ohbsuaU8gBlu4Rzk1A'

// React component using new simplified SDK with NekudaCardManagement only
const NekudaWalletComponent = () => {
  const [nekudaComponents, setNekudaComponents] = React.useState<any>(null)
  const [prefillData, setPrefillData] = React.useState({
    email: '',
    billing_address: '',
    city: '',
    state: '',
    zip_code: '',
    phone_number: ''
  })

  // Load Nekuda components dynamically
  React.useEffect(() => {
    const loadNekuda = async () => {
      try {
        console.log('[Nekuda] Loading components...')
        const module = await import('@nekuda/react-nekuda-js')
        setNekudaComponents(module)
        console.log('[Nekuda] Components loaded successfully')
      } catch (err) {
        console.error('[Nekuda] Failed to load components:', err)
      }
    }
    loadNekuda()
  }, [])

  // Called when user clicks "Add Card" button
  const handleAddCardClick = () => {
    console.log('[Nekuda] Add card clicked')
    // Optionally update prefill data for the next card
    setPrefillData({
      ...prefillData,
      // You can modify prefill data here if needed
    })
  }

  // Called whenever the cards list changes (add, update, delete)
  const handleCardsUpdated = (cards: any[]) => {
    console.log('[Nekuda] Cards list updated:', cards)
    console.log(`[Nekuda] Total cards: ${cards.length}`)
    
    // Update the button indicator
    hasStoredCards.value = cards && cards.length > 0
    
    // Log each card's details
    cards.forEach((card: any, index: number) => {
      console.log(`[Nekuda] Card ${index + 1}:`, {
        id: card.id,
        brand: card.brand,
        last4: card.last4,
        expiry: card.expiry,
        isDefault: card.isDefault
      })
    })
  }

  if (!nekudaComponents) {
    return React.createElement('div', {
      style: { 
        color: 'rgba(255, 255, 255, 0.6)', 
        textAlign: 'center', 
        padding: '20px',
        fontSize: '14px'
      }
    }, 'Loading wallet...')
  }

  const { NekudaWalletProvider, NekudaCardManagement } = nekudaComponents

  // Dark theme styling aligned with style.css
  const darkTheme = {
    styles: {
      fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", "Inter", "Segoe UI", system-ui, sans-serif',
      fontSize: '14px'
    },
    walletStyles: {
      modal: {
        backgroundColor: '#111113',
        color: '#ffffff',
        border: '1px solid #1e1e20',
        borderRadius: '16px',
        backdropFilter: 'blur(20px)'
      },
      cardItem: {
        backgroundColor: '#1e1e20',
        color: '#ffffff',
        border: '1px solid #2a2a2d',
        borderRadius: '12px',
        padding: '16px',
        marginBottom: '12px',
        transition: 'all 0.3s ease',
        ':hover': {
          borderColor: '#00D2FF',
          boxShadow: '0 0 20px rgba(0, 210, 255, 0.15)'
        }
      },
      button: {
        primary: {
          background: 'linear-gradient(135deg, #00D2FF 0%, #3A7BD5 100%)',
          color: '#ffffff',
          border: 'none',
          borderRadius: '12px',
          padding: '12px 24px',
          fontSize: '14px',
          fontWeight: '500',
          cursor: 'pointer',
          transition: 'all 0.3s ease',
          boxShadow: '0 4px 16px rgba(0, 210, 255, 0.2)'
        },
        secondary: {
          backgroundColor: '#1e1e20',
          color: '#ffffff',
          border: '1px solid #2a2a2d',
          borderRadius: '12px',
          padding: '12px 24px',
          fontSize: '14px',
          fontWeight: '500',
          cursor: 'pointer',
          transition: 'all 0.3s ease'
        },
        ghost: {
          backgroundColor: 'transparent',
          color: 'rgba(255, 255, 255, 0.6)',
          border: 'none',
          padding: '8px 12px',
          fontSize: '14px',
          cursor: 'pointer',
          transition: 'all 0.2s ease'
        }
      }
    },
    elementsConfig: {
      cardNumber: {
        base: {
          backgroundColor: '#1e1e20',
          border: '1px solid #2a2a2d',
          color: '#ffffff',
          padding: '12px',
          borderRadius: '8px',
          fontSize: '14px',
          '::placeholder': {
            color: 'rgba(255, 255, 255, 0.4)'
          }
        },
        focus: {
          borderColor: '#00D2FF',
          outline: 'none',
          boxShadow: '0 0 0 2px rgba(0, 210, 255, 0.2)'
        },
        error: {
          borderColor: '#ff4444',
          color: '#ff4444'
        }
      },
      cardExpiry: {
        base: {
          backgroundColor: '#1e1e20',
          border: '1px solid #2a2a2d',
          color: '#ffffff',
          padding: '12px',
          borderRadius: '8px',
          fontSize: '14px',
          '::placeholder': {
            color: 'rgba(255, 255, 255, 0.4)'
          }
        },
        focus: {
          borderColor: '#00D2FF',
          outline: 'none',
          boxShadow: '0 0 0 2px rgba(0, 210, 255, 0.2)'
        },
        error: {
          borderColor: '#ff4444'
        }
      },
      cardCvv: {
        base: {
          backgroundColor: '#1e1e20',
          border: '1px solid #2a2a2d',
          color: '#ffffff',
          padding: '12px',
          borderRadius: '8px',
          fontSize: '14px',
          '::placeholder': {
            color: 'rgba(255, 255, 255, 0.4)'
          }
        },
        focus: {
          borderColor: '#00D2FF',
          outline: 'none',
          boxShadow: '0 0 0 2px rgba(0, 210, 255, 0.2)'
        },
        error: {
          borderColor: '#ff4444'
        }
      },
      name: {
        base: {
          backgroundColor: '#1e1e20',
          border: '1px solid #2a2a2d',
          color: '#ffffff',
          padding: '12px',
          borderRadius: '8px',
          fontSize: '14px',
          '::placeholder': {
            color: 'rgba(255, 255, 255, 0.4)'
          }
        },
        focus: {
          borderColor: '#00D2FF',
          outline: 'none',
          boxShadow: '0 0 0 2px rgba(0, 210, 255, 0.2)'
        }
      },
      email: {
        base: {
          backgroundColor: '#1e1e20',
          border: '1px solid #2a2a2d',
          color: '#ffffff',
          padding: '12px',
          borderRadius: '8px',
          fontSize: '14px',
          '::placeholder': {
            color: 'rgba(255, 255, 255, 0.4)'
          }
        },
        focus: {
          borderColor: '#00D2FF',
          outline: 'none',
          boxShadow: '0 0 0 2px rgba(0, 210, 255, 0.2)'
        }
      },
      billingAddress: {
        base: {
          backgroundColor: '#1e1e20',
          border: '1px solid #2a2a2d',
          color: '#ffffff',
          padding: '12px',
          borderRadius: '8px',
          fontSize: '14px',
          '::placeholder': {
            color: 'rgba(255, 255, 255, 0.4)'
          }
        },
        focus: {
          borderColor: '#00D2FF',
          outline: 'none',
          boxShadow: '0 0 0 2px rgba(0, 210, 255, 0.2)'
        }
      },
      city: {
        base: {
          backgroundColor: '#1e1e20',
          border: '1px solid #2a2a2d',
          color: '#ffffff',
          padding: '12px',
          borderRadius: '8px',
          fontSize: '14px',
          '::placeholder': {
            color: 'rgba(255, 255, 255, 0.4)'
          }
        },
        focus: {
          borderColor: '#00D2FF',
          outline: 'none',
          boxShadow: '0 0 0 2px rgba(0, 210, 255, 0.2)'
        }
      },
      state: {
        base: {
          backgroundColor: '#1e1e20',
          border: '1px solid #2a2a2d',
          color: '#ffffff',
          padding: '12px',
          borderRadius: '8px',
          fontSize: '14px',
          '::placeholder': {
            color: 'rgba(255, 255, 255, 0.4)'
          }
        },
        focus: {
          borderColor: '#00D2FF',
          outline: 'none',
          boxShadow: '0 0 0 2px rgba(0, 210, 255, 0.2)'
        }
      },
      zipCode: {
        base: {
          backgroundColor: '#1e1e20',
          border: '1px solid #2a2a2d',
          color: '#ffffff',
          padding: '12px',
          borderRadius: '8px',
          fontSize: '14px',
          '::placeholder': {
            color: 'rgba(255, 255, 255, 0.4)'
          }
        },
        focus: {
          borderColor: '#00D2FF',
          outline: 'none',
          boxShadow: '0 0 0 2px rgba(0, 210, 255, 0.2)'
        }
      },
      phoneNumber: {
        base: {
          backgroundColor: '#1e1e20',
          border: '1px solid #2a2a2d',
          color: '#ffffff',
          padding: '12px',
          borderRadius: '8px',
          fontSize: '14px',
          '::placeholder': {
            color: 'rgba(255, 255, 255, 0.4)'
          }
        },
        focus: {
          borderColor: '#00D2FF',
          outline: 'none',
          boxShadow: '0 0 0 2px rgba(0, 210, 255, 0.2)'
        }
      }
    }
  }

  // Use NekudaCardManagement for both adding first card and managing existing cards
  return React.createElement(
    NekudaWalletProvider,
    {
      publicKey: NEKUDA_PUBLIC_KEY,
      userId: userId
    },
    React.createElement('div', null,
      // Warning box
      React.createElement('div', {
        key: 'demo-warning',
        style: {
          marginBottom: '20px',
          padding: '12px',
          backgroundColor: 'rgba(255, 193, 7, 0.1)',
          borderLeft: '3px solid #ffc107',
          borderRadius: '4px'
        }
      }, React.createElement('p', {
        style: {
          margin: '0',
          color: '#ffc107',
          fontSize: '13px',
          fontWeight: '500'
        }
      }, '⚠️ Demo only - Do not enter real payment details')),
      // Card management component
      React.createElement(NekudaCardManagement, {
        open: true,
        defaultCardDetails: prefillData,
        onAddCardClick: handleAddCardClick,
        onCardsUpdated: handleCardsUpdated,
        ...darkTheme
      })
    )
  )
}

const toggleWallet = async () => {
  isWalletOpen.value = !isWalletOpen.value
  
  if (isWalletOpen.value) {
    await nextTick()
    await initializeWallet()
  }
}

const closeWallet = () => {
  isWalletOpen.value = false
  cleanup()
}

const initializeWallet = async () => {
  if (!walletContainer.value || reactRoot) return
  
  try {
    loading.value = true
    error.value = null
    
    console.log('[Nekuda] Initializing wallet...')
    
    reactRoot = createRoot(walletContainer.value)
    reactRoot.render(React.createElement(NekudaWalletComponent))
    
    console.log('[Nekuda] Wallet initialized successfully')
  } catch (err) {
    console.error('[Nekuda] Error initializing wallet:', err)
    error.value = 'Failed to load wallet. Please try again.'
  } finally {
    loading.value = false
  }
}

const cleanup = () => {
  if (reactRoot) {
    reactRoot.unmount()
    reactRoot = null
  }
}

// Cleanup on unmount
onUnmounted(() => {
  cleanup()
})
</script>

<style scoped>
/* Wallet-specific styles */
.nekuda-wallet-content {
  min-height: 300px;
}
</style>