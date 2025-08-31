<template>
  <div id="app" class="h-screen flex bg-[#0a0a0b] text-white overflow-hidden">
    <!-- Main Chat Interface -->
    <div class="flex-1 flex flex-col">
      <!-- Header -->
      <header class="bg-[#111113] border-b border-[#1e1e20] px-3 sm:px-6 py-3 sm:py-4 flex items-center justify-between backdrop-blur-xl">
        <!-- Logo and Title -->
        <div class="flex items-center space-x-2 sm:space-x-3 min-w-0 flex-1">
          <a 
            href="https://nekuda.ai" 
            target="_blank"
            rel="noopener noreferrer"
            class="flex-shrink-0 transition-transform hover:scale-105"
          >
            <img src="/dot_black.png" alt="nekuda logo" class="w-6 h-6 sm:w-7 sm:h-7 rounded-2xl shadow-lg" />
          </a>
          <h1 class="text-sm sm:text-lg font-medium text-white tracking-tight truncate">
            <span class="hidden sm:inline">Headless Store + nekuda wallet Demo</span>
            <span class="sm:hidden">nekuda wallet</span>
          </h1>
        </div>
        
        <!-- Mobile Action Buttons -->
        <div class="md:hidden flex items-center space-x-2">
          <!-- Mobile nekuda wallet Button -->
          <NekudawalletButton />
          
          <!-- Mobile Menu Button -->
          <button 
            @click="showMobileMenu = !showMobileMenu"
            class="p-2 rounded-xl bg-[#1e1e20] border border-[#2a2a2d] text-white min-w-touch min-h-touch flex items-center justify-center"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>

        <!-- Desktop Action Buttons -->
        <div class="hidden md:flex items-center space-x-3">
          <!-- nekuda wallet Button -->
          <NekudawalletButton />
          
          <!-- Cart Toggle Button -->
          <button 
            @click="cartStore.toggleCart()"
            class="relative group bg-[#1e1e20] hover:bg-[#2a2a2d] text-white px-4 py-2.5 rounded-2xl transition-all duration-300 flex items-center space-x-2 border border-[#2a2a2d] hover:border-[#00D2FF]/30 hover:shadow-[0_0_20px_rgba(0,210,255,0.15)] min-w-touch min-h-touch"
          >
            <svg class="w-4 h-4 transition-transform group-hover:scale-110" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4m0 0L7 13m0 0l-1.5 6M7 13l-1.5-6m0 0h15.5M7 13v6a1 1 0 001 1h7a1 1 0 001-1v-6M7 13H5.4" />
            </svg>
            <span class="text-sm font-medium">Cart</span>
            <div 
              v-if="cartStore.itemCount > 0"
              class="absolute -top-1 -right-1 bg-gradient-to-r from-[#FF6B6B] to-[#FF5722] text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-semibold transform animate-pulse shadow-lg"
            >
              {{ cartStore.itemCount }}
            </div>
          </button>

          <!-- About Button -->
          <button 
            @click="showAbout = !showAbout"
            class="group bg-[#1e1e20] hover:bg-[#2a2a2d] text-white p-3 rounded-2xl transition-all duration-300 flex items-center border border-[#2a2a2d] hover:border-[#00D2FF]/30 hover:shadow-[0_0_20px_rgba(0,210,255,0.15)] min-w-touch min-h-touch"
            title="About this demo"
          >
            <svg class="w-5 h-5 transition-transform group-hover:scale-110" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
            </svg>
          </button>
            
          <!-- GitHub Link -->
          <a 
            href="https://github.com/nekuda-ai/nekuda-mcp-ui-demo" 
            target="_blank"
            rel="noopener noreferrer"
            class="group bg-[#1e1e20] hover:bg-[#2a2a2d] text-white p-3 rounded-2xl transition-all duration-300 flex items-center border border-[#2a2a2d] hover:border-[#00D2FF]/30 hover:shadow-[0_0_20px_rgba(0,210,255,0.15)] min-w-touch min-h-touch"
          >
            <svg class="w-5 h-5 transition-transform group-hover:scale-110" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
          </a>
        </div>


        <!-- Mobile Menu Overlay -->
        <div 
          v-if="showMobileMenu"
          @click="showMobileMenu = false"
          class="md:hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-40 animate-fade-in"
        ></div>

        <!-- Mobile Menu -->
        <div 
          v-if="showMobileMenu"
          class="md:hidden fixed top-16 right-3 bg-[#111113] border border-[#1e1e20] rounded-2xl p-4 z-50 animate-mobile-menu shadow-2xl backdrop-blur-xl"
        >
          <div class="flex flex-col space-y-3 w-48">
            <!-- About Button -->
            <button 
              @click="showAbout = !showAbout; showMobileMenu = false"
              class="group bg-[#1e1e20] hover:bg-[#2a2a2d] text-white px-4 py-3 rounded-2xl transition-all duration-300 flex items-center justify-center space-x-2 border border-[#2a2a2d] hover:border-[#00D2FF]/30 min-h-touch"
            >
              <svg class="w-5 h-5 transition-transform group-hover:scale-110" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
              </svg>
              <span class="text-sm font-medium">About</span>
            </button>
            
            <!-- GitHub Link -->
            <a 
              href="https://github.com/nekuda-ai/nekuda-mcp-ui-demo" 
              target="_blank"
              rel="noopener noreferrer"
              @click="showMobileMenu = false"
              class="group bg-[#1e1e20] hover:bg-[#2a2a2d] text-white px-4 py-3 rounded-2xl transition-all duration-300 flex items-center justify-center space-x-2 border border-[#2a2a2d] hover:border-[#00D2FF]/30 min-h-touch"
            >
              <svg class="w-5 h-5 transition-transform group-hover:scale-110" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
              <span class="text-sm font-medium">GitHub</span>
            </a>
          </div>
        </div>
      </header>

      <!-- Chat Interface -->
      <ChatInterface class="flex-1" />
      
    </div>

    <!-- Cart Sidebar -->
    <CartSidebar />
    
    <!-- About Modal -->
    <div 
      v-if="showAbout"
      @click="showAbout = false"
      class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in"
    >
      <div 
        @click.stop
        class="bg-[#111113] border border-[#1e1e20] rounded-2xl p-6 max-w-md w-full shadow-2xl backdrop-blur-xl"
      >
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-semibold text-white">About This Demo</h2>
          <button 
            @click="showAbout = false"
            class="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-[#1e1e20] transition-colors"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="text-gray-300 space-y-3">
          <p> This is a demo showcasing the integration of a headless store using <a href="https://github.com/idosal/mcp-ui" target="_blank" rel="noopener noreferrer" class="text-[#00D2FF] underline underline-offset-2 hover:text-[#00B8E6] transition-colors">MCP-UI ↗</a> with nekuda wallet.</p>
          <p class="mt-1">Features:</p>
          <ul class="list-disc list-inside space-y-1 ml-4">
            <li>Headless store with MCP-UI components</li>
            <li>API-first checkout with agentic network tokens</li>
            <li>One-click checkout with nekuda wallet</li>
          </ul>
          <div class="pt-2">
            <a 
              href="https://nekuda.ai" 
              target="_blank"
              rel="noopener noreferrer"
              class="text-[#00D2FF] hover:text-[#00B8E6] transition-colors"
            >
              Learn more at nekuda.ai →
            </a>
          </div>
          <!-- About Modal Footer with Icons -->
          <div class="mt-4 pt-3 border-t border-[#1e1e20] flex items-center justify-center text-sm text-gray-400">
            <div class="flex items-center space-x-5">
              <a 
                href="https://x.com/nekuda_ai" 
                target="_blank" 
                rel="noopener noreferrer"
                class="hover:text-white transition-colors"
                aria-label="Nekuda on X (Twitter)"
                title="X (Twitter)"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-5 h-5">
                  <path d="M18.244 2H21.5l-7.5 8.574L22.5 22h-6.672l-5.22-6.126L4.5 22H1.244l8.08-9.236L1 2h6.828l4.743 5.58L18.244 2zm-1.17 18h1.82L7.01 4h-1.9l12.964 16z"/>
                </svg>
              </a>
              <a 
                href="https://nekuda.substack.com/" 
                target="_blank" 
                rel="noopener noreferrer"
                class="hover:text-white transition-colors"
                aria-label="Nekuda Substack"
                title="Substack"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-5 h-5">
                  <path d="M3 4h18v3H3V4zm0 5h18v3H3V9zm0 5h18v6l-9-3-9 3v-6z"/>
                </svg>
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useCartStore } from '@/stores/cart'
import ChatInterface from '@/components/ChatInterface.vue'
import CartSidebar from '@/components/CartSidebar.vue'
import NekudawalletButton from '@/components/NekudawalletButton.vue'

const chatStore = useChatStore()
const cartStore = useCartStore()
const showMobileMenu = ref(false)
const showAbout = ref(false)

onMounted(async () => {
  // Initialize chat with welcome message and sync cart from server
  await chatStore.initializeChat()
})
</script>

<style scoped>
/* Component-specific styles can go here */
</style>