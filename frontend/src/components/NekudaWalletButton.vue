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

// React component following documentation exactly
const NekudaWalletComponent = () => {
  const [processing, setProcessing] = React.useState(false)
  const [succeeded, setSucceeded] = React.useState(false)
  const [errorState, setErrorState] = React.useState(null)
  const [nekudaComponents, setNekudaComponents] = React.useState(null)
  const [savedCards, setSavedCards] = React.useState([])
  const [showCardManagement, setShowCardManagement] = React.useState(false)

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
        setErrorState('Failed to load Nekuda components')
      }
    }
    loadNekuda()
  }, [])

  // Check for existing cards when components load
  React.useEffect(() => {
    if (nekudaComponents) {
      checkForExistingCards()
    }
  }, [nekudaComponents])

  const checkForExistingCards = async () => {
    if (!nekudaComponents) return

    try {
      console.log('[Nekuda] Checking for existing cards for user:', userId)
      const apiService = nekudaComponents.createWalletApiService({
        customerId: 'demo-customer',
        publicKey: NEKUDA_PUBLIC_KEY
      })
      
      const cards = await apiService.getCardsForSdk(userId)
      console.log('[Nekuda] Found cards:', cards)
      
      setSavedCards(cards)
      const hasCards = cards && cards.length > 0
      setShowCardManagement(hasCards)
      hasStoredCards.value = hasCards
      
      console.log('[Nekuda] Card management mode:', hasCards ? 'Management' : 'Collection')
    } catch (err) {
      console.log('[Nekuda] No existing cards or error:', err)
      setShowCardManagement(false)
      hasStoredCards.value = false
    }
  }

  // Handle successful payment form save (following docs pattern)
  const handlePaymentSave = async (formData) => {
    console.log('[Nekuda] Payment saved via coordinator:', formData)
    
    // Extract token ID from coordinator response (as per docs)
    const tokenId = formData.id || formData.cardTokenId
    
    if (tokenId) {
      setProcessing(false)
      setSucceeded(true)
      setErrorState(null)
      console.log('[Nekuda] Card token received:', tokenId)
      
      // Refresh to switch to card management mode
      setTimeout(() => {
        checkForExistingCards()
        setSucceeded(false) // Reset for next time
      }, 1000)
    } else {
      setErrorState('Payment submission failed')
      setProcessing(false)
    }
  }

  const handleCardSave = async (card) => {
    console.log('[Nekuda] Card saved in management:', card)
    await checkForExistingCards()
  }

  const handleCardDelete = async (cardId) => {
    console.log('[Nekuda] Card deleted:', cardId)
    await checkForExistingCards()
  }

  const handleDefaultCardSet = async (cardId) => {
    console.log('[Nekuda] Default card set:', cardId)
    await checkForExistingCards()
  }

  if (!nekudaComponents) {
    return React.createElement('div', {
      style: { 
        color: 'white', 
        textAlign: 'center', 
        padding: '20px' 
      }
    }, 'Loading Nekuda SDK...')
  }

  const { NekudaWalletProvider, NekudaPaymentForm, NekudaCardManagement, createWalletApiService } = nekudaComponents

  // Show card management if user has cards, otherwise show payment form for first card
  if (showCardManagement) {
    const apiService = createWalletApiService({
      customerId: 'demo-customer',
      publicKey: NEKUDA_PUBLIC_KEY
    })

    return React.createElement(
      NekudaWalletProvider,
      {
        publicKey: NEKUDA_PUBLIC_KEY,
        userId: userId
      },
      React.createElement(NekudaCardManagement, {
        open: true,
        apiService: apiService,
        userId: userId,
        onCardSave: handleCardSave,
        onCardDelete: handleCardDelete,
        onDefaultCardSet: handleDefaultCardSet,
        savedCards: savedCards
      })
    )
  }

  // Initial card collection using NekudaPaymentForm (following docs exactly)
  return React.createElement(
    NekudaWalletProvider,
    {
      publicKey: NEKUDA_PUBLIC_KEY,
      userId: userId
    },
    React.createElement('div', {
      style: {
        color: 'white'
      }
    }, [
      React.createElement('h3', {
        key: 'title',
        style: {
          marginBottom: '16px',
          fontSize: '18px',
          fontWeight: '600'
        }
      }, 'Add Your First Payment Method'),
      
      React.createElement('p', {
        key: 'description',
        style: {
          marginBottom: '20px',
          color: 'rgba(255, 255, 255, 0.7)',
          fontSize: '14px'
        }
      }, 'Your payment information will be securely stored and tokenized.'),
      
      React.createElement(NekudaPaymentForm, {
        key: 'form',
        onSave: handlePaymentSave
      }, [
        errorState && React.createElement('div', {
          key: 'error',
          style: { 
            color: 'red', 
            marginBottom: '10px',
            fontSize: '14px'
          }
        }, errorState),
        
        React.createElement('button', {
          key: 'submit',
          type: 'submit',
          disabled: processing || succeeded,
          style: {
            marginTop: '16px',
            backgroundColor: succeeded ? '#10b981' : '#3b82f6',
            color: 'white',
            border: 'none',
            padding: '12px 24px',
            borderRadius: '8px',
            fontSize: '14px',
            fontWeight: '500',
            cursor: processing || succeeded ? 'not-allowed' : 'pointer',
            width: '100%',
            opacity: processing ? 0.7 : 1
          }
        }, processing ? 'Processing...' : succeeded ? '✓ Saved Successfully!' : 'Save Payment Details'),
        
        succeeded && React.createElement('div', {
          key: 'success',
          style: { 
            color: '#10b981', 
            marginTop: '10px',
            fontSize: '14px'
          }
        }, 'Payment method saved successfully!')
      ])
    ])
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