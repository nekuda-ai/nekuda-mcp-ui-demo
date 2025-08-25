<template>
  <div v-if="hasError" class="error-boundary">
    <div class="error-container">
      <div class="error-icon">⚠️</div>
      <h2 class="error-title">Something went wrong</h2>
      <p class="error-message">{{ errorMessage }}</p>
      <div class="error-actions">
        <button @click="retry" class="retry-button">
          Try Again
        </button>
        <button @click="reportError" class="report-button">
          Report Issue
        </button>
      </div>
      <details v-if="showDetails" class="error-details">
        <summary>Technical Details</summary>
        <pre class="error-stack">{{ errorDetails }}</pre>
      </details>
    </div>
  </div>
  <slot v-else />
</template>

<script setup lang="ts">
import { ref, onErrorCaptured, nextTick } from 'vue'
import { createLogger, logError, createErrorNotification, AppError, ErrorCode, type Logger } from '@shared/error_handling'

interface Props {
  fallbackMessage?: string
  showDetails?: boolean
  onError?: (error: Error, info: string) => void
}

const props = withDefaults(defineProps<Props>(), {
  fallbackMessage: 'An unexpected error occurred. Please try again.',
  showDetails: false
})

const emit = defineEmits<{
  error: [error: Error, info: string]
  retry: []
}>()

// Setup structured logging
const logger: Logger = createLogger('error-boundary')

const hasError = ref(false)
const errorMessage = ref('')
const errorDetails = ref('')
const errorInstance = ref<Error | null>(null)

const handleError = (error: Error, info: string) => {
  hasError.value = true
  
  // Create structured error
  const appError = error instanceof AppError ? error : new AppError(
    error.message,
    ErrorCode.COMPONENT_ERROR,
    { 
      component: 'ErrorBoundary',
      additionalData: { info }
    },
    error
  )
  
  errorMessage.value = appError.userMessage
  errorDetails.value = `${error.name}: ${error.message}\n${error.stack || ''}\n\nComponent Info: ${info}`
  errorInstance.value = error
  
  // Log the error
  logError(logger, appError)
  
  // Call optional error handler
  if (props.onError) {
    props.onError(error, info)
  }
  
  // Emit error event
  emit('error', error, info)
}

const retry = async () => {
  logger.info('User triggered error boundary retry')
  hasError.value = false
  errorMessage.value = ''
  errorDetails.value = ''
  errorInstance.value = null
  
  await nextTick()
  emit('retry')
}

const reportError = () => {
  logger.info('User triggered error report')
  
  if (errorInstance.value) {
    // Create notification for error reporting
    const notification = createErrorNotification(errorInstance.value)
    
    // In a real app, you might send this to an error reporting service
    console.log('Error Report:', {
      error: errorInstance.value,
      notification,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    })
    
    // Show user feedback
    alert('Error report submitted. Thank you for helping us improve!')
  }
}

// Vue 3 error boundary
onErrorCaptured((error: Error, instance, info: string) => {
  handleError(error, info)
  return false // Prevent error from propagating
})

// Handle unhandled promise rejections
if (typeof window !== 'undefined') {
  window.addEventListener('unhandledrejection', (event) => {
    const error = event.reason instanceof Error ? event.reason : new Error(String(event.reason))
    handleError(error, 'Unhandled Promise Rejection')
  })
}
</script>

<style scoped>
.error-boundary {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: 2rem;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  margin: 1rem;
}

.error-container {
  text-align: center;
  max-width: 500px;
}

.error-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.error-title {
  color: #dc2626;
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.error-message {
  color: #6b7280;
  margin-bottom: 2rem;
  line-height: 1.5;
}

.error-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-bottom: 2rem;
}

.retry-button {
  background-color: #3b82f6;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.retry-button:hover {
  background-color: #2563eb;
}

.report-button {
  background-color: #6b7280;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.report-button:hover {
  background-color: #4b5563;
}

.error-details {
  text-align: left;
  margin-top: 1rem;
}

.error-details summary {
  cursor: pointer;
  color: #6b7280;
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.error-stack {
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  padding: 1rem;
  font-size: 0.875rem;
  color: #374151;
  overflow-x: auto;
  white-space: pre-wrap;
  max-height: 200px;
  overflow-y: auto;
}
</style>
