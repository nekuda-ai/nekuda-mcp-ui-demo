<template>
  <div class="message-content">
    <!-- Regular message content -->
    <div v-if="!message.uiResource" class="prose prose-sm max-w-none">
      <p class="whitespace-pre-wrap">{{ message.content }}</p>
    </div>

    <!-- Message with UI Resource (MCP-UI component) -->
    <div v-else class="space-y-3">
      <!-- Optional text content above the UI resource -->
      <div v-if="message.content && message.content.trim()" class="prose prose-sm max-w-none">
        <p class="whitespace-pre-wrap">{{ message.content }}</p>
      </div>

      <!-- MCP-UI Resource -->
      <div class="ui-resource-container">
        <UIResourceRenderer :ui-resource="message.uiResource" :message-id="message.id" />
      </div>
    </div>

    <!-- Message timestamp -->
    <div class="mt-2 text-xs text-gray-400">
      {{ formatTime(message.timestamp) }}
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ChatMessage } from '@/types'
import UIResourceRenderer from './UIResourceRenderer.vue'

interface Props {
  message: ChatMessage
}

defineProps<Props>()

const formatTime = (timestamp: Date): string => {
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  }).format(new Date(timestamp))
}
</script>

<style scoped>
.ui-resource-container {
  /* Ensure UI resources have proper containment */
  max-width: 100%;
  background: transparent !important;
  border: none !important;
}

/* Style for prose content */
.prose p {
  margin: 0;
  line-height: 1.5;
}

/* Override prose styles for better chat appearance */
.prose {
  color: inherit;
}
</style>