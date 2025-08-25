/**
 * Async Queue for handling sequential operations
 * Prevents race conditions by ensuring operations execute one at a time
 */

export type QueuedOperation<T = any> = {
  id: string
  operation: () => Promise<T>
  resolve: (value: T) => void
  reject: (error: any) => void
  timestamp: number
}

export class AsyncQueue {
  private queue: QueuedOperation[] = []
  private isProcessing = false
  private activeOperation: string | null = null

  /**
   * Add an operation to the queue
   * @param operation - Async function to execute
   * @param id - Optional unique identifier for the operation
   * @returns Promise that resolves with the operation result
   */
  async enqueue<T>(operation: () => Promise<T>, id?: string): Promise<T> {
    const operationId = id || `op-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    
    return new Promise<T>((resolve, reject) => {
      const queuedOp: QueuedOperation<T> = {
        id: operationId,
        operation,
        resolve,
        reject,
        timestamp: Date.now()
      }

      this.queue.push(queuedOp)
      console.log(`🔄 Queue: Added operation ${operationId} (queue size: ${this.queue.length})`)
      
      // Start processing if not already running
      if (!this.isProcessing) {
        this.processQueue()
      }
    })
  }

  /**
   * Process all operations in the queue sequentially
   */
  private async processQueue(): Promise<void> {
    if (this.isProcessing || this.queue.length === 0) {
      return
    }

    this.isProcessing = true
    console.log(`🚀 Queue: Starting to process ${this.queue.length} operations`)

    while (this.queue.length > 0) {
      const operation = this.queue.shift()!
      this.activeOperation = operation.id

      try {
        console.log(`⏳ Queue: Executing operation ${operation.id}`)
        const result = await operation.operation()
        operation.resolve(result)
        console.log(`✅ Queue: Completed operation ${operation.id}`)
      } catch (error) {
        console.error(`❌ Queue: Failed operation ${operation.id}:`, error)
        operation.reject(error)
      } finally {
        this.activeOperation = null
      }
    }

    this.isProcessing = false
    console.log(`🏁 Queue: Finished processing all operations`)
  }

  /**
   * Get current queue status
   */
  getStatus() {
    return {
      queueLength: this.queue.length,
      isProcessing: this.isProcessing,
      activeOperation: this.activeOperation
    }
  }

  /**
   * Clear all pending operations (emergency stop)
   */
  clear() {
    const cleared = this.queue.length
    this.queue.forEach(op => {
      op.reject(new Error('Operation cancelled - queue cleared'))
    })
    this.queue = []
    console.log(`🗑️ Queue: Cleared ${cleared} pending operations`)
  }
}

// Global cart operations queue - singleton instance
export const cartOperationsQueue = new AsyncQueue()