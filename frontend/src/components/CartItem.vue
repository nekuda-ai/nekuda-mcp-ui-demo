<template>
  <div class="cart-item bg-[#1e1e20] border border-[#2a2a2d] rounded-2xl p-5 backdrop-blur-sm">
    <div class="flex items-start space-x-4">
      <!-- Product Image -->
      <div class="flex-shrink-0 relative">
        <img 
          v-if="item.imageUrl"
          :src="item.imageUrl" 
          :alt="item.name"
          class="w-16 h-16 object-cover rounded-xl border border-[#2a2a2d]"
          @error="handleImageError"
        >
        <div 
          class="w-16 h-16 rounded-xl border border-[#2a2a2d] flex items-center justify-center text-2xl absolute top-0 left-0"
          :class="item.imageUrl ? 'hidden' : 'flex'"
          :style="{ background: `linear-gradient(135deg, ${item.color || '#3b82f6'} 0%, rgba(255,255,255,0.1) 100%)` }"
        >
          {{ item.icon || '📦' }}
        </div>
      </div>

      <!-- Product Details -->
      <div class="flex-1 min-w-0">
        <div class="flex items-start justify-between gap-3">
          <div class="flex-1 min-w-0">
            <h4 class="text-sm font-semibold text-white break-words leading-tight">{{ item.name }}</h4>
            <p class="text-sm text-white/60 mt-1 truncate">{{ item.variant }}</p>
            <p class="text-sm font-semibold text-[#00D2FF] mt-1">${{ (item.price || 0).toFixed(2) }}</p>
          </div>

          <!-- Remove Button -->
          <button 
            @click="$emit('remove', item.id)"
            class="text-white/60 hover:text-red-400 transition-colors duration-300 p-2 hover:bg-red-500/10 rounded-lg flex-shrink-0"
            title="Remove item"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>

        <!-- Quantity Controls -->
        <div class="mt-4 flex items-center justify-between">
          <div class="flex items-center bg-[#111113] border border-[#2a2a2d] rounded-xl">
            <button 
              @click="decreaseQuantity"
              :disabled="item.quantity <= 1"
              class="p-2 text-white/60 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors duration-300 hover:bg-[#2a2a2d] rounded-l-xl"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4" />
              </svg>
            </button>
            
            <span class="px-4 py-2 text-sm font-semibold text-white min-w-[3rem] text-center border-x border-[#2a2a2d]">
              {{ item.quantity }}
            </span>
            
            <button 
              @click="increaseQuantity"
              :disabled="item.quantity >= 99"
              class="p-2 text-white/60 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors duration-300 hover:bg-[#2a2a2d] rounded-r-xl"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
            </button>
          </div>

          <!-- Item Total -->
          <div class="text-base font-bold text-gradient-primary">
            ${{ ((item.price || 0) * item.quantity).toFixed(2) }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { CartItem } from '@/types'

interface Props {
  item: CartItem
}

interface Emits {
  (e: 'update-quantity', itemId: string, quantity: number): void
  (e: 'remove', itemId: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const increaseQuantity = () => {
  if (props.item.quantity < 99) {
    emit('update-quantity', props.item.id, props.item.quantity + 1)
  }
}

const decreaseQuantity = () => {
  if (props.item.quantity > 1) {
    emit('update-quantity', props.item.id, props.item.quantity - 1)
  }
}

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  // Hide the image and show the fallback icon instead
  img.style.display = 'none'
  const fallbackDiv = img.nextElementSibling as HTMLElement
  if (fallbackDiv) {
    fallbackDiv.style.display = 'flex'
  }
}
</script>

<style scoped>
.cart-item {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.cart-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
  border-color: rgba(0, 210, 255, 0.3);
}

/* Ensure quantity input is properly centered */
.quantity-display {
  min-width: 2rem;
  text-align: center;
}
</style>