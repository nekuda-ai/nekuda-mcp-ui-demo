<template>
  <div ref="nekudaContainer"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { createRoot } from 'react-dom/client'
import React from 'react'
import { NekudaWalletProvider } from '@nekuda/react-nekuda-js'

interface Props {
  publicKey?: string
}

const props = withDefaults(defineProps<Props>(), {
  publicKey: 'pk_test_your_public_key_here' // This will be replaced with actual key
})

const nekudaContainer = ref<HTMLDivElement>()
let reactRoot: any = null

const slots = defineSlots<{
  default(): any
}>()

onMounted(() => {
  if (nekudaContainer.value) {
    reactRoot = createRoot(nekudaContainer.value)
    
    // Create React component with provider
    const NekudaProviderComponent = React.createElement(
      NekudaWalletProvider,
      { 
        publicKey: props.publicKey,
        environment: 'sandbox' // Use sandbox for development
      },
      React.createElement('div', { 
        ref: 'childContainer',
        style: { width: '100%', height: '100%' }
      })
    )
    
    reactRoot.render(NekudaProviderComponent)
  }
})

onUnmounted(() => {
  if (reactRoot) {
    reactRoot.unmount()
  }
})

// Export methods to interact with Nekuda SDK
const createMandate = async (mandateData: any) => {
  // This will be implemented to call Nekuda SDK methods
  console.log('Creating mandate:', mandateData)
  return { success: true, mandateId: 'test-mandate-123' }
}

const requestCardReveal = async (mandateId: string) => {
  // This will be implemented to call Nekuda SDK methods  
  console.log('Requesting card reveal for mandate:', mandateId)
  return { success: true, token: 'test-reveal-token-123' }
}

defineExpose({
  createMandate,
  requestCardReveal
})
</script>