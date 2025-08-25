/**
 * Utility for managing unique user IDs for demo purposes.
 * Each browser session gets a unique user ID that persists during the session
 * but resets when the browser/tab is closed.
 */

const SESSION_KEY = 'nekuda_demo_user_id'

/**
 * Generates a unique user ID for this demo session
 */
function generateUserId(): string {
  // Use crypto.randomUUID() if available, fallback to timestamp + random
  if (crypto && crypto.randomUUID) {
    return `user_${crypto.randomUUID()}`
  }
  
  // Fallback for older browsers
  const timestamp = Date.now()
  const random = Math.random().toString(36).substring(2, 8)
  return `user_${timestamp}_${random}`
}

/**
 * Gets the current session's user ID, generating one if it doesn't exist
 */
export function getUserId(): string {
  // Check if we already have a user ID for this session
  let userId = sessionStorage.getItem(SESSION_KEY)
  
  if (!userId) {
    // Generate new user ID and store it
    userId = generateUserId()
    sessionStorage.setItem(SESSION_KEY, userId)
    console.log('[Demo] Generated new user ID for session:', userId)
  }
  
  return userId
}

/**
 * Force regenerate a new user ID (useful for testing)
 */
export function regenerateUserId(): string {
  const userId = generateUserId()
  sessionStorage.setItem(SESSION_KEY, userId)
  console.log('[Demo] Regenerated user ID:', userId)
  return userId
}