<template>
  <div class="chat-container h-full relative">
    <!-- Messages Container -->
    <div 
      ref="messagesContainer"
      class="chat-messages scrollbar-none h-full overflow-y-auto pb-[240px] sm:pb-[260px]"
    >
      <div 
        v-for="message in chatStore.messages"
        :key="message.id"
        :class="['message', message.role, 'animate-message-in']"
      >
        <MessageComponent :message="message" />
      </div>

      <!-- Loading indicator -->
      <div v-if="chatStore.isLoading" class="message assistant animate-message-in">
        <div class="message-content">
          <div class="flex items-center space-x-3">
            <div class="flex space-x-1">
              <div class="w-2 h-2 bg-[#00D2FF] rounded-full animate-bounce"></div>
              <div class="w-2 h-2 bg-[#00D2FF] rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
              <div class="w-2 h-2 bg-[#00D2FF] rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
            </div>
            <span class="text-sm text-white/60 font-medium">Thinking...</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Input Area - Fixed at bottom -->
    <div class="fixed bottom-0 left-0 right-0 bg-[#111113] border-t border-[#1e1e20] p-3 sm:p-6 z-20 pb-safe-bottom">
      <div class="max-w-3xl mx-auto">
        <div class="flex items-end space-x-2 sm:space-x-4">
          <div class="flex-1 relative">
            <textarea
              v-model="messageInput"
              @keydown="handleKeydown"
              :disabled="chatStore.isLoading"
              placeholder="Ask about products, add items to cart..."
              rows="1"
              class="w-full px-4 sm:px-5 py-3 sm:py-4 bg-[#1e1e20] border border-[#2a2a2d] rounded-2xl resize-none focus:outline-none focus:ring-2 focus:ring-[#00D2FF]/50 focus:border-[#00D2FF]/30 disabled:opacity-50 disabled:cursor-not-allowed text-white placeholder-white/40 transition-all duration-300 text-base"
              :class="{ 'pr-12 sm:pr-14': messageInput.trim() }"
              ref="textareaRef"
            />
            
            <!-- Send Button (appears when there's text) -->
            <button
              v-if="messageInput.trim()"
              @click="sendMessage"
              :disabled="chatStore.isLoading"
              class="absolute right-2 sm:right-3 top-1/2 transform -translate-y-1/2 bg-gradient-to-r from-[#00D2FF] to-[#3A7BD5] hover:shadow-[0_0_20px_rgba(0,210,255,0.4)] disabled:opacity-50 disabled:cursor-not-allowed text-white p-2 sm:p-2.5 rounded-xl transition-all duration-300 hover:scale-105 active:scale-95 min-w-touch min-h-touch flex items-center justify-center"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Quick Actions -->
        <div class="mt-3 sm:mt-4 flex flex-nowrap gap-1 sm:gap-2 overflow-x-auto scrollbar-none">
          <button
            v-for="suggestion in quickSuggestions"
            :key="suggestion.text"
            @click="sendQuickMessage(suggestion.text)"
            :disabled="chatStore.isLoading"
            class="px-2 sm:px-3 py-2 sm:py-2.5 bg-[#1e1e20] hover:bg-[#2a2a2d] border border-[#2a2a2d] hover:border-[#00D2FF]/30 text-white/80 hover:text-white text-xs rounded-2xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-[0_0_20px_rgba(0,210,255,0.1)] font-medium min-h-touch whitespace-nowrap flex-shrink-0"
          >
            {{ suggestion.text }}
          </button>
        </div>

        <!-- Error Display -->
        <div v-if="chatStore.error" class="mt-3 sm:mt-4 p-3 sm:p-4 bg-red-500/10 border border-red-500/30 rounded-2xl backdrop-blur-sm">
          <div class="flex items-start sm:items-center justify-between gap-2">
            <p class="text-xs sm:text-sm text-red-400 font-medium flex-1 leading-relaxed">{{ chatStore.error }}</p>
            <button
              @click="chatStore.clearError()"
              class="text-red-400/60 hover:text-red-400 transition-colors duration-200 p-2 hover:bg-red-500/10 rounded-lg min-w-touch min-h-touch flex items-center justify-center flex-shrink-0"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, onUpdated } from 'vue'
import { useChatStore } from '@/stores/chat'
import MessageComponent from './MessageComponent.vue'

const chatStore = useChatStore()
const messageInput = ref('')
const messagesContainer = ref<HTMLElement | null>(null)
const textareaRef = ref<HTMLTextAreaElement | null>(null)

const quickSuggestions = [
  { text: 'Show me NBA jerseys' },
  { text: 'Show me all products' },
  { text: 'Show me Curry jersey' },
  { text: 'What basketballs do you have?' }
]

const sendMessage = async () => {
  const message = messageInput.value.trim()
  if (!message || chatStore.isLoading) return

  messageInput.value = ''
  await chatStore.sendMessage(message)
  
  // Auto-resize textarea back to single line
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
  }
}

const sendQuickMessage = async (message: string) => {
  if (chatStore.isLoading) return
  
  messageInput.value = message
  await sendMessage()
}

const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Enter') {
    if (event.shiftKey) {
      // Allow shift+enter for new lines
      return
    } else {
      event.preventDefault()
      sendMessage()
    }
  }

  // Auto-resize textarea
  nextTick(() => {
    const textarea = textareaRef.value
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px'
    }
  })
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// Auto-scroll to bottom when new messages arrive
onUpdated(() => {
  scrollToBottom()
})

onMounted(() => {
  scrollToBottom()
})
</script>

<style scoped>
/* Auto-resize textarea */
textarea {
  min-height: 48px;
  max-height: 120px;
  transition: height 0.1s ease;
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
}

/* Hide scrollbar for WebKit browsers */
textarea::-webkit-scrollbar {
  display: none;
}

/* Ensure input stays fixed at bottom */
</style>